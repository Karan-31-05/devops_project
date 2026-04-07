"""
Timetable Auto-Fill Engine
==========================
Ported and refactored from generate_timetable.py into a reusable class
that integrates with the wizard's TimetableConfig, LabRoom, LabRestriction,
and FixedSlotReservation models.

Features:
- Respects pre-reserved (pinned) slots from FixedSlotReservation
- Respects blocked slots (free periods, library hour, etc.)
- Uses only selected labs (TimetableConfigLab) instead of hardcoded NUM_LABS
- Enforces LabRestriction (program/year/course level)
- Faculty conflict detection across all batches
- Lab session scheduling (2-period and 4-period)
- Theory class distribution across days
"""

from collections import defaultdict
from datetime import date
import random
import re

from django.db import transaction
from django.db.models import Q

from main_app.models import (
    TimeSlot, Timetable, TimetableEntry, Course_Assignment,
    ProgramBatch, FixedSlotReservation, TimetableConfig,
    TimetableConfigLab, LabRoom, LabRestriction, Course, Faculty_Profile,
    SameTimeConstraint, MELabAssistConstraint, FacultyTimeBlock,
    ElectiveCourseOffering, ElectiveOfferingFacultyAssignment,
    RegulationCoursePlan, PECCourseCombinationRule,
    PECGroupConfig, ClubbedCourseGroup, ClubbedCourseMember,
)


DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI']
DAY_INDEX = {day: idx for idx, day in enumerate(DAYS)}
NUM_PERIODS = 8

# 2-period lab slots — consecutive periods without breaks between them
LAB_SLOT_2_PERIOD = [(1, 2), (3, 4), (5, 6), (7, 8)]

# 3-period lab slots — contiguous blocks within half-day windows
LAB_SLOT_3_PERIOD = [(1, 2, 3), (2, 3, 4), (5, 6, 7), (6, 7, 8)]

# 4-period lab slots — morning half (1-4) or afternoon half (5-8)
LAB_SLOT_4_PERIOD = [(1, 2, 3, 4), (5, 6, 7, 8)]

MAPPED_COURSE_RE = re.compile(r'Mapped\s+Course\s*:\s*([A-Za-z0-9]+)', re.IGNORECASE)


def get_required_periods(course, semester=None):
    """
    Calculate how many periods per week a course needs.
    Returns dict with theory periods, lab sessions count, lab type (2/3/4 periods).
    
    For placeholder courses (PEC/OEC) with no LTP data, resolves the first
    active ElectiveCourseOffering to determine periods from the actual course.
    """
    effective = course

    # For placeholders with no course_type, resolve from offering
    if course.is_placeholder and not course.course_type:
        actual = _resolve_placeholder_to_actual(course, semester)
        if actual:
            effective = actual

    if effective.course_type in ['L', 'LIT']:
        practical_hrs = effective.practical_hours or 0
        if practical_hrs >= 4:
            lab_type = 4
            lab_sessions = 1
        elif practical_hrs == 3:
            lab_type = 3
            lab_sessions = 1
        else:
            lab_type = 2
            lab_sessions = max(1, practical_hrs // 2)
        theory_periods = effective.lecture_hours or 0
        return {
            'theory': theory_periods,
            'lab_sessions': lab_sessions,
            'lab_type': lab_type,
            'total': theory_periods + (lab_sessions * lab_type),
        }
    else:
        theory = (effective.lecture_hours or 0) + (effective.tutorial_hours or 0)
        return {
            'theory': theory,
            'lab_sessions': 0,
            'lab_type': 0,
            'total': theory,
        }


def _resolve_placeholder_to_actual(placeholder_course, semester=None):
    """
    For a placeholder course (PEC-03, PEC-04, etc.), find the first active
    ElectiveCourseOffering and return the actual_course so we can read
    its LTP values.  Returns None if no offering is found.
    """
    filters = {
        'regulation_course_plan__course': placeholder_course,
        'is_active': True,
    }
    if semester:
        filters['semester'] = semester

    offering = ElectiveCourseOffering.objects.filter(
        **filters
    ).select_related('actual_course').first()

    return offering.actual_course if offering else None


class TimetableEngine:
    """
    Auto-fill engine that generates timetable entries for every batch
    within a TimetableConfig, respecting pinned/blocked slots and
    lab restrictions.
    """

    def __init__(self, config: TimetableConfig, exclude_batch_ids=None, clubbed_slots=None, lab_occupancy=None, lab_assist_slots=None, generation_preferences=None):
        self.config = config
        self.time_slots = list(TimeSlot.objects.all().order_by('slot_number'))
        self.warnings = []  # Collect scheduling warnings
        self._excluded_batch_ids = set(exclude_batch_ids or [])
        self.generation_preferences = self._normalize_generation_preferences(generation_preferences)
        self.prefer_avoid_professor_edges = self.generation_preferences['avoid_professor_first_last']
        self._professor_ids = set(
            Faculty_Profile.objects.filter(designation='PROF').values_list('id', flat=True)
        )

        # Clubbed-course slot placements from previously generated configs.
        # Format: { (course_code, faculty_id): [(day, slot_num), ...] }
        self.clubbed_slots = clubbed_slots or {}

        # Lab-room slots already occupied by previously generated configs.
        # Format: set((day, slot_num, lab_id), ...)
        self.lab_occupancy = set(lab_occupancy or [])

        # Global BE lab placements keyed by course_code.
        # Format: {course_code: {(day, slot_num), ...}}
        self.global_lab_assist_slots = lab_assist_slots if lab_assist_slots is not None else defaultdict(set)

        # For ME class configs, these BE lab course codes should block all placements.
        self.me_assist_lab_course_codes = set(
            MELabAssistConstraint.objects.filter(
                academic_year=config.academic_year,
                semester_type=config.semester.semester_type,
                me_program=config.program,
                me_year_of_study=config.year_of_study,
            ).values_list('be_lab_course__course_code', flat=True)
        )

        # Selected labs for this run
        selected_lab_ids = TimetableConfigLab.objects.filter(
            config=config,
        ).values_list('lab_id', flat=True)

        if selected_lab_ids:
            self.labs = list(LabRoom.objects.filter(id__in=selected_lab_ids, is_active=True).order_by('room_code'))
        else:
            # Fall back to all active labs
            self.labs = list(LabRoom.objects.filter(is_active=True).order_by('room_code'))

        self.num_labs = len(self.labs)

        # Pre-load restrictions for quick lookup
        # {lab_id: [{'program_id': ..., 'year_of_study': ..., 'course_id': ...}, ...]}
        self.lab_restrictions = defaultdict(list)
        for r in LabRestriction.objects.filter(lab__in=self.labs):
            self.lab_restrictions[r.lab_id].append({
                'program_id': r.program_id,
                'year_of_study': r.year_of_study,
                'course_id': r.course_id,
            })

        # {course_pk: {lab_id, ...}} for explicit course-level lab restrictions.
        self.course_restricted_lab_ids = defaultdict(set)
        for lab_id, restriction_rows in self.lab_restrictions.items():
            for row in restriction_rows:
                if row['course_id']:
                    self.course_restricted_lab_ids[row['course_id']].add(lab_id)

        # ── Global tracking structures (shared across batches) ──
        # {faculty_id: {(day, slot_num), ...}}
        self.faculty_schedule = defaultdict(set)
        # {faculty_id: {day: periods_count}}
        self.faculty_day_load = defaultdict(lambda: defaultdict(int))
        # {faculty_id: {day: count_of_lab_sessions_any_length}}
        self.faculty_lab_sessions_by_day = defaultdict(lambda: defaultdict(int))
        self._recorded_lab_sessions = set()
        # {faculty_id: {day: count_of_4h_lab_sessions}}
        self.faculty_long_lab_days = defaultdict(lambda: defaultdict(int))
        self._recorded_long_lab_sessions = set()
        # {(day, slot_num): {lab_id: batch_label_or_None}}
        self.lab_schedule_slots = defaultdict(lambda: {lab.id: None for lab in self.labs})
        # {(day, slot_pair_tuple): {lab_id: batch_label_or_None}}
        self.lab_schedule_2p = defaultdict(lambda: {lab.id: None for lab in self.labs})

        # Seed lab occupancy from earlier configs in generate_all() so labs cannot clash
        # across different programs/batches in the same run.
        for day, slot_num, lab_id in self.lab_occupancy:
            if lab_id in self.lab_schedule_slots[(day, slot_num)]:
                self.lab_schedule_slots[(day, slot_num)][lab_id] = '__BUSY__'

        # ── Per-batch blocked/occupied slots (seeded from reservations) ──
        # {timetable_id: {(day, slot_num), ...}}
        self.occupied = defaultdict(set)
        self.lab_workload_by_day = defaultdict(lambda: defaultdict(int))
        self.imported_lab_workload_by_day = defaultdict(lambda: defaultdict(int))
        self.lab_halfday_workload_by_timetable = defaultdict(lambda: defaultdict(int))
        self.imported_lab_halfday_workload_by_timetable = defaultdict(lambda: defaultdict(int))

        # ── Pre-populate faculty schedule from EXISTING active timetables ──
        # This ensures generating timetable for Year 2 won't conflict with
        # faculty already assigned in Year 1's active timetable.
        self._load_existing_faculty_commitments(exclude_batch_ids=exclude_batch_ids)
        self._load_existing_me_assist_slots()

        # Prepared lazily so multi-config generation can run global lab and
        # theory passes without rebuilding per-batch state.
        self._prepared = False
        self._batch_list = []
        self._batch_ids = set()
        self._timetable_map = {}
        self._course_requirements_map = {}
        self._timetables_created = []
        self.clubbed_slot_reservations = defaultdict(set)

    @staticmethod
    def _normalize_generation_preferences(generation_preferences):
        prefs = generation_preferences or {}
        return {
            'avoid_professor_first_last': bool(prefs.get('avoid_professor_first_last', False)),
        }

    @staticmethod
    def _semester_numbers_for_type(semester_type):
        return [1, 3, 5, 7] if semester_type == 'ODD' else [2, 4, 6, 8]

    @staticmethod
    def _resolve_batches_for_config(config):
        """Resolve batches for a config using cohort mapping when needed."""
        year_of_study = int(config.year_of_study)

        qs = ProgramBatch.objects.filter(
            academic_year=config.academic_year,
            program=config.program,
            year_of_study=year_of_study,
            is_active=True,
        ).order_by('batch_name')

        if qs.exists() or year_of_study <= 1:
            return qs

        # Cohort fallback: admission AY Year 1 rows (e.g., current Y3 -> admission AY Y1)
        try:
            start_year = int(config.academic_year.year.split('-')[0])
            admission_start_year = start_year - (year_of_study - 1)
            admission_year_label = f"{admission_start_year}-{str(admission_start_year + 1)[-2:]}"
        except (ValueError, IndexError):
            return ProgramBatch.objects.none()

        return ProgramBatch.objects.filter(
            academic_year__year=admission_year_label,
            program=config.program,
            year_of_study=1,
            is_active=True,
        ).order_by('batch_name')

    # ─── Pre-load existing faculty commitments ─────────────────

    def _load_existing_faculty_commitments(self, exclude_batch_ids=None):
        """
        Populate faculty_schedule from all active timetables that are NOT
        part of the batches being regenerated. This prevents the engine
        from double-booking a faculty member who is already scheduled
        elsewhere.
        
        Args:
            exclude_batch_ids: Set of ProgramBatch IDs that will be regenerated
                               (their existing entries are ignored).
                               If None, excludes the current config's program+year batches.
        """
        if exclude_batch_ids is None:
            exclude_batch_ids = set(
                self._resolve_batches_for_config(self.config).values_list('id', flat=True)
            )

        existing_entries = TimetableEntry.objects.filter(
            timetable__is_active=True,
            timetable__academic_year=self.config.academic_year,
            timetable__semester=self.config.semester,
            faculty__isnull=False,
        ).exclude(
            timetable__program_batch_id__in=exclude_batch_ids,
        ).values_list(
            'faculty_id', 'day', 'time_slot__slot_number'
        )

        for faculty_id, day, slot_num in existing_entries:
            self._book_faculty(faculty_id, day, slot_num)

        # ── Also load explicit FacultyTimeBlock entries ──
        sem_numbers = [1, 3, 5, 7] if (self.config.semester.semester_number % 2 == 1) else [2, 4, 6, 8]
        faculty_blocks = FacultyTimeBlock.objects.filter(
            academic_year=self.config.academic_year,
            semester__semester_number__in=sem_numbers,
        ).values_list('faculty_id', 'day', 'time_slot__slot_number')

        for faculty_id, day, slot_num in faculty_blocks:
            self._book_faculty(faculty_id, day, slot_num)

        # ── Also load existing LAB room usage from active timetables outside target batches ──
        # This prevents reusing the same lab room at the same period for unaffected classes.
        existing_lab_entries = TimetableEntry.objects.filter(
            timetable__is_active=True,
            timetable__academic_year=self.config.academic_year,
            timetable__semester=self.config.semester,
            lab_room__isnull=False,
            is_lab=True,
        ).exclude(
            timetable__program_batch_id__in=exclude_batch_ids,
        ).values_list('day', 'time_slot__slot_number', 'lab_room_id')

        for day, slot_num, lab_id in existing_lab_entries:
            if lab_id in self.lab_schedule_slots[(day, slot_num)]:
                self.lab_schedule_slots[(day, slot_num)][lab_id] = '__BUSY__'

    def _load_existing_me_assist_slots(self):
        """
        Preload BE lab placements from existing timetables so ME assist blocking
        works even before new BE labs are generated in this run.
        """
        if not self.me_assist_lab_course_codes:
            return

        sem_numbers = self._semester_numbers_for_type(self.config.semester.semester_type)
        existing_rows = TimetableEntry.objects.filter(
            timetable__is_active=True,
            timetable__academic_year=self.config.academic_year,
            timetable__semester__semester_number__in=sem_numbers,
            timetable__program_batch__program__degree='BE',
            is_lab=True,
            course__course_code__in=self.me_assist_lab_course_codes,
        ).exclude(
            timetable__program_batch_id__in=self._excluded_batch_ids,
        ).values_list('course__course_code', 'day', 'time_slot__slot_number')

        for course_code, day, slot_num in existing_rows:
            self.global_lab_assist_slots.setdefault(course_code, set()).add((day, slot_num))

    def _record_be_lab_slots_for_course(self, course, day, slots):
        """Record BE lab slot occupancy by course code for ME-assist blocking."""
        if self.config.program.degree != 'BE':
            return
        if not course or not getattr(course, 'course_code', None):
            return

        slot_set = self.global_lab_assist_slots.setdefault(course.course_code, set())
        for slot_num in slots:
            slot_set.add((day, slot_num))

    def _is_blocked_by_me_lab_assist(self, day, slots):
        """True when this config's ME class is mapped to BE labs at these slots."""
        if not self.me_assist_lab_course_codes:
            return False

        for course_code in self.me_assist_lab_course_codes:
            blocked_slots = self.global_lab_assist_slots.get(course_code, set())
            if any((day, slot_num) in blocked_slots for slot_num in slots):
                return True
        return False

    def _get_target_batches(self):
        return list(self._resolve_batches_for_config(self.config))

    @staticmethod
    def _extract_mapped_course_code(special_note):
        if not special_note:
            return None
        match = MAPPED_COURSE_RE.search(special_note)
        if not match:
            return None
        return match.group(1).strip().upper()

    @staticmethod
    def _clubbing_course_code_for_assignment(assignment):
        mapped_code = TimetableEngine._extract_mapped_course_code(getattr(assignment, 'special_note', ''))
        if mapped_code:
            return mapped_code

        course = getattr(assignment, 'course', None)
        if course and course.course_code:
            return course.course_code
        return None

    @staticmethod
    def _clubbing_key_for_assignment(assignment):
        code = TimetableEngine._clubbing_course_code_for_assignment(assignment)
        if not code or not assignment.faculty_id:
            return None
        return (code, assignment.faculty_id)

    def _refresh_external_commitments(self):
        """
        Merge in faculty/lab commitments that may have been created by other
        configs after this engine instance was initialized.
        """
        self._load_existing_faculty_commitments(exclude_batch_ids=self._batch_ids or None)
        self._load_existing_me_assist_slots()

    def _rebuild_pending_clubbed_slot_set(self):
        pending_keys = {
            key
            for reqs in self._course_requirements_map.values()
            for cr in reqs
            for key in [self._clubbing_key_for_assignment(cr['assignment'])]
            if key and key in self.clubbed_slots
        }

        self.pending_clubbed_slot_set = set()
        for key in pending_keys:
            payload = self.clubbed_slots.get(key, {})
            if isinstance(payload, dict):
                self.pending_clubbed_slot_set.update(self._to_day_slot_pairs(payload.get('theory', [])))
                self.pending_clubbed_slot_set.update(self._to_day_slot_pairs(payload.get('lab', [])))
            else:
                self.pending_clubbed_slot_set.update(self._to_day_slot_pairs(payload))

    def _reserve_imported_clubbed_slots(self):
        self.clubbed_slot_reservations = defaultdict(set)
        self.imported_lab_workload_by_day = defaultdict(lambda: defaultdict(int))
        self.imported_lab_halfday_workload_by_timetable = defaultdict(lambda: defaultdict(int))

        for batch in self._batch_list:
            timetable = self._timetable_map.get(batch.id)
            if not timetable:
                continue

            for cr in self._course_requirements_map.get(batch.id, []):
                asgn = cr['assignment']
                key = self._clubbing_key_for_assignment(asgn)
                if not key:
                    continue
                payload = self.clubbed_slots.get(key)
                if not payload:
                    continue

                if isinstance(payload, dict):
                    theory_items = list(payload.get('theory', []))
                    lab_items = list(payload.get('lab', []))
                    slot_items = theory_items + lab_items
                else:
                    theory_items = list(payload)
                    lab_items = []
                    slot_items = theory_items

                for item in slot_items:
                    if isinstance(item, (list, tuple)) and len(item) >= 2:
                        self.clubbed_slot_reservations[timetable.id].add((item[0], item[1]))

                lab_type = cr.get('lab_type', 0)
                if lab_type <= 0 or not lab_items:
                    continue

                slots_by_day = defaultdict(list)
                for item in lab_items:
                    if isinstance(item, (list, tuple)) and len(item) >= 2:
                        slots_by_day[item[0]].append(item[1])

                for day, slot_numbers in slots_by_day.items():
                    session_groups = self._extract_lab_session_groups(slot_numbers, lab_type)
                    self.imported_lab_workload_by_day[timetable.id][day] += len(session_groups)
                    for slots in session_groups:
                        halfday_key = self._get_lab_halfday_key(slots)
                        self.imported_lab_halfday_workload_by_timetable[timetable.id][halfday_key] += 1

    def _slots_reserved_for_imported_clubbed_slot(self, timetable_id, day, slots):
        reserved = self.clubbed_slot_reservations.get(timetable_id, set())
        return any((day, slot) in reserved for slot in slots)

    def _extract_lab_session_groups(self, slot_numbers, session_length):
        if session_length <= 0:
            return []

        groups = []
        run = []

        for slot_num in sorted(set(slot_numbers)):
            if not run or slot_num == run[-1] + 1:
                run.append(slot_num)
            else:
                while len(run) >= session_length:
                    groups.append(tuple(run[:session_length]))
                    run = run[session_length:]
                run = [slot_num]

        while len(run) >= session_length:
            groups.append(tuple(run[:session_length]))
            run = run[session_length:]

        return groups

    def _count_lab_sessions_from_slot_numbers(self, slot_numbers, session_length):
        return len(self._extract_lab_session_groups(slot_numbers, session_length))

    def _get_lab_halfday_key(self, slots):
        return 'AM' if max(slots) <= 4 else 'PM'

    def _record_lab_workload(self, timetable_id, day, slots=None):
        self.lab_workload_by_day[timetable_id][day] += 1
        if slots:
            halfday_key = self._get_lab_halfday_key(slots)
            self.lab_halfday_workload_by_timetable[timetable_id][halfday_key] += 1

    def _consume_imported_lab_workload(self, timetable_id, day, slots=None):
        current = self.imported_lab_workload_by_day[timetable_id].get(day, 0)
        if current > 0:
            self.imported_lab_workload_by_day[timetable_id][day] = current - 1

        if slots:
            halfday_key = self._get_lab_halfday_key(slots)
            current_halfday = self.imported_lab_halfday_workload_by_timetable[timetable_id].get(halfday_key, 0)
            if current_halfday > 0:
                self.imported_lab_halfday_workload_by_timetable[timetable_id][halfday_key] = current_halfday - 1

    def _seed_lab_workload_from_reservations(self, timetable_id, reservations):
        slots_by_day_course = defaultdict(list)
        session_length_by_key = {}

        for res in reservations:
            if res.is_blocked or not res.course:
                continue

            req = get_required_periods(res.course, self.config.semester)
            session_length = req.get('lab_type', 0)
            if session_length <= 0:
                continue

            key = (res.day, res.course.course_code)
            slots_by_day_course[key].append(res.time_slot.slot_number)
            session_length_by_key[key] = session_length

        for (day, course_code), slot_numbers in slots_by_day_course.items():
            session_length = session_length_by_key[(day, course_code)]
            session_groups = self._extract_lab_session_groups(slot_numbers, session_length)
            self.lab_workload_by_day[timetable_id][day] += len(session_groups)
            for slots in session_groups:
                halfday_key = self._get_lab_halfday_key(slots)
                self.lab_halfday_workload_by_timetable[timetable_id][halfday_key] += 1

    def _lab_workload_score(self, timetable_id, day):
        placed = self.lab_workload_by_day[timetable_id].get(day, 0)
        imported = self.imported_lab_workload_by_day[timetable_id].get(day, 0)
        occupied = sum(1 for existing_day, _slot in self.occupied[timetable_id] if existing_day == day)
        return (placed + imported, occupied, DAY_INDEX[day])

    def _ordered_days_for_lab(self, timetable_id):
        return sorted(DAYS, key=lambda day: self._lab_workload_score(timetable_id, day))

    def _ordered_days_for_lab_for_assignment(self, timetable_id, assignment):
        faculty_ids = self._get_lab_faculty_ids(assignment)

        def score(day):
            base_score = self._lab_workload_score(timetable_id, day)
            # Softly penalize 2nd/3rd same-day labs for all involved faculty
            # (main and assistant are treated the same).
            same_day_lab_penalty = sum(
                self.faculty_lab_sessions_by_day[fid].get(day, 0)
                for fid in faculty_ids
            )
            faculty_day_load = sum(self.faculty_day_load[fid].get(day, 0) for fid in faculty_ids)
            faculty_spread_penalty = sum(
                self._faculty_day_load_spread_penalty(fid, day)
                for fid in faculty_ids
            )
            faculty_long_lab_count = sum(
                self.faculty_long_lab_days[fid].get(day, 0)
                for fid in faculty_ids
            )
            return (
                same_day_lab_penalty,
                base_score[0],
                faculty_long_lab_count,
                faculty_spread_penalty,
                faculty_day_load,
                base_score[1],
                base_score[2],
            )

        return sorted(DAYS, key=score)

    def _lab_halfday_balance_score(self, timetable_id, slots):
        halfday_key = self._get_lab_halfday_key(slots)
        placed = self.lab_halfday_workload_by_timetable[timetable_id].get(halfday_key, 0)
        imported = self.imported_lab_halfday_workload_by_timetable[timetable_id].get(halfday_key, 0)
        return (placed + imported, slots[0])

    def _order_lab_slot_options(self, timetable_id, slot_options, prefer_odd_pairs=False):
        def score(slot_tuple):
            odd_penalty = 0
            if prefer_odd_pairs and slot_tuple[0] % 2 == 0:
                odd_penalty = 1
            return (
                self._lab_halfday_balance_score(timetable_id, slot_tuple)[0],
                odd_penalty,
                self._lab_halfday_balance_score(timetable_id, slot_tuple)[1],
            )

        return sorted(slot_options, key=score)

    def _ordered_days_for_group_lab(self, timetable_ids, faculty_ids=None):
        faculty_ids = list(faculty_ids or [])

        def score(day):
            per_timetable_scores = [self._lab_workload_score(timetable_id, day) for timetable_id in timetable_ids]
            # Softly penalize 2nd/3rd same-day labs for all anchor faculty.
            same_day_lab_penalty = sum(
                self.faculty_lab_sessions_by_day[fid].get(day, 0)
                for fid in faculty_ids
            )
            faculty_day_load = sum(self.faculty_day_load[fid].get(day, 0) for fid in faculty_ids)
            faculty_spread_penalty = sum(
                self._faculty_day_load_spread_penalty(fid, day)
                for fid in faculty_ids
            )
            faculty_long_lab_count = sum(
                self.faculty_long_lab_days[fid].get(day, 0)
                for fid in faculty_ids
            )
            return (
                same_day_lab_penalty,
                max((item[0] for item in per_timetable_scores), default=0),
                sum(item[0] for item in per_timetable_scores),
                faculty_long_lab_count,
                faculty_spread_penalty,
                faculty_day_load,
                sum(item[1] for item in per_timetable_scores),
                DAY_INDEX[day],
            )

        return sorted(DAYS, key=score)

    def _order_group_lab_slot_options(self, timetable_ids, slot_options, prefer_odd_pairs=False):
        def score(slot_tuple):
            halfday_key = self._get_lab_halfday_key(slot_tuple)
            halfday_total = sum(
                self.lab_halfday_workload_by_timetable[timetable_id].get(halfday_key, 0)
                + self.imported_lab_halfday_workload_by_timetable[timetable_id].get(halfday_key, 0)
                for timetable_id in timetable_ids
            )
            odd_penalty = 0
            if prefer_odd_pairs and slot_tuple[0] % 2 == 0:
                odd_penalty = 1
            return (halfday_total, odd_penalty, slot_tuple[0])

        return sorted(slot_options, key=score)

    def _prepare_generation(self, effective_date):
        if self._prepared:
            return {'success': True}

        batch_list = self._get_target_batches()
        if not batch_list:
            return {'success': False, 'error': 'No batches found', 'timetables': [], 'warnings': []}

        pec_errors = self._validate_pec_rules()
        if pec_errors:
            return {
                'success': False,
                'error': 'PEC configuration validation failed',
                'timetables': [],
                'warnings': pec_errors,
            }

        config = self.config
        program = config.program
        timetable_map = {}
        course_requirements_map = {}

        self._pec_group_handled_course_ids = set()
        self._pec_placeholder_courses = []

        elective_actual_course_codes = set(
            ElectiveCourseOffering.objects.filter(
                semester=config.semester,
                regulation_course_plan__branch=program.code,
                regulation_course_plan__program_type=program.level,
                is_active=True,
            ).values_list('actual_course__course_code', flat=True)
        )

        for batch in batch_list:
            timetable, created = Timetable.objects.update_or_create(
                academic_year=config.academic_year,
                semester=config.semester,
                year=config.year_of_study,
                program_batch=batch,
                defaults={
                    'batch': batch.batch_name,
                    'effective_from': effective_date,
                    'created_by': config.created_by,
                    'is_active': True,
                },
            )
            if not created:
                timetable.entries.all().delete()

            timetable_map[batch.id] = timetable

            reservations = list(
                FixedSlotReservation.objects.filter(
                    config=config, batch=batch,
                ).select_related('course', 'faculty', 'time_slot')
            )

            for res in reservations:
                TimetableEntry.objects.create(
                    timetable=timetable,
                    day=res.day,
                    time_slot=res.time_slot,
                    course=res.course if not res.is_blocked else None,
                    faculty=res.faculty if not res.is_blocked else None,
                    special_note=res.special_note if not res.is_blocked else res.block_reason,
                    is_blocked=res.is_blocked,
                    block_reason=res.block_reason if res.is_blocked else None,
                )

            self._seed_from_reservations(timetable, batch, reservations)

            assignments = Course_Assignment.objects.filter(
                academic_year=config.academic_year,
                batch=batch,
                semester=config.semester,
                is_active=True,
            ).exclude(
                course__course_code__in=elective_actual_course_codes
            ).select_related('course', 'faculty', 'lab_assistant', 'lab_main_faculty')

            course_requirements = []
            for asgn in assignments:
                req = get_required_periods(asgn.course)
                already_reserved = self._count_reserved_for_course(
                    reservations, asgn.course.course_code
                )

                theory_remaining = max(0, req['theory'] - already_reserved)
                lab_remaining = req['lab_sessions']
                if req['lab_type'] > 0 and already_reserved > 0:
                    lab_used = already_reserved // req['lab_type']
                    lab_remaining = max(0, req['lab_sessions'] - lab_used)
                    leftover = already_reserved - lab_used * req['lab_type']
                    theory_remaining = max(0, req['theory'] - leftover)

                course_requirements.append({
                    'assignment': asgn,
                    'theory_remaining': theory_remaining,
                    'lab_sessions_remaining': lab_remaining,
                    'lab_type': req['lab_type'],
                    'is_lab_course': asgn.course.course_type in ['L', 'LIT'],
                })

            course_requirements_map[batch.id] = course_requirements

        self._prepared = True
        self._batch_list = batch_list
        self._batch_ids = {batch.id for batch in batch_list}
        self._timetable_map = timetable_map
        self._course_requirements_map = course_requirements_map
        self._timetables_created = []
        self._rebuild_pending_clubbed_slot_set()

        return {'success': True}

    # ─── Lab availability helpers ────────────────────────────────

    def _lab_is_allowed(self, lab_id, program, year_of_study, course=None):
        """
        Check whether a lab is allowed for a given program/year/course.
        If the lab has NO restrictions, it is open to everyone.
        If restrictions exist, at least one must match.
        """
        restrictions = self.lab_restrictions.get(lab_id, [])
        if not restrictions:
            return True  # No restrictions → open to all

        for r in restrictions:
            program_ok = r['program_id'] is None or r['program_id'] == program.id
            year_ok = r['year_of_study'] is None or r['year_of_study'] == year_of_study
            course_ok = r['course_id'] is None or (course and r['course_id'] == course.pk)
            if program_ok and year_ok and course_ok:
                return True
        return False

    def _get_course_candidate_labs(self, course=None):
        """
        Return candidate lab rooms for a course.

        If explicit course-level restrictions exist, they are treated as
        exclusive lab choices for that course.
        """
        if not course:
            return list(self.labs)

        restricted_ids = self.course_restricted_lab_ids.get(course.pk, set())
        if restricted_ids:
            return [lab for lab in self.labs if lab.id in restricted_ids]

        return list(self.labs)

    def _get_preferred_lab_for_course(self, course):
        """If any lab has a course-level restriction matching this course, prefer it."""
        for lab in self.labs:
            for r in self.lab_restrictions.get(lab.id, []):
                if r['course_id'] and r['course_id'] == course.pk:
                    return lab
        return None

    def _get_available_lab_2p(self, day, slot_pair, program, year_of_study, course=None):
        """
        Get an available lab for a 2-period session.
        Returns LabRoom instance or None.
        """
        candidate_labs = self._get_course_candidate_labs(course)
        preferred = self._get_preferred_lab_for_course(course) if course else None
        if preferred and all(lab.id != preferred.id for lab in candidate_labs):
            preferred = None
        start_slot, end_slot = slot_pair

        # Try preferred lab first
        if preferred:
            start_state = self.lab_schedule_slots[(day, start_slot)].get(preferred.id)
            end_state = self.lab_schedule_slots[(day, end_slot)].get(preferred.id)
            if start_state is None and end_state is None:
                if self._lab_is_allowed(preferred.id, program, year_of_study, course):
                    return preferred

        # Try all other labs
        for lab in candidate_labs:
            if lab == preferred:
                continue
            start_state = self.lab_schedule_slots[(day, start_slot)].get(lab.id)
            end_state = self.lab_schedule_slots[(day, end_slot)].get(lab.id)
            if start_state is None and end_state is None and self._lab_is_allowed(lab.id, program, year_of_study, course):
                return lab
        return None

    def _get_available_lab_3p(self, day, slot_tuple, program, year_of_study, course=None):
        candidate_labs = self._get_course_candidate_labs(course)
        preferred = self._get_preferred_lab_for_course(course) if course else None
        if preferred and all(lab.id != preferred.id for lab in candidate_labs):
            preferred = None

        def is_free_for(lab_id):
            return all(self.lab_schedule_slots[(day, s)].get(lab_id) is None for s in slot_tuple)

        if preferred and is_free_for(preferred.id):
            if self._lab_is_allowed(preferred.id, program, year_of_study, course):
                return preferred

        for lab in candidate_labs:
            if lab == preferred:
                continue
            if is_free_for(lab.id) and self._lab_is_allowed(lab.id, program, year_of_study, course):
                return lab
        return None

    def _get_available_lab_4p(self, day, slot_tuple, program, year_of_study, course=None):
        """
        Get an available lab for a 4-period session.
        Needs to be free for BOTH underlying 2-period slots.
        """
        if slot_tuple == (1, 2, 3, 4):
            pair1, pair2 = (1, 2), (3, 4)
        else:
            pair1, pair2 = (5, 6), (7, 8)

        slots = list(slot_tuple)

        candidate_labs = self._get_course_candidate_labs(course)
        preferred = self._get_preferred_lab_for_course(course) if course else None
        if preferred and all(lab.id != preferred.id for lab in candidate_labs):
            preferred = None
        if preferred:
            if (all(self.lab_schedule_slots[(day, s)].get(preferred.id) is None for s in slots)
                    and self._lab_is_allowed(preferred.id, program, year_of_study, course)):
                return preferred

        for lab in candidate_labs:
            if lab == preferred:
                continue
            if (all(self.lab_schedule_slots[(day, s)].get(lab.id) is None for s in slots)
                    and self._lab_is_allowed(lab.id, program, year_of_study, course)):
                return lab
        return None

    def _book_lab_2p(self, day, slot_pair, lab, batch_label):
        start_slot, end_slot = slot_pair
        self.lab_schedule_slots[(day, start_slot)][lab.id] = batch_label
        self.lab_schedule_slots[(day, end_slot)][lab.id] = batch_label
        self.lab_schedule_2p[(day, slot_pair)][lab.id] = batch_label

    def _book_lab_3p(self, day, slot_tuple, lab, batch_label):
        for slot in slot_tuple:
            self.lab_schedule_slots[(day, slot)][lab.id] = batch_label

    def _book_lab_4p(self, day, slot_tuple, lab, batch_label):
        for slot in slot_tuple:
            self.lab_schedule_slots[(day, slot)][lab.id] = batch_label
        if slot_tuple == (1, 2, 3, 4):
            self.lab_schedule_2p[(day, (1, 2))][lab.id] = batch_label
            self.lab_schedule_2p[(day, (3, 4))][lab.id] = batch_label
        else:
            self.lab_schedule_2p[(day, (5, 6))][lab.id] = batch_label
            self.lab_schedule_2p[(day, (7, 8))][lab.id] = batch_label

    # ─── Faculty helpers ─────────────────────────────────────────

    def _is_faculty_available(self, faculty_id, day, slot_num):
        return (day, slot_num) not in self.faculty_schedule[faculty_id]

    def _is_faculty_available_for_slots(self, faculty_id, day, slots):
        for s in slots:
            if (day, s) in self.faculty_schedule[faculty_id]:
                return False
        return True

    def _book_faculty(self, faculty_id, day, slot_num):
        slot_key = (day, slot_num)
        if slot_key in self.faculty_schedule[faculty_id]:
            return
        self.faculty_schedule[faculty_id].add(slot_key)
        self.faculty_day_load[faculty_id][day] += 1

    def _faculty_day_load_spread_penalty(self, faculty_id, day):
        day_loads = [self.faculty_day_load[faculty_id].get(d, 0) for d in DAYS]
        min_load = min(day_loads) if day_loads else 0
        return self.faculty_day_load[faculty_id].get(day, 0) - min_load

    def _is_professor_id(self, faculty_id):
        return faculty_id in self._professor_ids

    def _is_slot_edge_period(self, slot_num):
        return slot_num in (1, NUM_PERIODS)

    def _same_halfday(self, slot_a, slot_b):
        return ((slot_a <= 4 and slot_b <= 4) or (slot_a >= 5 and slot_b >= 5))

    def _ordered_theory_slots_for_faculty_ids(self, faculty_ids):
        slot_order = [ts for ts in self.time_slots if not ts.is_break]
        if not slot_order:
            return slot_order

        if not self.prefer_avoid_professor_edges:
            return slot_order

        faculty_ids = [fid for fid in (faculty_ids or []) if fid]
        if not faculty_ids:
            return slot_order

        if not any(self._is_professor_id(fid) for fid in faculty_ids):
            return slot_order

        non_edge_slots = [ts for ts in slot_order if not self._is_slot_edge_period(ts.slot_number)]
        edge_slots = [ts for ts in slot_order if self._is_slot_edge_period(ts.slot_number)]

        # Keep preference soft by only pushing edges to the end.
        if non_edge_slots:
            return non_edge_slots + edge_slots
        return slot_order

    def _has_long_lab_day(self, faculty_id, day):
        return self.faculty_long_lab_days[faculty_id].get(day, 0) > 0

    def _record_long_lab_session_for_faculty_ids(self, faculty_ids, day, slots):
        slots_key = tuple(sorted(slots))
        if len(slots_key) < 4:
            return

        for fid in set(faculty_ids):
            if not fid:
                continue
            marker = (fid, day, slots_key)
            if marker in self._recorded_long_lab_sessions:
                continue
            self._recorded_long_lab_sessions.add(marker)
            self.faculty_long_lab_days[fid][day] += 1

    def _record_lab_session_for_faculty_ids(self, faculty_ids, day, slots):
        slots_key = tuple(sorted(slots))
        if len(slots_key) < 2:
            return

        for fid in set(faculty_ids):
            if not fid:
                continue
            marker = (fid, day, slots_key)
            if marker in self._recorded_lab_sessions:
                continue
            self._recorded_lab_sessions.add(marker)
            self.faculty_lab_sessions_by_day[fid][day] += 1

        # Keep existing long-lab tracking as a separate signal.
        self._record_long_lab_session_for_faculty_ids(faculty_ids, day, slots)

    def _get_lab_primary_faculty(self, assignment):
        return assignment.effective_lab_main_faculty or assignment.faculty

    def _get_lab_faculty_ids(self, assignment):
        faculty_ids = []
        lab_primary = self._get_lab_primary_faculty(assignment)
        if lab_primary and lab_primary.id:
            faculty_ids.append(lab_primary.id)
        if assignment.lab_assistant_id and assignment.lab_assistant_id not in faculty_ids:
            faculty_ids.append(assignment.lab_assistant_id)
        return faculty_ids

    def _are_lab_faculties_available_for_slots(self, assignment, day, slots):
        for fid in self._get_lab_faculty_ids(assignment):
            if not self._is_faculty_available_for_slots(fid, day, slots):
                return False
        return True

    def _book_lab_faculties_for_slots(self, assignment, day, slots):
        faculty_ids = self._get_lab_faculty_ids(assignment)
        for fid in faculty_ids:
            for slot_num in slots:
                self._book_faculty(fid, day, slot_num)

        self._record_lab_session_for_faculty_ids(faculty_ids, day, slots)

    def _assignment_requires_physical_lab(self, assignment):
        """
        Allow explicit opt-out from physical lab room usage.

        Primary source (new):
        - Course_Assignment.practical_in_classroom = True

        Backward-compatible markers (case-insensitive) in Course_Assignment.special_note:
        - NO_LAB_ROOM
        - CLASSROOM_LAB
        - NO_PHYSICAL_LAB
        """
        if getattr(assignment, 'practical_in_classroom', False):
            return False

        note = (assignment.special_note or '').upper()
        markers = ('NO_LAB_ROOM', 'CLASSROOM_LAB', 'NO_PHYSICAL_LAB')
        return not any(marker in note for marker in markers)

    def _get_consecutive_slot_options(self, length):
        """Build contiguous non-break slot windows of a given length.

        Two slots are only considered contiguous if:
        1. They are consecutive slot numbers (n, n+1).
        2. Neither is a break slot.
        3. The time gap between slot[n].end_time and slot[n+1].start_time
           is ≤ 15 minutes — this prevents lab windows from spanning
           a lunch break that is not stored as an explicit break TimeSlot.
        """
        from datetime import datetime as _dt
        slot_map = {ts.slot_number: ts for ts in self.time_slots}
        slots = [(ts.slot_number, ts.is_break) for ts in self.time_slots]
        options = []
        for i in range(len(slots) - length + 1):
            window = slots[i:i + length]
            nums = [n for n, _ in window]
            if any(is_break for _, is_break in window):
                continue
            if not all(nums[idx + 1] == nums[idx] + 1 for idx in range(len(nums) - 1)):
                continue
            # Reject windows where any adjacent pair has a gap > 15 min
            # (e.g. period 4 ends 12:15, period 5 starts 13:10 → 55 min lunch gap)
            has_lunch_gap = False
            for idx in range(len(nums) - 1):
                ts_curr = slot_map.get(nums[idx])
                ts_next = slot_map.get(nums[idx + 1])
                if ts_curr and ts_next:
                    today = _dt.today().date()
                    end_dt = _dt.combine(today, ts_curr.end_time)
                    start_dt = _dt.combine(today, ts_next.start_time)
                    gap_minutes = (start_dt - end_dt).total_seconds() / 60
                    if gap_minutes > 15:
                        has_lunch_gap = True
                        break
            if not has_lunch_gap:
                options.append(tuple(nums))
        return options

    # ─── Seed from existing reservations ─────────────────────────

    def _seed_from_reservations(self, timetable, batch, reservations):
        """
        Populate tracking structures from FixedSlotReservation entries
        that have already been written into TimetableEntry.
        """
        reserved_long_lab_slots = defaultdict(list)

        for res in reservations:
            slot_num = res.time_slot.slot_number
            day = res.day
            self.occupied[timetable.id].add((day, slot_num))

            if not res.is_blocked and self._is_blocked_by_me_lab_assist(day, [slot_num]):
                self.warnings.append(
                    f"Reservation overlaps ME assist block on {day} P{slot_num} for batch {batch.batch_name}"
                )

            if not res.is_blocked and res.course and res.course.course_type in ['L', 'LIT']:
                self._record_be_lab_slots_for_course(res.course, day, [slot_num])

            if not res.is_blocked and res.faculty:
                self._book_faculty(res.faculty.id, day, slot_num)
                if res.course:
                    req = get_required_periods(res.course, self.config.semester)
                    if req.get('lab_type', 0) >= 4:
                        reserved_long_lab_slots[(res.faculty.id, day)].append(slot_num)

        for (faculty_id, day), slot_numbers in reserved_long_lab_slots.items():
            for session_slots in self._extract_lab_session_groups(slot_numbers, 4):
                self._record_long_lab_session_for_faculty_ids([faculty_id], day, session_slots)

        self._seed_lab_workload_from_reservations(timetable.id, reservations)

    # ─── Schedule labs ─────────────────────────────────────────

    def _estimate_lab_flexibility(self, timetable, course_req, batch, program, lab_type):
        """Estimate how many placements are currently feasible for this lab request."""
        assignment = course_req['assignment']
        course = assignment.course
        needs_physical_lab = self._assignment_requires_physical_lab(assignment)

        if lab_type == 4:
            slot_options = list(LAB_SLOT_4_PERIOD)
        else:
            slot_options = self._get_consecutive_slot_options(lab_type)

        feasible_count = 0
        for day in DAYS:
            for slot_tuple in slot_options:
                slots = list(slot_tuple)

                if any((day, s) in self.occupied[timetable.id] for s in slots):
                    continue

                if self._slots_reserved_for_imported_clubbed_slot(timetable.id, day, slots):
                    continue

                if self._slots_reserved_for_pending_club(day, slots):
                    continue

                if self._is_blocked_by_me_lab_assist(day, slots):
                    continue

                if not self._are_lab_faculties_available_for_slots(assignment, day, slots):
                    continue

                if needs_physical_lab:
                    if lab_type == 4:
                        lab = self._get_available_lab_4p(day, slot_tuple, program, batch.year_of_study, course)
                    elif lab_type == 3:
                        lab = self._get_available_lab_3p(day, slot_tuple, program, batch.year_of_study, course)
                    else:
                        lab = self._get_available_lab_2p(day, slot_tuple, program, batch.year_of_study, course)

                    if lab is None:
                        continue

                feasible_count += 1

        return feasible_count

    def _schedule_labs(self, timetable, course_requirements, batch, program):
        """Schedule all lab sessions — 4-period first, then 3-period, then 2-period."""
        lab_courses = [c for c in course_requirements
                       if c['is_lab_course'] and c['lab_sessions_remaining'] > 0]
        if not lab_courses:
            return

        lab_4p = [c for c in lab_courses if c['lab_type'] == 4]
        lab_3p = [c for c in lab_courses if c['lab_type'] == 3]
        lab_2p = [c for c in lab_courses if c['lab_type'] == 2]

        lab_4p = sorted(
            lab_4p,
            key=lambda cr: (
                self._estimate_lab_flexibility(timetable, cr, batch, program, 4),
                cr['assignment'].course.course_code,
            )
        )
        for cr in lab_4p:
            self._schedule_4_period_lab(timetable, cr, batch, program)

        lab_3p = sorted(
            lab_3p,
            key=lambda cr: (
                self._estimate_lab_flexibility(timetable, cr, batch, program, 3),
                cr['assignment'].course.course_code,
            )
        )
        for cr in lab_3p:
            self._schedule_3_period_lab(timetable, cr, batch, program)

        lab_2p = sorted(
            lab_2p,
            key=lambda cr: (
                self._estimate_lab_flexibility(timetable, cr, batch, program, 2),
                cr['assignment'].course.course_code,
            )
        )
        for cr in lab_2p:
            self._schedule_2_period_lab(timetable, cr, batch, program)

    def _schedule_lab_request(self, timetable, course_req, batch, program, lab_type):
        if lab_type == 4:
            self._schedule_4_period_lab(timetable, course_req, batch, program)
        elif lab_type == 3:
            self._schedule_3_period_lab(timetable, course_req, batch, program)
        elif lab_type == 2:
            self._schedule_2_period_lab(timetable, course_req, batch, program)

    def _schedule_lab_type_globally(self, batch_list, timetable_map, course_requirements_map, program, lab_type):
        """
        Schedule one lab duration across every batch in this config before
        moving to the next shorter duration.
        """
        requests = []
        for batch in batch_list:
            timetable = timetable_map[batch.id]
            for course_req in course_requirements_map.get(batch.id, []):
                if (
                    course_req['is_lab_course']
                    and course_req['lab_sessions_remaining'] > 0
                    and course_req['lab_type'] == lab_type
                ):
                    requests.append((batch, timetable, course_req))

        requests.sort(
            key=lambda item: (
                self._estimate_lab_flexibility(item[1], item[2], item[0], program, lab_type),
                -item[2]['lab_sessions_remaining'],
                item[0].batch_name,
                item[2]['assignment'].course.course_code,
            )
        )

        for batch, timetable, course_req in requests:
            if course_req['lab_sessions_remaining'] <= 0 or course_req['lab_type'] != lab_type:
                continue
            self._schedule_lab_request(timetable, course_req, batch, program, lab_type)

    def _schedule_3_period_lab(self, timetable, course_req, batch, program):
        assignment = course_req['assignment']
        course = assignment.course
        needs_physical_lab = self._assignment_requires_physical_lab(assignment)

        while course_req['lab_sessions_remaining'] > 0:
            scheduled = False
            day_order = self._ordered_days_for_lab_for_assignment(timetable.id, assignment)

            for day in day_order:
                if scheduled:
                    break
                slot_options = self._order_lab_slot_options(
                    timetable.id,
                    self._get_consecutive_slot_options(3),
                )

                for slot_tuple in slot_options:
                    slots = list(slot_tuple)

                    if any((day, s) in self.occupied[timetable.id] for s in slots):
                        continue

                    if self._slots_reserved_for_imported_clubbed_slot(timetable.id, day, slots):
                        continue

                    if self._slots_reserved_for_pending_club(day, slots):
                        continue

                    if self._is_blocked_by_me_lab_assist(day, slots):
                        continue

                    if not self._are_lab_faculties_available_for_slots(assignment, day, slots):
                        continue

                    lab = None
                    if needs_physical_lab:
                        lab = self._get_available_lab_3p(
                            day, slot_tuple, program, batch.year_of_study, course
                        )
                        if lab is None:
                            continue

                    for idx, slot_num in enumerate(slots):
                        ts = TimeSlot.objects.get(slot_number=slot_num)
                        if needs_physical_lab and lab:
                            note = f"{lab.room_code} (Start)" if idx == 0 else (
                                f"{lab.room_code} (End)" if idx == len(slots) - 1 else lab.room_code
                            )
                        else:
                            note = "Classroom Lab"
                        lab_primary_faculty = self._get_lab_primary_faculty(assignment)
                        TimetableEntry.objects.create(
                            timetable=timetable,
                            day=day,
                            time_slot=ts,
                            course=course,
                            faculty=lab_primary_faculty,
                            lab_assistant=assignment.lab_assistant if assignment.lab_assistant else None,
                            is_lab=True,
                            lab_room=lab if needs_physical_lab else None,
                            special_note=note,
                        )
                        self.occupied[timetable.id].add((day, slot_num))

                    self._book_lab_faculties_for_slots(assignment, day, slots)

                    if needs_physical_lab and lab:
                        self._book_lab_3p(day, slot_tuple, lab, batch.batch_name)
                    self._record_lab_workload(timetable.id, day, slots)
                    self._record_be_lab_slots_for_course(course, day, slots)
                    course_req['lab_sessions_remaining'] -= 1
                    scheduled = True
                    break

            if not scheduled:
                self.warnings.append(
                    f"Could not schedule 3-period lab for {course.course_code} "
                    f"(batch {batch.batch_name})"
                )
                break

    def _schedule_4_period_lab(self, timetable, course_req, batch, program):
        assignment = course_req['assignment']
        course = assignment.course
        needs_physical_lab = self._assignment_requires_physical_lab(assignment)

        while course_req['lab_sessions_remaining'] > 0:
            scheduled = False
            day_order = self._ordered_days_for_lab_for_assignment(timetable.id, assignment)

            for day in day_order:
                if scheduled:
                    break
                slot_options = self._order_lab_slot_options(
                    timetable.id,
                    list(LAB_SLOT_4_PERIOD),
                )

                for slot_tuple in slot_options:
                    slots = list(slot_tuple)

                    # Any slot already occupied?
                    if any((day, s) in self.occupied[timetable.id] for s in slots):
                        continue

                    if self._slots_reserved_for_imported_clubbed_slot(timetable.id, day, slots):
                        continue

                    if self._slots_reserved_for_pending_club(day, slots):
                        continue

                    if self._is_blocked_by_me_lab_assist(day, slots):
                        continue

                    # Faculty available?
                    if not self._are_lab_faculties_available_for_slots(assignment, day, slots):
                        continue

                    # Lab room available?
                    lab = None
                    if needs_physical_lab:
                        lab = self._get_available_lab_4p(
                            day, slot_tuple, program, batch.year_of_study, course
                        )
                        if lab is None:
                            continue

                    # ── All checks passed — schedule ──
                    session_label = "Morning" if slot_tuple == (1, 2, 3, 4) else "Afternoon"
                    for i, slot_num in enumerate(slots):
                        ts = TimeSlot.objects.get(slot_number=slot_num)
                        if needs_physical_lab and lab:
                            note = f"{lab.room_code} ({session_label})" if i == 0 else (
                                f"{lab.room_code} (End)" if i == len(slots) - 1 else lab.room_code
                            )
                        else:
                            note = "Classroom Lab"
                        lab_primary_faculty = self._get_lab_primary_faculty(assignment)
                        TimetableEntry.objects.create(
                            timetable=timetable,
                            day=day,
                            time_slot=ts,
                            course=course,
                            faculty=lab_primary_faculty,
                            lab_assistant=assignment.lab_assistant if assignment.lab_assistant else None,
                            is_lab=True,
                            lab_room=lab if needs_physical_lab else None,
                            special_note=note,
                        )
                        self.occupied[timetable.id].add((day, slot_num))

                    self._book_lab_faculties_for_slots(assignment, day, slots)

                    if needs_physical_lab and lab:
                        self._book_lab_4p(day, slot_tuple, lab, batch.batch_name)
                    self._record_lab_workload(timetable.id, day, slots)
                    self._record_be_lab_slots_for_course(course, day, slots)
                    course_req['lab_sessions_remaining'] -= 1
                    scheduled = True
                    break

            if not scheduled:
                self.warnings.append(
                    f"Could not schedule 4-period lab for {course.course_code} "
                    f"(batch {batch.batch_name})"
                )
                break

    def _schedule_2_period_lab(self, timetable, course_req, batch, program):
        assignment = course_req['assignment']
        course = assignment.course
        needs_physical_lab = self._assignment_requires_physical_lab(assignment)

        while course_req['lab_sessions_remaining'] > 0:
            scheduled = False
            day_order = self._ordered_days_for_lab_for_assignment(timetable.id, assignment)

            for day in day_order:
                if scheduled:
                    break
                slot_options = self._order_lab_slot_options(
                    timetable.id,
                    self._get_consecutive_slot_options(2),
                    prefer_odd_pairs=True,
                )

                for slot_pair in slot_options:
                    start_slot, end_slot = slot_pair
                    slots = [start_slot, end_slot]

                    # Any slot already occupied?
                    if ((day, start_slot) in self.occupied[timetable.id]
                            or (day, end_slot) in self.occupied[timetable.id]):
                        continue

                    if self._slots_reserved_for_imported_clubbed_slot(timetable.id, day, slots):
                        continue

                    if self._slots_reserved_for_pending_club(day, slots):
                        continue

                    if self._is_blocked_by_me_lab_assist(day, slots):
                        continue

                    if not self._are_lab_faculties_available_for_slots(assignment, day, slots):
                        continue

                    # Lab room?
                    lab = None
                    if needs_physical_lab:
                        lab = self._get_available_lab_2p(
                            day, slot_pair, program, batch.year_of_study, course
                        )
                        if lab is None:
                            continue

                    # ── Schedule ──
                    start_ts = TimeSlot.objects.get(slot_number=start_slot)
                    end_ts = TimeSlot.objects.get(slot_number=end_slot)

                    TimetableEntry.objects.create(
                        timetable=timetable,
                        day=day,
                        time_slot=start_ts,
                        course=course,
                        faculty=self._get_lab_primary_faculty(assignment),
                        lab_assistant=assignment.lab_assistant if assignment.lab_assistant else None,
                        is_lab=True,
                        lab_end_slot=end_ts,
                        lab_room=lab if needs_physical_lab else None,
                        special_note=lab.room_code if (needs_physical_lab and lab) else 'Classroom Lab',
                    )
                    TimetableEntry.objects.create(
                        timetable=timetable,
                        day=day,
                        time_slot=end_ts,
                        course=course,
                        faculty=self._get_lab_primary_faculty(assignment),
                        lab_assistant=assignment.lab_assistant if assignment.lab_assistant else None,
                        is_lab=True,
                        lab_room=lab if needs_physical_lab else None,
                        special_note=lab.room_code if (needs_physical_lab and lab) else 'Classroom Lab',
                    )

                    self._book_lab_faculties_for_slots(assignment, day, (start_slot, end_slot))
                    for s in (start_slot, end_slot):
                        self.occupied[timetable.id].add((day, s))

                    if needs_physical_lab and lab:
                        self._book_lab_2p(day, slot_pair, lab, batch.batch_name)
                    self._record_lab_workload(timetable.id, day, slots)
                    self._record_be_lab_slots_for_course(course, day, slots)
                    course_req['lab_sessions_remaining'] -= 1
                    scheduled = True
                    break

            if not scheduled:
                self.warnings.append(
                    f"Could not schedule 2-period lab for {course.course_code} "
                    f"(batch {batch.batch_name})"
                )
                break

    # ─── Schedule same-time courses across ALL batches ───────────

    def _get_all_elective_faculty(self, course, semester):
        """
        For a placeholder/elective course (e.g., PEC-03), return ALL faculty
        teaching under it via ElectiveCourseOffering + ElectiveOfferingFacultyAssignment.
        
        This ensures that when PEC-03 is scheduled at a time slot, ALL faculty
        offering courses under that elective slot are checked for availability
        and have their slots blocked — not just the per-batch Course_Assignment faculty.
        
        Returns: set of faculty IDs
        """
        elective_faculty_ids = set()

        if not course.is_placeholder:
            return elective_faculty_ids

        # Find all RegulationCoursePlan entries for this placeholder course
        rcp_ids = RegulationCoursePlan.objects.filter(
            course=course,
        ).values_list('id', flat=True)

        if not rcp_ids:
            return elective_faculty_ids

        # Find all active offerings for these plans in the current semester
        offerings = ElectiveCourseOffering.objects.filter(
            regulation_course_plan_id__in=rcp_ids,
            semester=semester,
            is_active=True,
        )

        # Collect all faculty assigned to these offerings
        for offering in offerings:
            faculty_assignments = ElectiveOfferingFacultyAssignment.objects.filter(
                offering=offering,
                is_active=True,
            ).select_related('faculty')
            for fa in faculty_assignments:
                if fa.faculty_id:
                    elective_faculty_ids.add(fa.faculty_id)

        return elective_faculty_ids

    def _schedule_same_time_courses(self, batches, timetable_map,
                                     course_requirements_map, program):
        """
        For each SameTimeConstraint in this config, find a (day, period) that
        is free for EVERY batch and where every batch's faculty is available,
        then place the course in that slot across all timetables at once.

        For placeholder/elective courses (PEC, OEC), also checks and blocks
        ALL faculty from ElectiveCourseOffering assignments — not just the
        per-batch Course_Assignment faculty.

        This runs AFTER Phase 1 (fixed reservations) and BEFORE the normal
        per-batch auto-fill.

        Updates course_requirements_map so the auto-fill phase sees the
        correct remaining counts.
        
        AUTO-SCHEDULES PEC PLACEHOLDER COURSES: If PEC courses exist in the
        regulation course plans for this semester but aren't in SameTimeConstraint,
        they are automatically added and scheduled as same-time constraints.
        """
        constraints = SameTimeConstraint.objects.filter(
            config=self.config,
        ).select_related('course').order_by('course__course_code')

        # If PEC group config exists, PEC placeholders are handled in
        # _schedule_pec_groups and must not be scheduled again here.
        has_pec_group_config = PECGroupConfig.objects.filter(
            semester=self.config.semester,
            branch=program.code,
            program_type=program.level,
        ).exists()
        
        constraint_courses = {c.course_id for c in constraints}
        
        # Auto-detect PEC placeholder courses and add them automatically
        # only when PEC group config is not being used.
        auto_constraints = []
        if not has_pec_group_config:
            pec_courses = Course.objects.filter(
                is_placeholder=True,
                placeholder_type='PEC'
            )
            pec_plans = RegulationCoursePlan.objects.filter(
                course__in=pec_courses,
                semester=self.config.semester.semester_number,
                branch=program.code,
                program_type=program.level,
            ).select_related('course')

            auto_constraints = []
            for plan in pec_plans:
                if plan.course_id not in constraint_courses:
                    auto_constraints.append(plan.course)

        # Convert constraints to list of Course objects (consistently)
        constraints_list = [
            c.course for c in constraints
            if not (
                has_pec_group_config
                and c.course.is_placeholder
                and c.course.course_code.startswith('PEC')
            )
        ]
        constraints_list.extend(auto_constraints)

        if not constraints_list:
            return

        # Track which slot positions are already used by PEC placeholder slots.
        # Used to enforce pair-wise overlap compatibility rules between PEC slots.
        pec_slot_placements = defaultdict(set)  # course_pk -> {(day, slot), ...}
        same_time_courses = {c.pk: c for c in constraints_list}

        for course in constraints_list:
            # Skip PEC courses already handled by _schedule_pec_groups
            if hasattr(self, '_pec_group_handled_course_ids') and course.pk in self._pec_group_handled_course_ids:
                continue

            req = get_required_periods(course, self.config.semester)

            # Gather per-batch assignments for this course
            assignments_map = {}   # batch_id -> Course_Assignment
            for batch in batches:
                asgn = Course_Assignment.objects.filter(
                    academic_year=self.config.academic_year,
                    batch=batch,
                    course=course,
                    is_active=True,
                ).select_related('faculty').first()
                if asgn:
                    assignments_map[batch.id] = asgn

            # ── Gather ALL elective offering faculty for placeholder courses ──
            # e.g., PEC-03 may have 5 actual courses offered by 5 different faculty;
            # ALL of them must be available and blocked at the scheduled slot.
            elective_faculty_ids = self._get_all_elective_faculty(
                course, self.config.semester
            )

            # For placeholder courses without Course_Assignments, build
            # a synthetic assignments_map using offering faculty so the
            # timetable entries can still be created.
            if not assignments_map and course.is_placeholder and elective_faculty_ids:
                # Pick a representative faculty from offerings for each batch
                representative_faculty_id = next(iter(elective_faculty_ids))
                try:
                    rep_faculty = Faculty_Profile.objects.get(id=representative_faculty_id)
                except Faculty_Profile.DoesNotExist:
                    rep_faculty = None

                if rep_faculty:
                    for batch in batches:
                        # Create a lightweight object to hold faculty for entry creation
                        assignments_map[batch.id] = type('SyntheticAssignment', (), {
                            'faculty': rep_faculty,
                            'faculty_id': rep_faculty.id,
                            'course': course,
                        })()

            if not assignments_map:
                continue

            # Also include per-batch assignment faculty in the set
            all_faculty_ids = set(elective_faculty_ids)
            for asgn in assignments_map.values():
                if asgn.faculty_id:
                    all_faculty_ids.add(asgn.faculty_id)

            # ── Resolve actual course codes for display ──
            # For placeholder courses, resolve to actual elective offering codes
            same_time_note = 'Same-time'
            if course.is_placeholder:
                rcp_ids = RegulationCoursePlan.objects.filter(
                    course=course,
                    semester=self.config.semester.semester_number,
                    branch=program.code,
                    program_type=program.level,
                ).values_list('id', flat=True)
                if rcp_ids:
                    offerings = ElectiveCourseOffering.objects.filter(
                        regulation_course_plan_id__in=rcp_ids,
                        semester=self.config.semester,
                        is_active=True,
                    ).select_related('actual_course').order_by('actual_course__course_code')
                    codes = [o.actual_course.course_code for o in offerings]
                    if codes:
                        same_time_note = '/'.join(codes)
                    else:
                        same_time_note = course.course_code
                else:
                    same_time_note = course.course_code
            else:
                same_time_note = course.course_code

            # ── Schedule theory periods for this course across all batches ──
            theory_needed = req['theory']

            # Subtract already-reserved periods (from FixedSlotReservation)
            for batch in batches:
                reqs = course_requirements_map.get(batch.id, [])
                for cr in reqs:
                    if cr['assignment'].course.course_code == course.course_code:
                        theory_needed = min(theory_needed, cr['theory_remaining'])
                        break

            course_days = set()
            periods_placed = 0

            for _ in range(theory_needed):
                scheduled = False
                day_order = DAYS.copy()
                day_order = sorted(day_order, key=lambda d: d in course_days)

                for day in day_order:
                    if scheduled:
                        break
                    slot_order = self._ordered_theory_slots_for_faculty_ids(all_faculty_ids)

                    for ts in slot_order:
                        if ts.is_break:
                            continue
                        slot = ts.slot_number

                        # Enforce PEC overlap compatibility matrix.
                        if course.is_placeholder and course.course_code.startswith('PEC'):
                            violates_pec_rule = False
                            for other_course_id, used_slots in pec_slot_placements.items():
                                if not used_slots or (day, slot) not in used_slots:
                                    continue

                                other_course = same_time_courses.get(other_course_id)
                                if not other_course:
                                    continue

                                if not self._pec_pair_can_overlap(course, other_course):
                                    violates_pec_rule = True
                                    break

                            if violates_pec_rule:
                                continue

                        if self._is_blocked_by_me_lab_assist(day, [slot]):
                            continue

                        # Check ALL batches are free at this slot
                        all_free = True
                        for batch in batches:
                            tt = timetable_map[batch.id]
                            if (day, slot) in self.occupied[tt.id]:
                                all_free = False
                                break
                        if not all_free:
                            continue

                        # Check ALL faculty are available (batch + elective offering)
                        all_faculty_ok = True
                        for fid in all_faculty_ids:
                            if not self._is_faculty_available(fid, day, slot):
                                all_faculty_ok = False
                                break
                        if not all_faculty_ok:
                            continue

                        # ── Place the course for every batch ──
                        for batch in batches:
                            tt = timetable_map[batch.id]
                            asgn = assignments_map.get(batch.id)
                            if asgn:
                                TimetableEntry.objects.create(
                                    timetable=tt,
                                    day=day,
                                    time_slot=ts,
                                    course=course,
                                    faculty=asgn.faculty,
                                    is_lab=False,
                                    special_note=same_time_note,
                                )

                        # ── Block ALL faculty (batch + elective offering) ──
                        for fid in all_faculty_ids:
                            self._book_faculty(fid, day, slot)

                        for batch in batches:
                            tt = timetable_map[batch.id]
                            self.occupied[tt.id].add((day, slot))

                        if course.is_placeholder and course.course_code.startswith('PEC'):
                            pec_slot_placements[course.pk].add((day, slot))

                        course_days.add(day)
                        periods_placed += 1
                        scheduled = True
                        break

                if not scheduled:
                    remaining = theory_needed - periods_placed
                    self.warnings.append(
                        f"Could not schedule same-time theory for "
                        f"{course.course_code} ({remaining} periods remaining)"
                    )
                    break

            # ── Reduce theory_remaining in course_requirements_map ──
            for batch in batches:
                reqs = course_requirements_map.get(batch.id, [])
                for cr in reqs:
                    if cr['assignment'].course.course_code == course.course_code:
                        cr['theory_remaining'] = max(0, cr['theory_remaining'] - periods_placed)
                        break

    # ─── Schedule clubbed PG courses ────────────────────────────

    def _schedule_clubbed_courses(
        self,
        batches,
        timetable_map,
        course_requirements_map,
        place_theory=True,
        place_labs=True,
        lab_type_filter=None,
    ):
        """
        For courses that are "clubbed" across multiple PG programs
        (ClubbedCourseGroup), reuse the same (day, slot) placements from
        a previously-generated program's timetable.

        self.clubbed_slots is populated by generate_all() and contains either:
            { (course_code, faculty_id): [(day, slot_num), ...] }
        or:
            { (course_code, faculty_id): {'theory': [...], 'lab': [...]} }

        For each batch, if a Course_Assignment matches a key in
        clubbed_slots, we place the course at the same day+slot,
        mark the slot as occupied, and decrement theory_remaining.
        """
        if not self.clubbed_slots:
            return

        for batch in batches:
            tt = timetable_map[batch.id]
            reqs = course_requirements_map.get(batch.id, [])

            for cr in reqs:
                asgn = cr['assignment']
                key = self._clubbing_key_for_assignment(asgn)
                if not key:
                    continue
                payload = self.clubbed_slots.get(key)
                if not payload:
                    continue

                if isinstance(payload, dict):
                    theory_slots = list(payload.get('theory', []))
                    lab_slots = list(payload.get('lab', []))
                else:
                    theory_slots = list(payload)
                    lab_slots = []

                if place_theory and theory_slots and cr.get('theory_remaining', 0) > 0:
                    theory_periods_placed = 0
                    for day, slot_num in theory_slots:
                        if self._is_blocked_by_me_lab_assist(day, [slot_num]):
                            continue

                        if (day, slot_num) in self.occupied[tt.id]:
                            self.warnings.append(
                                f"Clubbed slot ({day}, P{slot_num}) already occupied "
                                f"for {asgn.course.course_code} batch {batch.batch_name}"
                            )
                            continue

                        ts = TimeSlot.objects.get(slot_number=slot_num)
                        TimetableEntry.objects.create(
                            timetable=tt,
                            day=day,
                            time_slot=ts,
                            course=asgn.course,
                            faculty=asgn.faculty,
                            is_lab=False,
                            special_note="Clubbed",
                        )
                        self.occupied[tt.id].add((day, slot_num))
                        self._book_faculty(asgn.faculty_id, day, slot_num)
                        theory_periods_placed += 1

                    if theory_periods_placed > 0:
                        cr['theory_remaining'] = max(0, cr['theory_remaining'] - theory_periods_placed)

                # Place lab clubbed slots as contiguous sessions
                if (
                    place_labs
                    and lab_slots
                    and cr.get('lab_sessions_remaining', 0) > 0
                    and (lab_type_filter is None or cr.get('lab_type') == lab_type_filter)
                ):
                    by_day = defaultdict(list)
                    # lab slot item can be:
                    #   (day, slot) or (day, slot, lab_room_id)
                    for item in lab_slots:
                        if len(item) >= 3:
                            day, slot_num, room_id = item[0], item[1], item[2]
                        else:
                            day, slot_num = item[0], item[1]
                            room_id = None
                        by_day[day].append((slot_num, room_id))

                    lab_sessions = []
                    for day, slot_items in by_day.items():
                        sorted_items = sorted(slot_items, key=lambda x: x[0])
                        if not sorted_items:
                            continue

                        run_slots = [sorted_items[0][0]]
                        run_room = sorted_items[0][1]
                        for slot_num, room_id in sorted_items[1:]:
                            same_room_chain = (
                                room_id == run_room
                                or room_id is None
                                or run_room is None
                            )
                            if slot_num == run_slots[-1] + 1 and same_room_chain:
                                run_slots.append(slot_num)
                                if run_room is None and room_id is not None:
                                    run_room = room_id
                            else:
                                lab_sessions.append((day, run_slots, run_room))
                                run_slots = [slot_num]
                                run_room = room_id
                        if run_slots:
                            lab_sessions.append((day, run_slots, run_room))

                    lab_sessions.sort(key=lambda item: (item[0], item[1][0]))
                    target_len = cr.get('lab_type', 0)
                    lab_sessions_placed = 0

                    for day, slot_seq, source_room_id in lab_sessions:
                        if cr['lab_sessions_remaining'] <= 0:
                            break
                        if target_len and len(slot_seq) < target_len:
                            continue

                        use_slots = slot_seq[:target_len] if target_len else slot_seq
                        if self._is_blocked_by_me_lab_assist(day, use_slots):
                            continue

                        if any((day, s) in self.occupied[tt.id] for s in use_slots):
                            self.warnings.append(
                                f"Clubbed lab slot ({day}, {','.join('P'+str(s) for s in use_slots)}) already occupied "
                                f"for {asgn.course.course_code} batch {batch.batch_name}"
                            )
                            continue

                        source_room = None
                        if source_room_id:
                            source_room = LabRoom.objects.filter(id=source_room_id).first()

                        for idx, slot_num in enumerate(use_slots):
                            ts = TimeSlot.objects.get(slot_number=slot_num)
                            note = 'Clubbed LAB'
                            if idx == 0:
                                note = 'Clubbed LAB (Start)'
                            elif idx == len(use_slots) - 1:
                                note = 'Clubbed LAB (End)'

                            TimetableEntry.objects.create(
                                timetable=tt,
                                day=day,
                                time_slot=ts,
                                course=asgn.course,
                                faculty=self._get_lab_primary_faculty(asgn),
                                lab_assistant=asgn.lab_assistant if asgn.lab_assistant else None,
                                is_lab=True,
                                lab_room=source_room,
                                special_note=note,
                            )
                            self.occupied[tt.id].add((day, slot_num))

                        self._book_lab_faculties_for_slots(asgn, day, use_slots)

                        self._record_lab_workload(tt.id, day, use_slots)
                        self._record_be_lab_slots_for_course(asgn.course, day, use_slots)
                        self._consume_imported_lab_workload(tt.id, day, use_slots)
                        lab_sessions_placed += 1
                        cr['lab_sessions_remaining'] = max(0, cr['lab_sessions_remaining'] - 1)

                    if lab_sessions_placed == 0 and cr.get('lab_sessions_remaining', 0) > 0:
                        self.warnings.append(
                            f"Could not place clubbed lab session for {asgn.course.course_code} batch {batch.batch_name}"
                        )

    def _get_clubbed_slot_payload(self, course_code, faculty_ids):
        for faculty_id in faculty_ids or []:
            payload = self.clubbed_slots.get((course_code, faculty_id))
            if payload:
                if isinstance(payload, dict):
                    return {
                        'theory': list(payload.get('theory', [])),
                        'lab': list(payload.get('lab', [])),
                    }
                return {
                    'theory': list(payload),
                    'lab': [],
                }
        return {'theory': [], 'lab': []}

    def _get_clubbed_slots_for_course(self, course_code, faculty_ids):
        return self._get_clubbed_slot_payload(course_code, faculty_ids)['theory']

    def _get_clubbed_lab_slots_for_course(self, course_code, faculty_ids):
        return self._get_clubbed_slot_payload(course_code, faculty_ids)['lab']

    @staticmethod
    def _to_day_slot_pairs(slot_items):
        """Normalize [(day, slot), (day, slot, room_id), ...] -> {(day, slot), ...}."""
        pairs = set()
        for item in slot_items or []:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                pairs.add((item[0], item[1]))
        return pairs

    def _slot_reserved_for_pending_club(self, day, slot, allowed_slots=None):
        allowed = self._to_day_slot_pairs(allowed_slots)
        if (day, slot) in allowed:
            return False
        return (day, slot) in getattr(self, 'pending_clubbed_slot_set', set())

    def _slots_reserved_for_pending_club(self, day, slots, allowed_slots=None):
        return any(
            self._slot_reserved_for_pending_club(day, slot, allowed_slots=allowed_slots)
            for slot in slots
        )

    @staticmethod
    def _filter_public_warnings(warnings):
        filtered = []
        for warning in warnings:
            if warning.startswith('PEC group ') and 'scheduling independently.' in warning:
                continue
            if warning.startswith('PEC group ') and 'will be scheduled independently.' in warning:
                continue
            filtered.append(warning)
        return filtered

    def _pec_pair_can_overlap(self, slot_a_course, slot_b_course):
        """
        Return True if two PEC placeholder slots are allowed to overlap.
        Overlap is allowed only when all configured pair rows for the slot pair
        are marked can_overlap=True. Any False row blocks overlap.
        """
        if slot_a_course.pk == slot_b_course.pk:
            return True

        blocked_exists = PECCourseCombinationRule.objects.filter(
            config=self.config,
            can_overlap=False,
        ).filter(
            Q(slot_a_course=slot_a_course, slot_b_course=slot_b_course)
            | Q(slot_a_course=slot_b_course, slot_b_course=slot_a_course)
        ).exists()

        return not blocked_exists

    # ─── PEC Group-aware scheduling ──────────────────────────────

    def _get_offering_faculty_for_course(self, actual_course, semester):
        """
        Get all faculty IDs assigned to a specific actual course's offerings.
        Returns set of faculty_ids.
        """
        faculty_ids = set()
        offerings = ElectiveCourseOffering.objects.filter(
            actual_course=actual_course,
            semester=semester,
            is_active=True,
        )
        for off in offerings:
            for fa in ElectiveOfferingFacultyAssignment.objects.filter(
                offering=off, is_active=True
            ):
                if fa.faculty_id:
                    faculty_ids.add(fa.faculty_id)
        return faculty_ids

    def _schedule_pec_groups(
        self,
        batches,
        timetable_map,
        course_requirements_map,
        program,
        schedule_theory=True,
        schedule_labs=True,
        lab_type_filter=None,
    ):
        """
        Group-aware PEC scheduling using PECGroupConfig.

        Algorithm:
        1. Load PECGroupConfig for this config's semester + program.
        2. For each group, resolve actual Course objects and their workloads.
        3. Find the "anchor" course (highest total workload) in each group.
        4. Schedule the anchor course first — labs (consecutive), then theory.
           All its periods are placed across all batches simultaneously.
        5. For each non-anchor course in the same group, attempt to overlay it
           on the SAME day+slot as the anchor — but only if all that course's
           faculty are free.  This is best-effort; if faculty clash, the non-
           anchor course is scheduled independently in Phase 2.
        6. Different groups are forbidden from occupying the same (day, slot).

        After this phase, the course_requirements_map entries for PEC
        placeholder courses are decremented so Phase 2 won't double-schedule.
        """
        config = self.config

        # Find PECGroupConfig for this program
        branch = config.program.code
        # We need to determine program_type — infer from Program.level
        program_type = config.program.level  # 'UG' or 'PG'

        try:
            group_config = PECGroupConfig.objects.get(
                semester=config.semester,
                branch=branch,
                program_type=program_type,
            )
        except PECGroupConfig.DoesNotExist:
            # No group config — nothing to do
            return

        groups = group_config.groups or []
        if not groups:
            return

        # Identify PEC placeholder courses for this config from assigned courses
        # first; if missing, fall back to regulation plans for this program.
        pec_placeholder_courses = {}
        for batch in batches:
            reqs = course_requirements_map.get(batch.id, [])
            for cr in reqs:
                c = cr['assignment'].course
                if c and c.is_placeholder and c.course_code.startswith('PEC'):
                    pec_placeholder_courses[c.course_code] = c

        if not pec_placeholder_courses:
            pec_plans = RegulationCoursePlan.objects.filter(
                semester=config.semester.semester_number,
                branch=config.program.code,
                program_type=config.program.level,
                course__is_placeholder=True,
                course__course_code__startswith='PEC',
            ).select_related('course')
            for plan in pec_plans:
                pec_placeholder_courses[plan.course.course_code] = plan.course

        if not pec_placeholder_courses:
            return

        # Keep deterministic placeholder order for group slot entry creation.
        self._pec_placeholder_courses = [
            pec_placeholder_courses[k]
            for k in sorted(pec_placeholder_courses.keys())
        ]

        # Collect all actual course codes from ALL groups for quick lookup
        all_group_course_codes = set()
        for g in groups:
            for cd in g:
                all_group_course_codes.add(cd.get('code', ''))

        # Pre-load actual Course objects for all codes in groups
        actual_courses = {
            c.course_code: c
            for c in Course.objects.filter(course_code__in=all_group_course_codes)
        }

        # Track which (day, slot) pairs belong to each group index
        # to enforce "different groups → different time slots"
        if not hasattr(self, '_pec_group_slot_usage'):
            self._pec_group_slot_usage = defaultdict(set)
        group_slot_usage = self._pec_group_slot_usage

        for group_idx, group in enumerate(groups):
            if not group:
                continue

            # Resolve courses + workloads for this group
            group_courses = []
            for cd in group:
                code = cd.get('code', '')
                course_obj = actual_courses.get(code)
                if not course_obj:
                    continue
                req = get_required_periods(course_obj, config.semester)
                faculty_ids = self._get_offering_faculty_for_course(
                    course_obj, config.semester
                )
                group_courses.append({
                    'course': course_obj,
                    'code': code,
                    'req': req,
                    'total': req['total'],
                    'faculty_ids': faculty_ids,
                })

            if not group_courses:
                continue

            group_courses.sort(key=lambda x: (-x['total'], x['code']))

            # Build display note base for this group.
            # We later refine each THEORY slot note so it lists only the
            # courses that actually share that specific slot.
            ordered_group_codes = [gc['code'] for gc in group_courses]
            group_note = '/'.join(ordered_group_codes)

            theory_courses = [gc for gc in group_courses if gc['req']['theory'] > 0]
            lab_courses = [gc for gc in group_courses if gc['req']['lab_sessions'] > 0]

            theory_anchor = None
            if theory_courses:
                theory_anchor = max(
                    theory_courses,
                    key=lambda gc: (gc['req']['theory'], gc['total'], gc['req']['lab_sessions'], gc['code'])
                )

            lab_anchor = None
            if lab_courses:
                lab_anchor = max(
                    lab_courses,
                    key=lambda gc: (gc['req']['lab_sessions'], gc['req']['lab_type'], gc['total'], gc['code'])
                )

            # ── Schedule lab anchor's LAB sessions first ──
            if not hasattr(self, '_pec_group_anchor_lab_slots'):
                self._pec_group_anchor_lab_slots = {}
            anchor_lab_slots_placed = list(self._pec_group_anchor_lab_slots.get(group_idx, []))
            if (
                schedule_labs
                and lab_anchor
                and lab_anchor['req']['lab_sessions'] > 0
                and (lab_type_filter is None or lab_anchor['req']['lab_type'] == lab_type_filter)
            ):
                lab_type = lab_anchor['req']['lab_type']
                lab_sessions_needed = lab_anchor['req']['lab_sessions']
                lab_anchor_faculty = set(lab_anchor['faculty_ids'])
                preferred_lab_slots = self._get_clubbed_lab_slots_for_course(lab_anchor['code'], lab_anchor_faculty)

                for _ in range(lab_sessions_needed):
                    placed = self._place_pec_group_lab(
                        batches, timetable_map, lab_anchor, lab_anchor_faculty,
                        group_slot_usage, group_idx, program,
                        lab_type, group_note,
                        preferred_slots=preferred_lab_slots,
                    )
                    if placed:
                        anchor_lab_slots_placed.append(placed)
                    else:
                        self.warnings.append(
                            f"Could not schedule {lab_type}-period lab for "
                            f"PEC group {group_idx + 1} anchor {lab_anchor['code']}"
                        )

            # ── Schedule theory anchor's THEORY periods ──
            self._pec_group_anchor_lab_slots[group_idx] = anchor_lab_slots_placed
            anchor_theory_slots = []  # [(day, slot_num)]
            theory_slot_courses = {}  # {(day, slot_num): {course_code, ...}}
            anchor_days_used = set()
            if schedule_theory and theory_anchor:
                theory_anchor_faculty = set(theory_anchor['faculty_ids'])
                theory_needed = theory_anchor['req']['theory']
                preferred_anchor_slots = self._get_clubbed_slots_for_course(theory_anchor['code'], theory_anchor_faculty)
                overlay_faculty_groups = [
                    set(gc['faculty_ids'])
                    for gc in theory_courses
                    if gc['code'] != theory_anchor['code'] and gc['faculty_ids']
                ]

                for _ in range(theory_needed):
                    placed = self._place_pec_group_theory(
                        batches, timetable_map, theory_anchor, theory_anchor_faculty,
                        group_slot_usage, group_idx, anchor_days_used, group_note,
                        preferred_slots=preferred_anchor_slots,
                        overlay_faculty_groups=overlay_faculty_groups,
                    )
                    if placed:
                        anchor_theory_slots.append(placed)
                        theory_slot_courses[placed] = {theory_anchor['code']}
                        anchor_days_used.add(placed[0])
                    else:
                        self.warnings.append(
                            f"Could not schedule theory for PEC group {group_idx + 1} "
                            f"anchor {theory_anchor['code']} "
                            f"({theory_needed - len(anchor_theory_slots)} periods remaining)"
                        )
                        break

            # ── Now overlay non-anchor theory courses on theory anchor's slots (best-effort) ──
            for other in ([gc for gc in theory_courses if not theory_anchor or gc['code'] != theory_anchor['code']] if schedule_theory else []):
                other_req = other['req']
                other_code = other['code']

                # Theory overlay: pick from anchor_theory_slots, up to other's theory need
                other_theory_needed = other_req['theory']
                other_theory_placed = 0
                for day, slot_num in anchor_theory_slots:
                    if other_theory_placed >= other_theory_needed:
                        break
                    # Overlay only if this course's faculty are actually free.
                    all_ok = True
                    for fid in other['faculty_ids']:
                        if not self._is_faculty_available(fid, day, slot_num):
                            all_ok = False
                            break
                    if not all_ok:
                        continue

                    for fid in other['faculty_ids']:
                        self._book_faculty(fid, day, slot_num)

                    theory_slot_courses.setdefault((day, slot_num), {theory_anchor['code']}).add(other_code)
                    other_theory_placed += 1

                if other_theory_placed < other_theory_needed:
                    remaining = other_theory_needed - other_theory_placed
                    self.warnings.append(
                        f"PEC group {group_idx + 1}: {other_code} has {remaining} "
                        f"theory period(s) that couldn't share anchor {theory_anchor['code']}'s slot — "
                        f"scheduling independently."
                    )

                    for _ in range(remaining):
                        placed = self._place_pec_independent_theory(
                            batches=batches,
                            timetable_map=timetable_map,
                            faculty_ids=other['faculty_ids'],
                            note_code=other_code,
                            group_slot_usage=group_slot_usage,
                            group_idx=group_idx,
                        )
                        if not placed:
                            self.warnings.append(
                                f"PEC group {group_idx + 1}: Could not independently schedule "
                                f"theory for {other_code}"
                            )
                            break

                # Lab overlay: if other course has labs, try to overlay on lab anchor's lab slots
            for other in ([gc for gc in lab_courses if not lab_anchor or gc['code'] != lab_anchor['code']] if schedule_labs else []):
                other_req = other['req']
                if other_req['lab_sessions'] > 0:
                    other_lab_type = other_req['lab_type']
                    other_lab_needed = other_req['lab_sessions']
                    other_lab_placed = 0

                    for lab_day, lab_slots, lab_room in anchor_lab_slots_placed:
                        if other_lab_placed >= other_lab_needed:
                            break

                        # Can only overlay if other's lab_type fits within anchor's slots
                        if other_lab_type > len(lab_slots):
                            continue

                        overlay_slots = lab_slots[:other_lab_type]

                        all_ok = True
                        for fid in other['faculty_ids']:
                            for s in overlay_slots:
                                if not self._is_faculty_available(fid, lab_day, s):
                                    all_ok = False
                                    break
                            if not all_ok:
                                break
                        if not all_ok:
                            continue

                        for fid in other['faculty_ids']:
                            for s in overlay_slots:
                                self._book_faculty(fid, lab_day, s)

                        other_lab_placed += 1

                    if other_lab_placed < other_lab_needed:
                        remaining = other_lab_needed - other_lab_placed
                        self.warnings.append(
                            f"PEC group {group_idx + 1}: {other_code} has {remaining} "
                            f"lab session(s) that couldn't share anchor's slot — "
                            f"will be scheduled independently."
                        )

            # Update theory slot labels to show only the courses that truly
            # share each period (e.g., anchor-only 4th period).
            for (slot_day, slot_num), slot_codes in (theory_slot_courses.items() if schedule_theory else []):
                ordered_slot_codes = [code for code in ordered_group_codes if code in slot_codes]
                if not ordered_slot_codes:
                    ordered_slot_codes = [theory_anchor['code']] if theory_anchor else [group_courses[0]['code']]
                slot_note = '/'.join(ordered_slot_codes)

                for batch in batches:
                    tt = timetable_map[batch.id]
                    TimetableEntry.objects.filter(
                        timetable=tt,
                        day=slot_day,
                        time_slot__slot_number=slot_num,
                        course__is_placeholder=True,
                    ).update(special_note=slot_note)

        # ── Mark PEC placeholders as handled in course_requirements_map ──
        # After PEC group scheduling, the PEC placeholder entries in
        # course_requirements_map should have their remaining counts zeroed
        # so Phase 2 doesn't try to schedule them again.
        for batch in batches:
            reqs = course_requirements_map.get(batch.id, [])
            for cr in reqs:
                course = cr['assignment'].course
                if (course.is_placeholder
                        and course.course_code.startswith('PEC')
                        and course.course_code in pec_placeholder_courses):
                    self._pec_group_handled_course_ids.add(course.pk)
                    if schedule_theory:
                        cr['theory_remaining'] = 0
                    if schedule_labs and lab_type_filter is None:
                        cr['lab_sessions_remaining'] = 0

    def _place_pec_group_theory(self, batches, timetable_map, anchor_info,
                                 anchor_faculty, group_slot_usage,
                                 group_idx, days_used, group_note,
                                 preferred_slots=None,
                                 overlay_faculty_groups=None):
        """
        Place ONE theory period for the PEC group anchor course across all batches.

        Constraints:
        - Slot must be free in ALL batch timetables
        - Anchor course faculty must be available
        - Slot must NOT be used by a DIFFERENT group
        - Prefer days not already used by this anchor (spread out)

        Returns (day, slot_num) on success, None on failure.
        Also creates TimetableEntry for the PEC placeholder in each batch.
        """
        candidate_slots = []
        seen = set()

        for item in preferred_slots or []:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                day, slot = item[0], item[1]
                candidate_slots.append((day, slot, True))
                seen.add((day, slot))

        day_order = DAYS.copy()
        day_order.sort(key=lambda d: d in days_used)
        for day in day_order:
            slot_order = self._ordered_theory_slots_for_faculty_ids(anchor_faculty)
            for ts in slot_order:
                if ts.is_break:
                    continue
                slot = ts.slot_number
                if (day, slot) in seen:
                    continue
                candidate_slots.append((day, slot, False))

        scored_slots = []
        for day, slot, is_preferred in candidate_slots:
            overlay_score = 0
            for faculty_group in overlay_faculty_groups or []:
                if all(self._is_faculty_available(fid, day, slot) for fid in faculty_group):
                    overlay_score += 1
            scored_slots.append((day, slot, is_preferred, overlay_score, day in days_used))

        scored_slots.sort(key=lambda item: (0 if item[2] else 1, -item[3], item[4]))

        for day, slot, _is_preferred, _overlay_score, _day_used in scored_slots:
            ts = next((slot_obj for slot_obj in self.time_slots if slot_obj.slot_number == slot), None)
            if not ts or ts.is_break:
                continue

            if self._slot_reserved_for_pending_club(day, slot, allowed_slots=preferred_slots):
                continue

            if self._is_blocked_by_me_lab_assist(day, [slot]):
                continue

            # Check: not used by a DIFFERENT group
            taken_by_other = False
            for other_gidx, used in group_slot_usage.items():
                if other_gidx != group_idx and (day, slot) in used:
                    taken_by_other = True
                    break
            if taken_by_other:
                continue

            # Check: free in ALL batch timetables
            all_free = True
            for batch in batches:
                tt = timetable_map[batch.id]
                if (day, slot) in self.occupied[tt.id]:
                    all_free = False
                    break
            if not all_free:
                continue

            # Check: anchor faculty available
            all_faculty_ok = True
            for fid in anchor_faculty:
                if not self._is_faculty_available(fid, day, slot):
                    all_faculty_ok = False
                    break
            if not all_faculty_ok:
                continue

            # ── Place it ──
            # Find which PEC placeholder to use for TimetableEntry
            # Prefer deterministic placeholder mapping by group index.
            pec_course = None
            pec_faculty = None
            placeholder_pool = getattr(self, '_pec_placeholder_courses', [])
            if placeholder_pool:
                pec_course = placeholder_pool[group_idx % len(placeholder_pool)]

            for batch in batches:
                for stc_course in placeholder_pool:
                    asgn = Course_Assignment.objects.filter(
                        academic_year=self.config.academic_year,
                        batch=batch,
                        course=stc_course,
                        is_active=True,
                    ).select_related('faculty').first()
                    if asgn:
                        pec_course = stc_course
                        pec_faculty = asgn.faculty
                        break
                if pec_course:
                    break

            if not pec_course:
                # Use anchor's course info as fallback
                pec_course = anchor_info['course']

            # Create entries for each batch
            for batch in batches:
                tt = timetable_map[batch.id]
                batch_faculty = pec_faculty
                if pec_course and pec_course.is_placeholder:
                    asgn = Course_Assignment.objects.filter(
                        academic_year=self.config.academic_year,
                        batch=batch,
                        course=pec_course,
                        is_active=True,
                    ).select_related('faculty').first()
                    if asgn:
                        batch_faculty = asgn.faculty

                TimetableEntry.objects.create(
                    timetable=tt,
                    day=day,
                    time_slot=ts,
                    course=pec_course,
                    faculty=batch_faculty,
                    is_lab=False,
                    special_note=group_note,
                )
                self.occupied[tt.id].add((day, slot))

            # Book anchor faculty
            for fid in anchor_faculty:
                self._book_faculty(fid, day, slot)

            group_slot_usage[group_idx].add((day, slot))
            return (day, slot)

        return None

    def _place_pec_independent_theory(self, batches, timetable_map,
                                      faculty_ids, note_code,
                                      group_slot_usage, group_idx):
        """
        Place one independent theory period for a non-anchor PEC course.
        Used when overlay on anchor slots is not possible.

        Returns (day, slot_num) on success, None otherwise.
        """
        day_order = DAYS.copy()

        for day in day_order:
            slot_order = self._ordered_theory_slots_for_faculty_ids(faculty_ids)

            for ts in slot_order:
                if ts.is_break:
                    continue
                slot = ts.slot_number

                if self._slot_reserved_for_pending_club(day, slot):
                    continue

                if self._is_blocked_by_me_lab_assist(day, [slot]):
                    continue

                # Keep group-occupied slots protected from OTHER groups,
                # but allow this group to place additional independent periods.
                taken_by_other = False
                for other_gidx, used in group_slot_usage.items():
                    if other_gidx != group_idx and (day, slot) in used:
                        taken_by_other = True
                        break
                if taken_by_other:
                    continue

                # Free in all batch timetables?
                all_free = True
                for batch in batches:
                    tt = timetable_map[batch.id]
                    if (day, slot) in self.occupied[tt.id]:
                        all_free = False
                        break
                if not all_free:
                    continue

                # Faculty available?
                all_faculty_ok = True
                for fid in faculty_ids:
                    if not self._is_faculty_available(fid, day, slot):
                        all_faculty_ok = False
                        break
                if not all_faculty_ok:
                    continue

                placeholder_pool = getattr(self, '_pec_placeholder_courses', [])
                pec_course = placeholder_pool[group_idx % len(placeholder_pool)] if placeholder_pool else None

                for batch in batches:
                    tt = timetable_map[batch.id]
                    batch_faculty = None
                    if pec_course and pec_course.is_placeholder:
                        asgn = Course_Assignment.objects.filter(
                            academic_year=self.config.academic_year,
                            batch=batch,
                            course=pec_course,
                            is_active=True,
                        ).select_related('faculty').first()
                        if asgn:
                            batch_faculty = asgn.faculty

                    TimetableEntry.objects.create(
                        timetable=tt,
                        day=day,
                        time_slot=ts,
                        course=pec_course,
                        faculty=batch_faculty,
                        is_lab=False,
                        special_note=note_code,
                    )
                    self.occupied[tt.id].add((day, slot))

                for fid in faculty_ids:
                    self._book_faculty(fid, day, slot)

                group_slot_usage[group_idx].add((day, slot))
                return (day, slot)

        return None

    def _place_pec_group_lab(self, batches, timetable_map, anchor_info,
                              anchor_faculty, group_slot_usage,
                              group_idx, program, lab_type, group_note,
                              preferred_slots=None):
        """
        Place ONE lab session for the PEC group anchor course across all batches.

        lab_type is 2 or 4 (number of consecutive periods).

        Returns (day, [slot_nums], lab_room) on success, None on failure.
        """
        timetable_ids = [
            timetable_map[batch.id].id
            for batch in batches
            if batch.id in timetable_map
        ]
        day_order = self._ordered_days_for_group_lab(timetable_ids, faculty_ids=anchor_faculty)

        if lab_type == 4:
            slot_options = list(LAB_SLOT_4_PERIOD)
        elif lab_type == 3:
            slot_options = self._get_consecutive_slot_options(3)
        else:
            slot_options = self._get_consecutive_slot_options(2)
        slot_options = self._order_group_lab_slot_options(
            timetable_ids,
            slot_options,
            prefer_odd_pairs=(lab_type == 2),
        )

        preferred_slot_options = []
        if preferred_slots:
            by_day = defaultdict(list)
            for item in preferred_slots:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    day, slot_num = item[0], item[1]
                    by_day[day].append(slot_num)
            for day, raw_slots in by_day.items():
                slots = sorted(set(raw_slots))
                run = []
                for slot_num in slots:
                    if not run or slot_num == run[-1] + 1:
                        run.append(slot_num)
                    else:
                        if len(run) >= lab_type:
                            preferred_slot_options.append((day, tuple(run[:lab_type])))
                        run = [slot_num]
                if len(run) >= lab_type:
                    preferred_slot_options.append((day, tuple(run[:lab_type])))

        for day in day_order:
            ordered_slot_tuples = []
            pref_for_day = [slot_tuple for pref_day, slot_tuple in preferred_slot_options if pref_day == day]
            if pref_for_day:
                ordered_slot_tuples.extend(pref_for_day)
            ordered_slot_tuples.extend([slot_tuple for slot_tuple in slot_options if slot_tuple not in ordered_slot_tuples])

            for slot_tuple in ordered_slot_tuples:
                slots = list(slot_tuple)

                if any(self._slot_reserved_for_pending_club(day, s) for s in slots):
                    continue

                if self._is_blocked_by_me_lab_assist(day, slots):
                    continue

                # Check: none of these slots used by a DIFFERENT group
                taken_by_other = False
                for other_gidx, used in group_slot_usage.items():
                    if other_gidx != group_idx:
                        for s in slots:
                            if (day, s) in used:
                                taken_by_other = True
                                break
                    if taken_by_other:
                        break
                if taken_by_other:
                    continue

                # Check: free in ALL batch timetables
                all_free = True
                for batch in batches:
                    tt = timetable_map[batch.id]
                    if self._slots_reserved_for_imported_clubbed_slot(tt.id, day, slots):
                        all_free = False
                        break
                    for s in slots:
                        if (day, s) in self.occupied[tt.id]:
                            all_free = False
                            break
                    if not all_free:
                        break
                if not all_free:
                    continue

                # Check: anchor faculty available for all slots
                all_faculty_ok = True
                for fid in anchor_faculty:
                    for s in slots:
                        if not self._is_faculty_available(fid, day, s):
                            all_faculty_ok = False
                            break
                    if not all_faculty_ok:
                        break
                if not all_faculty_ok:
                    continue

                # For PEC electives, number of parallel physical labs should follow
                # the elective offering's batch_count (not total class batches).
                # Example: if DevOps has batch_count=1, all class batches share one lab.
                offering_batch_count = ElectiveCourseOffering.objects.filter(
                    semester=self.config.semester,
                    actual_course=anchor_info['course'],
                    regulation_course_plan__branch=program.code,
                    regulation_course_plan__program_type=program.level,
                    is_active=True,
                ).values_list('batch_count', flat=True).first() or 1

                parallel_labs_needed = max(1, min(int(offering_batch_count), len(batches)))

                chosen_labs = []
                temp_reserved = []  # (lab, slots) reservations to rollback on failure
                allocation_failed = False

                # Choose only as many distinct labs as needed for parallel elective batches.
                for _ in range(parallel_labs_needed):
                    year_of_study = self.config.year_of_study
                    if lab_type == 4:
                        lab = self._get_available_lab_4p(
                            day, tuple(slots), program, year_of_study,
                            anchor_info['course']
                        )
                    elif lab_type == 3:
                        lab = self._get_available_lab_3p(
                            day, tuple(slots), program, year_of_study,
                            anchor_info['course']
                        )
                    else:
                        lab = self._get_available_lab_2p(
                            day, tuple(slots), program, year_of_study,
                            anchor_info['course']
                        )

                    if lab is None:
                        allocation_failed = True
                        break

                    for s in slots:
                        self.lab_schedule_slots[(day, s)][lab.id] = '__TEMP__'
                    temp_reserved.append((lab, list(slots)))
                    chosen_labs.append(lab)

                if allocation_failed or not chosen_labs:
                    for lab, reserved_slots in temp_reserved:
                        for s in reserved_slots:
                            self.lab_schedule_slots[(day, s)][lab.id] = None
                    continue

                # Map each class batch to one of the chosen labs.
                # If only one elective batch exists, every class batch uses same lab.
                batch_lab_allocations = []
                for idx, batch in enumerate(batches):
                    batch_lab_allocations.append((batch, chosen_labs[idx % len(chosen_labs)]))

                # ── Place it ──
                # Find PEC placeholder course for timetable entries
                pec_course = None
                placeholder_pool = getattr(self, '_pec_placeholder_courses', [])
                if placeholder_pool:
                    pec_course = placeholder_pool[group_idx % len(placeholder_pool)]
                if not pec_course:
                    pec_course = anchor_info['course']

                for batch, batch_lab in batch_lab_allocations:
                    tt = timetable_map[batch.id]
                    batch_faculty = None
                    if pec_course and pec_course.is_placeholder:
                        asgn = Course_Assignment.objects.filter(
                            academic_year=self.config.academic_year,
                            batch=batch,
                            course=pec_course,
                            is_active=True,
                        ).select_related('faculty').first()
                        if asgn:
                            batch_faculty = asgn.faculty

                    for i, slot_num in enumerate(slots):
                        ts_obj = TimeSlot.objects.get(slot_number=slot_num)
                        note_parts = [anchor_info['code'], batch_lab.room_code]
                        if lab_type == 4:
                            session_label = "Morning" if tuple(slots) == [1, 2, 3, 4] else "Afternoon"
                            if i == 0:
                                note_parts.append(f"({session_label})")
                            elif i == len(slots) - 1:
                                note_parts.append("(End)")
                        note = ' '.join(note_parts)

                        TimetableEntry.objects.create(
                            timetable=tt,
                            day=day,
                            time_slot=ts_obj,
                            course=pec_course,
                            faculty=batch_faculty,
                            is_lab=True,
                            lab_room=batch_lab,
                            special_note=note,
                        )
                        self.occupied[tt.id].add((day, slot_num))

                    self._record_lab_workload(tt.id, day, slots)

                self._record_be_lab_slots_for_course(anchor_info['course'], day, slots)

                # Convert temporary reservations into final bookings for each chosen lab.
                for batch_lab in chosen_labs:
                    if lab_type == 4:
                        self._book_lab_4p(day, tuple(slots), batch_lab, 'PEC')
                    elif lab_type == 3:
                        self._book_lab_3p(day, tuple(slots), batch_lab, 'PEC')
                    else:
                        self._book_lab_2p(day, tuple(slots), batch_lab, 'PEC')

                # Book anchor faculty for all slots
                for fid in anchor_faculty:
                    for s in slots:
                        self._book_faculty(fid, day, s)

                self._record_lab_session_for_faculty_ids(anchor_faculty, day, slots)

                for s in slots:
                    group_slot_usage[group_idx].add((day, s))

                first_lab = batch_lab_allocations[0][1] if batch_lab_allocations else None
                return (day, slots, first_lab)

        return None

    # ─── Schedule theory ─────────────────────────────────────────

    def _estimate_theory_flexibility(self, timetable, course_req):
        assignment = course_req['assignment']

        feasible_count = 0
        for day in DAYS:
            for ts in self.time_slots:
                if ts.is_break:
                    continue

                slot = ts.slot_number
                if (day, slot) in self.occupied[timetable.id]:
                    continue
                if self._is_blocked_by_me_lab_assist(day, [slot]):
                    continue
                if not self._is_faculty_available(assignment.faculty.id, day, slot):
                    continue

                feasible_count += 1

        return feasible_count

    def _get_existing_theory_days(self, timetable, course):
        return set(
            TimetableEntry.objects.filter(
                timetable=timetable,
                course=course,
                is_lab=False,
            ).values_list('day', flat=True)
        )

    def _get_existing_theory_slots_by_day(self, timetable, course):
        by_day = defaultdict(set)
        for day, slot_num in TimetableEntry.objects.filter(
            timetable=timetable,
            course=course,
            is_lab=False,
        ).values_list('day', 'time_slot__slot_number'):
            by_day[day].add(slot_num)
        return by_day

    def _get_existing_faculty_slots_by_day(self, timetable, faculty_id):
        by_day = defaultdict(set)
        for day, slot_num in TimetableEntry.objects.filter(
            timetable=timetable,
            faculty_id=faculty_id,
        ).values_list('day', 'time_slot__slot_number'):
            by_day[day].add(slot_num)
        return by_day

    def _same_class_short_gap_penalty(self, faculty_slots_by_day, day, candidate_slots):
        existing_slots = sorted(faculty_slots_by_day.get(day, set()))
        if not existing_slots:
            return 0

        for existing_slot in existing_slots:
            for candidate_slot in candidate_slots:
                if self._same_halfday(existing_slot, candidate_slot) and abs(existing_slot - candidate_slot) <= 2:
                    return 1
        return 0

    def _same_course_short_gap_penalty(self, course_slots_by_day, day, candidate_slots):
        existing_slots = sorted(course_slots_by_day.get(day, set()))
        if not existing_slots:
            return 0

        for existing_slot in existing_slots:
            for candidate_slot in candidate_slots:
                if self._same_halfday(existing_slot, candidate_slot) and abs(existing_slot - candidate_slot) <= 2:
                    return 1
        return 0

    def _theory_candidate_allowed(self, timetable, assignment, day, candidate_slots, course_slots_by_day, faculty_slots_by_day, strict_spacing):
        if self._is_blocked_by_me_lab_assist(day, candidate_slots):
            return False

        for slot in candidate_slots:
            if (day, slot) in self.occupied[timetable.id]:
                return False
            if not self._is_faculty_available(assignment.faculty.id, day, slot):
                return False

        class_gap_penalty = self._same_class_short_gap_penalty(
            faculty_slots_by_day,
            day,
            candidate_slots,
        )
        course_gap_penalty = self._same_course_short_gap_penalty(
            course_slots_by_day,
            day,
            candidate_slots,
        )

        if strict_spacing and (class_gap_penalty or course_gap_penalty):
            return False

        if strict_spacing and self._has_long_lab_day(assignment.faculty.id, day):
            day_load = self.faculty_day_load[assignment.faculty.id].get(day, 0)
            if day_load + len(candidate_slots) > 5:
                return False

        return True

    def _theory_candidate_score(self, assignment, day, candidate_slots, course_days, course_slots_by_day, faculty_slots_by_day):
        faculty_id = assignment.faculty.id
        day_load = self.faculty_day_load[faculty_id].get(day, 0)
        class_gap_penalty = self._same_class_short_gap_penalty(faculty_slots_by_day, day, candidate_slots)
        course_gap_penalty = self._same_course_short_gap_penalty(course_slots_by_day, day, candidate_slots)
        day_spread_penalty = self._faculty_day_load_spread_penalty(faculty_id, day)

        long_lab_overflow_penalty = 0
        if self._has_long_lab_day(faculty_id, day):
            projected_load = day_load + len(candidate_slots)
            long_lab_overflow_penalty = max(0, projected_load - 5)

        edge_penalty = 0
        if self.prefer_avoid_professor_edges and self._is_professor_id(faculty_id):
            edge_penalty = 1 if any(self._is_slot_edge_period(slot) for slot in candidate_slots) else 0

        return (
            class_gap_penalty,
            course_gap_penalty,
            long_lab_overflow_penalty,
            0 if day not in course_days else 1,
            day_spread_penalty,
            day_load,
            edge_penalty,
            candidate_slots[0],
        )

    def _find_best_theory_single_slot(self, timetable, course_req, course_days, course_slots_by_day, faculty_slots_by_day, strict_spacing):
        assignment = course_req['assignment']
        slot_order = self._ordered_theory_slots_for_faculty_ids([assignment.faculty.id])
        candidates = []

        for day in DAYS:
            for ts in slot_order:
                slot = ts.slot_number
                candidate_slots = [slot]
                if not self._theory_candidate_allowed(
                    timetable,
                    assignment,
                    day,
                    candidate_slots,
                    course_slots_by_day,
                    faculty_slots_by_day,
                    strict_spacing,
                ):
                    continue

                score = self._theory_candidate_score(
                    assignment,
                    day,
                    candidate_slots,
                    course_days,
                    course_slots_by_day,
                    faculty_slots_by_day,
                )
                candidates.append((score, day, slot))

        if not candidates:
            return None

        candidates.sort(key=lambda item: item[0])
        return candidates[0][1], candidates[0][2]

    def _place_theory_slots(self, timetable, assignment, day, slots, course_slots_by_day=None, faculty_slots_by_day=None):
        for slot in slots:
            ts = TimeSlot.objects.get(slot_number=slot)
            TimetableEntry.objects.create(
                timetable=timetable,
                day=day,
                time_slot=ts,
                course=assignment.course,
                faculty=assignment.faculty,
                is_lab=False,
            )
            self._book_faculty(assignment.faculty.id, day, slot)
            self.occupied[timetable.id].add((day, slot))
            if course_slots_by_day is not None:
                course_slots_by_day[day].add(slot)
            if faculty_slots_by_day is not None:
                faculty_slots_by_day[day].add(slot)

    def _find_preferred_theory_pair(self, timetable, course_req, course_days, course_slots_by_day, faculty_slots_by_day, strict_spacing):
        if course_req['theory_remaining'] < 2:
            return None

        assignment = course_req['assignment']

        pair_candidates = []
        for day in DAYS:
            for slot_pair in self._get_consecutive_slot_options(2):
                candidate_slots = list(slot_pair)
                if not self._theory_candidate_allowed(
                    timetable,
                    assignment,
                    day,
                    candidate_slots,
                    course_slots_by_day,
                    faculty_slots_by_day,
                    strict_spacing,
                ):
                    continue

                score = self._theory_candidate_score(
                    assignment,
                    day,
                    candidate_slots,
                    course_days,
                    course_slots_by_day,
                    faculty_slots_by_day,
                )
                pair_candidates.append((score, day, tuple(slot_pair)))

        if not pair_candidates:
            return None

        pair_candidates.sort(key=lambda item: item[0])
        return pair_candidates[0][1], pair_candidates[0][2]

    def _schedule_next_theory_period(self, timetable, course_req, course_days, course_slots_by_day, faculty_slots_by_day):
        assignment = course_req['assignment']

        # Prefer single-period placement first; consecutive theory is fallback only.
        for strict_spacing in (True, False):
            best_single = self._find_best_theory_single_slot(
                timetable,
                course_req,
                course_days,
                course_slots_by_day,
                faculty_slots_by_day,
                strict_spacing,
            )
            if best_single:
                day, slot = best_single
                self._place_theory_slots(
                    timetable,
                    assignment,
                    day,
                    [slot],
                    course_slots_by_day=course_slots_by_day,
                    faculty_slots_by_day=faculty_slots_by_day,
                )
                course_req['theory_remaining'] -= 1
                course_days.add(day)
                return True

        for strict_spacing in (True, False):
            preferred_pair = self._find_preferred_theory_pair(
                timetable,
                course_req,
                course_days,
                course_slots_by_day,
                faculty_slots_by_day,
                strict_spacing,
            )
            if preferred_pair:
                day, slot_pair = preferred_pair
                self._place_theory_slots(
                    timetable,
                    assignment,
                    day,
                    slot_pair,
                    course_slots_by_day=course_slots_by_day,
                    faculty_slots_by_day=faculty_slots_by_day,
                )
                course_req['theory_remaining'] -= len(slot_pair)
                course_days.add(day)
                return True

        return False

    def _schedule_theory(self, timetable, course_requirements, batch):
        theory_courses = [c for c in course_requirements if c['theory_remaining'] > 0]
        if not theory_courses:
            return

        for course_req in theory_courses:
            assignment = course_req['assignment']
            course_days = self._get_existing_theory_days(timetable, assignment.course)
            course_slots_by_day = self._get_existing_theory_slots_by_day(timetable, assignment.course)
            faculty_slots_by_day = self._get_existing_faculty_slots_by_day(timetable, assignment.faculty.id)

            while course_req['theory_remaining'] > 0:
                if not self._schedule_next_theory_period(
                    timetable,
                    course_req,
                    course_days,
                    course_slots_by_day,
                    faculty_slots_by_day,
                ):
                    self.warnings.append(
                        f"Could not schedule theory for {assignment.course.course_code} "
                        f"(batch {batch.batch_name}, {course_req['theory_remaining']} periods remaining)"
                    )
                    break

    def _schedule_theory_globally(self, batch_list, timetable_map, course_requirements_map):
        course_days_map = {}
        course_slots_by_day_map = {}
        faculty_slots_by_day_map = {}

        while True:
            requests = []
            for batch in batch_list:
                timetable = timetable_map[batch.id]
                for course_req in course_requirements_map.get(batch.id, []):
                    if course_req['theory_remaining'] <= 0:
                        continue

                    req_key = id(course_req)
                    if req_key not in course_days_map:
                        course_days_map[req_key] = self._get_existing_theory_days(
                            timetable,
                            course_req['assignment'].course,
                        )
                        course_slots_by_day_map[req_key] = self._get_existing_theory_slots_by_day(
                            timetable,
                            course_req['assignment'].course,
                        )
                        faculty_slots_by_day_map[req_key] = self._get_existing_faculty_slots_by_day(
                            timetable,
                            course_req['assignment'].faculty.id,
                        )

                    requests.append((batch, timetable, course_req, req_key))

            if not requests:
                break

            requests.sort(
                key=lambda item: (
                    self._estimate_theory_flexibility(item[1], item[2]),
                    -item[2]['theory_remaining'],
                    len(course_days_map[item[3]]),
                    item[0].batch_name,
                    item[2]['assignment'].course.course_code,
                )
            )

            batch, timetable, course_req, req_key = requests[0]
            if self._schedule_next_theory_period(
                timetable,
                course_req,
                course_days_map[req_key],
                course_slots_by_day_map[req_key],
                faculty_slots_by_day_map[req_key],
            ):
                continue

            assignment = course_req['assignment']
            self.warnings.append(
                f"Could not schedule theory for {assignment.course.course_code} "
                f"(batch {batch.batch_name}, {course_req['theory_remaining']} periods remaining)"
            )
            course_req['theory_remaining'] = 0

    def _get_placeholder_offerings(self, placeholder_course):
        """Return active offerings for a placeholder course in current config semester."""
        rcp_ids = RegulationCoursePlan.objects.filter(
            course=placeholder_course,
        ).values_list('id', flat=True)
        if not rcp_ids:
            return ElectiveCourseOffering.objects.none()

        return ElectiveCourseOffering.objects.filter(
            regulation_course_plan_id__in=rcp_ids,
            semester=self.config.semester,
            is_active=True,
        ).select_related('actual_course').order_by('actual_course__course_code')

    def _validate_pec_rules(self):
        """
        Validate PEC setup before generation.
        - Warn (not block) on mixed workloads inside a PEC group.
        - Check PECGroupConfig exists when PEC placeholders are present.
        Returns list of error strings (hard blockers only).
        """
        errors = []

        pec_slots = list(
            SameTimeConstraint.objects.filter(
                config=self.config,
                course__is_placeholder=True,
                course__course_code__startswith='PEC',
            ).select_related('course').values_list('course_id', flat=True)
        )

        if not pec_slots:
            return errors

        # PEC group scheduling is now handled by _schedule_pec_groups
        # which reads PECGroupConfig.  No hard errors needed here for
        # mixed workloads — the engine handles differential scheduling.

        return errors

    # ─── Count already-reserved periods per course ───────────────

    @staticmethod
    def _count_reserved_for_course(reservations, course_code):
        """Count how many reservation slots already cover a given course."""
        return sum(1 for r in reservations
                   if not r.is_blocked and r.course and r.course.course_code == course_code)

    # ─── Main generation entry point ─────────────────────────────

    def _mark_pec_lab_requirements_handled(self):
        for reqs in self._course_requirements_map.values():
            for cr in reqs:
                course = cr['assignment'].course
                if course and course.is_placeholder and course.course_code.startswith('PEC'):
                    cr['lab_sessions_remaining'] = 0

    def _schedule_lab_phase_for_type(self, lab_type):
        batch_list = self._batch_list
        timetable_map = self._timetable_map
        course_requirements_map = self._course_requirements_map
        program = self.config.program

        self._schedule_pec_groups(
            batch_list,
            timetable_map,
            course_requirements_map,
            program,
            schedule_theory=False,
            schedule_labs=True,
            lab_type_filter=lab_type,
        )
        self._schedule_clubbed_courses(
            batch_list,
            timetable_map,
            course_requirements_map,
            place_theory=False,
            place_labs=True,
            lab_type_filter=lab_type,
        )
        self._schedule_lab_type_globally(
            batch_list,
            timetable_map,
            course_requirements_map,
            program,
            lab_type,
        )

    def _run_theory_phase(self):
        batch_list = self._batch_list
        timetable_map = self._timetable_map
        course_requirements_map = self._course_requirements_map
        program = self.config.program

        self._rebuild_pending_clubbed_slot_set()
        self._refresh_external_commitments()

        self._schedule_pec_groups(
            batch_list,
            timetable_map,
            course_requirements_map,
            program,
            schedule_theory=True,
            schedule_labs=False,
        )
        self._schedule_clubbed_courses(
            batch_list,
            timetable_map,
            course_requirements_map,
            place_theory=True,
            place_labs=False,
        )
        self._schedule_same_time_courses(
            batch_list,
            timetable_map,
            course_requirements_map,
            program,
        )

        self._schedule_theory_globally(
            batch_list,
            timetable_map,
            course_requirements_map,
        )

    def _finalize_generation(self):
        self._timetables_created = []
        for batch in self._batch_list:
            timetable = self._timetable_map[batch.id]
            self._timetables_created.append({
                'id': timetable.id,
                'batch_name': batch.batch_name,
                'program_code': self.config.program.code,
                'year': self.config.year_of_study,
                'entries_count': timetable.entries.count(),
            })

        self.config.is_generated = True
        self.config.save()
        return self._timetables_created

    def generate(self, effective_date=None):
        """
        Run full generation:
        1. Copy reserved/blocked slots into TimetableEntry.
        2. Auto-fill remaining slots for each batch.
        Returns dict with results and warnings.
        """
        if effective_date is None:
            effective_date = date.today()

        with transaction.atomic():
            prepared = self._prepare_generation(effective_date)
            if not prepared.get('success'):
                return prepared

            for lab_type in (4, 3, 2):
                self._schedule_lab_phase_for_type(lab_type)
            self._mark_pec_lab_requirements_handled()

            self._run_theory_phase()
            timetables_created = self._finalize_generation()

        return {
            'success': True,
            'timetables': timetables_created,
            'warnings': self._filter_public_warnings(self.warnings),
        }

        config = self.config
        program = config.program

        batches = ProgramBatch.objects.filter(
            academic_year=config.academic_year,
            program=program,
            year_of_study=config.year_of_study,
            is_active=True,
        )

        if not batches.exists():
            return {'success': False, 'error': 'No batches found', 'timetables': [], 'warnings': []}

        pec_errors = self._validate_pec_rules()
        if pec_errors:
            return {
                'success': False,
                'error': 'PEC configuration validation failed',
                'timetables': [],
                'warnings': pec_errors,
            }

        timetables_created = []

        with transaction.atomic():
            # ── Phase 0: Create all timetables, copy reservations, build requirements ──
            timetable_map = {}            # batch_id -> Timetable
            course_requirements_map = {}  # batch_id -> [course_reqs]
            batch_list = list(batches)

            elective_actual_course_codes = set(
                ElectiveCourseOffering.objects.filter(
                    semester=config.semester,
                    regulation_course_plan__branch=program.code,
                    regulation_course_plan__program_type=program.level,
                    is_active=True,
                ).values_list('actual_course__course_code', flat=True)
            )

            for batch in batch_list:
                # Create or reset timetable record
                timetable, created = Timetable.objects.update_or_create(
                    academic_year=config.academic_year,
                    semester=config.semester,
                    year=config.year_of_study,
                    program_batch=batch,
                    defaults={
                        'batch': batch.batch_name,
                        'effective_from': effective_date,
                        'created_by': config.created_by,
                        'is_active': True,
                    },
                )
                if not created:
                    timetable.entries.all().delete()

                timetable_map[batch.id] = timetable

                # ── Phase 1: Copy fixed reservations ──
                reservations = list(
                    FixedSlotReservation.objects.filter(
                        config=config, batch=batch,
                    ).select_related('course', 'faculty', 'time_slot')
                )

                for res in reservations:
                    TimetableEntry.objects.create(
                        timetable=timetable,
                        day=res.day,
                        time_slot=res.time_slot,
                        course=res.course if not res.is_blocked else None,
                        faculty=res.faculty if not res.is_blocked else None,
                        special_note=res.special_note if not res.is_blocked else res.block_reason,
                        is_blocked=res.is_blocked,
                        block_reason=res.block_reason if res.is_blocked else None,
                    )

                # Seed tracking from reservations
                self._seed_from_reservations(timetable, batch, reservations)

                # Build course requirements strictly by explicit batch mapping
                assignments = Course_Assignment.objects.filter(
                    academic_year=config.academic_year,
                    batch=batch,
                    semester=config.semester,
                    is_active=True,
                ).exclude(
                    course__course_code__in=elective_actual_course_codes
                ).select_related('course', 'faculty', 'lab_assistant', 'lab_main_faculty')

                course_requirements = []
                for asgn in assignments:
                    req = get_required_periods(asgn.course)
                    already_reserved = self._count_reserved_for_course(
                        reservations, asgn.course.course_code
                    )

                    # Subtract already-reserved theory / lab periods
                    theory_remaining = max(0, req['theory'] - already_reserved)
                    lab_remaining = req['lab_sessions']
                    # If course is lab type and some periods already reserved,
                    # assume each lab_type-worth of reserved slots is one session
                    if req['lab_type'] > 0 and already_reserved > 0:
                        lab_used = already_reserved // req['lab_type']
                        lab_remaining = max(0, req['lab_sessions'] - lab_used)
                        # Leftover reserved slots that didn't make a full lab session
                        leftover = already_reserved - lab_used * req['lab_type']
                        theory_remaining = max(0, req['theory'] - leftover)

                    course_requirements.append({
                        'assignment': asgn,
                        'theory_remaining': theory_remaining,
                        'lab_sessions_remaining': lab_remaining,
                        'lab_type': req['lab_type'],
                        'is_lab_course': asgn.course.course_type in ['L', 'LIT'],
                    })

                course_requirements_map[batch.id] = course_requirements

            pending_keys = {
                key
                for reqs in course_requirements_map.values()
                for cr in reqs
                for key in [self._clubbing_key_for_assignment(cr['assignment'])]
                if key and key in self.clubbed_slots
            }
            self.pending_clubbed_slot_set = set()
            for key in pending_keys:
                payload = self.clubbed_slots.get(key, {})
                if isinstance(payload, dict):
                    self.pending_clubbed_slot_set.update(self._to_day_slot_pairs(payload.get('theory', [])))
                    self.pending_clubbed_slot_set.update(self._to_day_slot_pairs(payload.get('lab', [])))
                else:
                    self.pending_clubbed_slot_set.update(self._to_day_slot_pairs(payload))

            # ── Phase 1.5: Schedule PEC groups (group-aware differential scheduling) ──
            self._schedule_pec_groups(
                batch_list, timetable_map, course_requirements_map, program
            )

            # ── Phase 1.6: Schedule clubbed PG courses ──
            # Reuse slots from previously generated clubbed programs first,
            # so local same-time rules adapt around those fixed positions.
            self._schedule_clubbed_courses(
                batch_list, timetable_map, course_requirements_map
            )

            # ── Phase 1.7: Schedule same-time courses across ALL batches ──
            # (PEC placeholders already handled by Phase 1.5 are skipped)
            self._schedule_same_time_courses(
                batch_list, timetable_map, course_requirements_map, program
            )

            # ── Phase 2: Global lab-first strategy across all batches ──
            # 2A. Schedule labs for all batches first (no theory yet), so theory
            # does not consume scarce windows needed by labs in other batches.
            # Prioritize hardest lab batches first by estimated feasibility.
            def _batch_lab_priority(b):
                tt = timetable_map[b.id]
                reqs = course_requirements_map[b.id]

                total_pending_sessions = 0
                pending_4p_sessions = 0
                flexibility_score = 0

                for cr in reqs:
                    if not cr['is_lab_course'] or cr['lab_sessions_remaining'] <= 0:
                        continue

                    sessions = cr['lab_sessions_remaining']
                    total_pending_sessions += sessions
                    if cr['lab_type'] == 4:
                        pending_4p_sessions += sessions

                    est = self._estimate_lab_flexibility(
                        tt, cr, b, program, cr['lab_type']
                    )
                    flexibility_score += max(1, est) * sessions

                # Lower flexibility score means harder batch; prioritize first.
                # Then prioritize more 4-period sessions, then total sessions.
                return (
                    flexibility_score,
                    -pending_4p_sessions,
                    -total_pending_sessions,
                    b.batch_name,
                )

            batches_for_labs = sorted(batch_list, key=_batch_lab_priority)
            for batch in batches_for_labs:
                timetable = timetable_map[batch.id]
                course_requirements = course_requirements_map[batch.id]
                self._schedule_labs(timetable, course_requirements, batch, program)

            # 2B. After all labs are placed, fill theory for all batches.
            for batch in batch_list:
                timetable = timetable_map[batch.id]
                course_requirements = course_requirements_map[batch.id]
                self._schedule_theory(timetable, course_requirements, batch)

                timetables_created.append({
                    'id': timetable.id,
                    'batch_name': batch.batch_name,
                    'program_code': program.code,
                    'year': config.year_of_study,
                    'entries_count': timetable.entries.count(),
                })

            # Mark config as generated
            config.is_generated = True
            config.save()

        return {
            'success': True,
            'timetables': timetables_created,
            'warnings': self._filter_public_warnings(self.warnings),
        }

    # ─── Preview (dry-run) ───────────────────────────────────────

    def preview(self):
        """
        Analyse what the generation would produce without writing to DB.
        Returns course requirements, lab availability, and potential warnings.
        """
        config = self.config
        program = config.program

        batches = ProgramBatch.objects.filter(
            academic_year=config.academic_year,
            program=program,
            year_of_study=config.year_of_study,
            is_active=True,
        )

        result = {
            'batches': [],
            'total_labs_available': self.num_labs,
            'lab_names': [l.room_code for l in self.labs],
        }

        for batch in batches:
            reservations = FixedSlotReservation.objects.filter(
                config=config, batch=batch,
            )
            reserved_count = reservations.filter(is_blocked=False).count()
            blocked_count = reservations.filter(is_blocked=True).count()

            assignments = Course_Assignment.objects.filter(
                academic_year=config.academic_year,
                batch=batch,
                semester=config.semester,
                is_active=True,
            ).select_related('course')

            total_needed = 0
            for asgn in assignments:
                req = get_required_periods(asgn.course)
                total_needed += req['total']

            total_slots = len(DAYS) * NUM_PERIODS  # 40 per batch
            remaining = total_slots - reserved_count - blocked_count

            result['batches'].append({
                'batch_name': batch.batch_name,
                'batch_id': batch.id,
                'reserved_count': reserved_count,
                'blocked_count': blocked_count,
                'remaining_slots': remaining,
                'total_periods_needed': total_needed,
                'courses_count': assignments.count(),
            })

        return result

    # ─── Multi-config generation (all programs at once) ───────

    @staticmethod
    def generate_all(configs, created_by=None, generation_preferences=None):
        """
        Generate timetables for multiple TimetableConfigs at once.
        
        1. Collects ALL batch IDs across all configs.
        2. Excludes them from existing-faculty-commitment loading.
        3. Generates configs sequentially; each subsequent config sees
           the faculty bookings from previously generated configs
           because they share the engine's faculty_schedule (via DB).
        
        Args:
            configs: QuerySet or list of TimetableConfig objects
            created_by: Account_User for created_by field
        
        Returns:
            dict with overall results, per-config breakdown, and warnings.
        """
        configs = list(configs)
        if not configs:
            return {'success': False, 'error': 'No configs provided', 'results': []}

        # Prioritize B.E. programs so BE labs are placed first.
        def _config_priority(cfg):
            if cfg.program.degree == 'BE':
                return 0
            if cfg.program.level == 'UG':
                return 1
            return 2

        configs.sort(key=lambda cfg: (_config_priority(cfg), cfg.program.code, cfg.year_of_study))

        # Collect ALL batch IDs that will be (re)generated
        all_batch_ids = set()
        for cfg in configs:
            batch_ids = TimetableEngine._resolve_batches_for_config(cfg).values_list('id', flat=True)
            all_batch_ids.update(batch_ids)

        all_results = []
        all_warnings = []

        # ── Pre-load all active ClubbedCourseGroups ──
        # Build a lookup: (course_code, faculty_id) → group for quick matching
        # This persists across configs so clubbed slots can be shared.
        clubbed_lookup = {}  # (course_code, faculty_id) → ClubbedCourseGroup
        all_academic_years = {cfg.academic_year_id for cfg in configs}
        all_semesters = {cfg.semester_id for cfg in configs}
        all_semester_types = {cfg.semester.semester_type for cfg in configs}

        clubbed_groups = ClubbedCourseGroup.objects.filter(
            academic_year_id__in=all_academic_years,
            semester_id__in=all_semesters,
            is_active=True,
        ).select_related('course', 'faculty').prefetch_related('members')

        for grp in clubbed_groups:
            key = (grp.course.course_code, grp.faculty_id)
            clubbed_lookup[key] = grp

        # Accumulated clubbed slot placements passed to subsequent engines.
        # { (course_code, faculty_id): [(day, slot_num), ...] }
        accumulated_clubbed_slots = {}

        # Accumulated lab occupancy passed to subsequent engines.
        # set((day, slot_num, lab_id), ...)
        accumulated_lab_occupancy = set()

        # Shared BE lab slot map used by ME assist blocking.
        # {course_code: {(day, slot_num), ...}}
        accumulated_be_lab_slots_by_course = defaultdict(set)

        target_sem_numbers = set()
        for sem_type in all_semester_types:
            target_sem_numbers.update(TimetableEngine._semester_numbers_for_type(sem_type))

        mapped_be_lab_codes = set(
            MELabAssistConstraint.objects.filter(
                academic_year_id__in=all_academic_years,
                semester_type__in=all_semester_types,
            ).values_list('be_lab_course__course_code', flat=True)
        )

        if mapped_be_lab_codes and target_sem_numbers:
            existing_be_lab_rows = TimetableEntry.objects.filter(
                timetable__is_active=True,
                timetable__academic_year_id__in=all_academic_years,
                timetable__semester__semester_number__in=target_sem_numbers,
                timetable__program_batch__program__degree='BE',
                is_lab=True,
                course__course_code__in=mapped_be_lab_codes,
            ).exclude(
                timetable__program_batch_id__in=all_batch_ids,
            ).values_list('course__course_code', 'day', 'time_slot__slot_number')

            for course_code, day, slot_num in existing_be_lab_rows:
                accumulated_be_lab_slots_by_course[course_code].add((day, slot_num))

        with transaction.atomic():
            def _clubbed_slot_snapshot():
                return {
                    key: {
                        'theory': sorted(payload.get('theory', set())),
                        'lab': sorted(payload.get('lab', set())),
                    }
                    for key, payload in accumulated_clubbed_slots.items()
                }

            def _collect_cfg_slot_payload(cfg, include_theory=True, include_labs=True):
                cfg_batch_ids = list(
                    TimetableEngine._resolve_batches_for_config(cfg).values_list('id', flat=True)
                )
                if not cfg_batch_ids:
                    return

                cfg_assignments = list(
                    Course_Assignment.objects.filter(
                        academic_year=cfg.academic_year,
                        semester=cfg.semester,
                        batch_id__in=cfg_batch_ids,
                        is_active=True,
                        faculty_id__isnull=False,
                    ).select_related('course')
                )

                if include_labs:
                    new_lab_slots = TimetableEntry.objects.filter(
                        timetable__program_batch_id__in=cfg_batch_ids,
                        timetable__is_active=True,
                        lab_room__isnull=False,
                        is_lab=True,
                    ).values_list('day', 'time_slot__slot_number', 'lab_room_id')
                    for day, slot_num, lab_id in new_lab_slots:
                        accumulated_lab_occupancy.add((day, slot_num, lab_id))

                candidate_entries = list(
                    TimetableEntry.objects.filter(
                        timetable__program_batch_id__in=cfg_batch_ids,
                        timetable__is_active=True,
                    ).values_list(
                        'day',
                        'time_slot__slot_number',
                        'course__course_code',
                        'special_note',
                        'is_lab',
                        'lab_room_id',
                    )
                )

                for key, grp in clubbed_lookup.items():
                    member_batch_ids = set(grp.members.values_list('program_batch_id', flat=True))
                    participating_batch_ids = member_batch_ids.intersection(cfg_batch_ids)
                    if not participating_batch_ids:
                        continue

                    course_code, faculty_id = key
                    code_pattern = re.compile(r'\b' + re.escape(course_code) + r'\b')
                    entry_course_codes = set()
                    for asgn in cfg_assignments:
                        if asgn.batch_id not in participating_batch_ids:
                            continue
                        if asgn.faculty_id != faculty_id:
                            continue
                        asgn_key = TimetableEngine._clubbing_key_for_assignment(asgn)
                        if asgn_key == key and asgn.course and asgn.course.course_code:
                            entry_course_codes.add(asgn.course.course_code)

                    if not entry_course_codes:
                        entry_course_codes.add(course_code)

                    payload = accumulated_clubbed_slots.setdefault(
                        key,
                        {'theory': set(), 'lab': set()},
                    )

                    for day, slot_num, entry_course_code, special_note, is_lab, lab_room_id in candidate_entries:
                        if entry_course_code not in entry_course_codes and not (special_note and code_pattern.search(special_note)):
                            continue
                        if is_lab and include_labs:
                            # Keep one canonical lab room per (day, slot) to avoid
                            # clubbed followers diverging into different labs.
                            existing = [item for item in payload['lab'] if item[0] == day and item[1] == slot_num]
                            selected_room = lab_room_id
                            if existing:
                                for item in existing:
                                    payload['lab'].discard(item)
                                existing_rooms = [item[2] if len(item) >= 3 else None for item in existing]
                                existing_non_null = [rid for rid in existing_rooms if rid is not None]
                                if existing_non_null and selected_room is None:
                                    selected_room = existing_non_null[0]
                                elif existing_non_null and selected_room is not None and selected_room not in existing_non_null:
                                    selected_room = min(existing_non_null + [selected_room])
                            payload['lab'].add((day, slot_num, selected_room))
                        if (not is_lab) and include_theory:
                            payload['theory'].add((day, slot_num))

            def _schedule_global_clubbed_theory():
                if not engines:
                    return

                batch_to_engine = {}
                for engine in engines:
                    for batch in engine._batch_list:
                        batch_to_engine[batch.id] = engine

                time_slots = engines[0].time_slots

                for key, grp in clubbed_lookup.items():
                    course_code, faculty_id = key
                    members = []
                    for member in grp.members.select_related('program_batch'):
                        engine = batch_to_engine.get(member.program_batch_id)
                        if not engine:
                            continue

                        timetable = engine._timetable_map.get(member.program_batch_id)
                        if not timetable:
                            continue

                        req = None
                        for cr in engine._course_requirements_map.get(member.program_batch_id, []):
                            asgn = cr['assignment']
                            asgn_key = engine._clubbing_key_for_assignment(asgn)
                            if asgn_key == (course_code, faculty_id):
                                req = cr
                                break

                        if req is None:
                            continue

                        members.append((engine, timetable, req))

                    if len(members) < 2:
                        continue

                    theory_needed = min(req['theory_remaining'] for _, _, req in members)
                    if theory_needed <= 0:
                        continue

                    course_days = set()
                    periods_placed = 0

                    for _ in range(theory_needed):
                        scheduled = False
                        day_order = sorted(DAYS, key=lambda d: d in course_days)

                        for day in day_order:
                            if scheduled:
                                break

                            slot_order = members[0][0]._ordered_theory_slots_for_faculty_ids([faculty_id])
                            for ts in slot_order:
                                if ts.is_break:
                                    continue

                                slot = ts.slot_number

                                if any(engine._is_blocked_by_me_lab_assist(day, [slot]) for engine, _timetable, _ in members):
                                    continue

                                if any((day, slot) in engine.occupied[timetable.id] for engine, timetable, _ in members):
                                    continue

                                if any(not engine._is_faculty_available(faculty_id, day, slot) for engine, _, _ in members):
                                    continue

                                for engine, timetable, req in members:
                                    asgn = req['assignment']
                                    TimetableEntry.objects.create(
                                        timetable=timetable,
                                        day=day,
                                        time_slot=ts,
                                        course=asgn.course,
                                        faculty=asgn.faculty,
                                        is_lab=False,
                                        special_note="Clubbed",
                                    )
                                    engine.occupied[timetable.id].add((day, slot))
                                    engine._book_faculty(faculty_id, day, slot)
                                    req['theory_remaining'] = max(0, req['theory_remaining'] - 1)

                                accumulated_clubbed_slots.setdefault(
                                    key,
                                    {'theory': set(), 'lab': set()},
                                )['theory'].add((day, slot))
                                course_days.add(day)
                                periods_placed += 1
                                scheduled = True
                                break

                        if not scheduled:
                            remaining = theory_needed - periods_placed
                            member_labels = []
                            for engine, timetable, _req in members:
                                batch = timetable.program_batch
                                member_labels.append(
                                    f"{batch.program.code} Year {batch.year_of_study} Batch {batch.batch_name}"
                                )
                            all_warnings.append(
                                f"Could not align clubbed theory for {course_code} "
                                f"({remaining} periods remaining) across {', '.join(member_labels)}"
                            )
                            break

            engines = []
            for cfg in configs:
                engine = TimetableEngine(
                    cfg,
                    exclude_batch_ids=all_batch_ids,
                    clubbed_slots=_clubbed_slot_snapshot(),
                    lab_occupancy=set(accumulated_lab_occupancy),
                    lab_assist_slots=accumulated_be_lab_slots_by_course,
                    generation_preferences=generation_preferences,
                )
                prepared = engine._prepare_generation(effective_date=date.today())
                if not prepared.get('success'):
                    all_warnings.append(
                        f"{cfg.program.code} Year {cfg.year_of_study}: {prepared.get('error', 'Failed')}"
                    )
                    all_warnings.extend(prepared.get('warnings', []))
                    continue
                engines.append(engine)

            if not engines:
                return {
                    'success': False,
                    'error': 'No configs could be prepared for generation',
                    'timetables': [],
                    'warnings': TimetableEngine._filter_public_warnings(all_warnings),
                }

            for engine in engines:
                engine.clubbed_slots = _clubbed_slot_snapshot()
                engine._rebuild_pending_clubbed_slot_set()
                engine._reserve_imported_clubbed_slots()
                engine._refresh_external_commitments()
                for lab_type in (4, 3, 2):
                    engine._schedule_lab_phase_for_type(lab_type)
                engine._mark_pec_lab_requirements_handled()
                _collect_cfg_slot_payload(
                    engine.config,
                    include_theory=False,
                    include_labs=True,
                )

            for engine in engines:
                engine._refresh_external_commitments()
            _schedule_global_clubbed_theory()

            for engine in engines:
                engine.clubbed_slots = _clubbed_slot_snapshot()
                engine._rebuild_pending_clubbed_slot_set()
                engine._refresh_external_commitments()
                engine._run_theory_phase()
                all_results.extend(engine._finalize_generation())
                all_warnings.extend(engine.warnings)
                _collect_cfg_slot_payload(
                    engine.config,
                    include_theory=True,
                    include_labs=False,
                )

            return {
                'success': True,
                'timetables': all_results,
                'warnings': TimetableEngine._filter_public_warnings(all_warnings),
            }

            for cfg in configs:
                engine = TimetableEngine(
                    cfg,
                    exclude_batch_ids=all_batch_ids,
                    clubbed_slots=dict(accumulated_clubbed_slots),
                    lab_occupancy=set(accumulated_lab_occupancy),
                )
                result = engine.generate(effective_date=date.today())

                if result['success']:
                    all_results.extend(result['timetables'])
                    all_warnings.extend(result.get('warnings', []))

                    # Carry forward lab-room occupancy so later configs cannot book
                    # the same lab room in the same day/period.
                    cfg_batch_ids = list(
                        ProgramBatch.objects.filter(
                            academic_year=cfg.academic_year,
                            program=cfg.program,
                            year_of_study=cfg.year_of_study,
                            is_active=True,
                        ).values_list('id', flat=True)
                    )
                    new_lab_slots = TimetableEntry.objects.filter(
                        timetable__program_batch_id__in=cfg_batch_ids,
                        timetable__is_active=True,
                        lab_room__isnull=False,
                        is_lab=True,
                    ).values_list('day', 'time_slot__slot_number', 'lab_room_id')
                    for day, slot_num, lab_id in new_lab_slots:
                        accumulated_lab_occupancy.add((day, slot_num, lab_id))

                    # ── Collect newly placed clubbed-course slots ──
                    # For each course that belongs to a clubbed group,
                    # find the timetable entries just created and record
                    # their (day, slot) pairs for the next configs.
                    cfg_batch_ids = list(
                        ProgramBatch.objects.filter(
                            academic_year=cfg.academic_year,
                            program=cfg.program,
                            year_of_study=cfg.year_of_study,
                            is_active=True,
                        ).values_list('id', flat=True)
                    )

                    # Check every clubbed group to see if its course was
                    # assigned in this config's batches
                    for key, grp in clubbed_lookup.items():
                        if key in accumulated_clubbed_slots:
                            continue  # already recorded from an earlier config

                        # Does this config's program participate in this group?
                        member_batch_ids = set(
                            grp.members.values_list('program_batch_id', flat=True)
                        )
                        if not member_batch_ids.intersection(cfg_batch_ids):
                            continue

                        # Find the TimetableEntry records just created for
                        # this course+faculty in this config's timetables
                        course_code, faculty_id = key
                        candidate_entries = TimetableEntry.objects.filter(
                            timetable__program_batch_id__in=cfg_batch_ids,
                            timetable__is_active=True,
                        ).values_list(
                            'day',
                            'time_slot__slot_number',
                            'course__course_code',
                            'special_note',
                            'is_lab',
                            'lab_room_id',
                        )

                        code_pattern = re.compile(r'\b' + re.escape(course_code) + r'\b')
                        payload = {'theory': set(), 'lab': set()}
                        for day, slot_num, entry_course_code, special_note, is_lab, lab_room_id in candidate_entries:
                            if entry_course_code == course_code or (special_note and code_pattern.search(special_note)):
                                if is_lab:
                                    payload['lab'].add((day, slot_num, lab_room_id))
                                else:
                                    payload['theory'].add((day, slot_num))

                        if payload['theory'] or payload['lab']:
                            accumulated_clubbed_slots[key] = {
                                'theory': sorted(payload['theory']),
                                'lab': sorted(payload['lab']),
                            }
                else:
                    all_warnings.append(
                        f"{cfg.program.code} Year {cfg.year_of_study}: {result.get('error', 'Failed')}"
                    )

        return {
            'success': True,
            'timetables': all_results,
            'warnings': TimetableEngine._filter_public_warnings(all_warnings),
        }

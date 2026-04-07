from django.utils.deprecation import MiddlewareMixin
from django.urls import reverse
from django.shortcuts import redirect


class LoginCheckMiddleWare(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        modulename = view_func.__module__
        user = request.user  # Who is the current user?
        if user.is_authenticated:
            # Check if user is HOD (via Faculty_Profile.designation)
            if user.is_hod:
                # HOD in faculty mode can access staff_views
                if request.session.get('hod_view_mode') == 'faculty':
                    if modulename == 'main_app.student_views':
                        return redirect(reverse('staff_home'))
                    # Allow access to staff_views in faculty mode
                else:
                    # HOD in admin mode - redirect from student views to admin home
                    if modulename == 'main_app.student_views':
                        return redirect(reverse('admin_home'))
                    # Allow access to both hod_views and staff_views in admin mode
                    # (HOD can still access faculty features even in admin mode)
            elif user.role in ['FACULTY', 'GUEST']:  # Faculty or Guest Faculty (non-HOD)
                if modulename == 'main_app.student_views' or modulename == 'main_app.hod_views':
                    return redirect(reverse('staff_home'))
            elif user.role == 'STUDENT':  # Student
                if modulename == 'main_app.hod_views' or modulename == 'main_app.staff_views':
                    return redirect(reverse('student_home'))
            elif user.role == 'STAFF':  # Non-teaching staff (lab assistants)
                # Non-teaching staff can only access limited areas
                if modulename == 'main_app.hod_views' or modulename == 'main_app.student_views':
                    return redirect(reverse('staff_home'))
            else:  # None of the aforementioned? Please take the user to login page
                return redirect(reverse('login_page'))
        else:
            # Unauthenticated users
            # Allow access to login-related pages
            allowed_paths = [
                reverse('login_page'),
                reverse('user_login'),
                reverse('student_first_login'),
                reverse('send_student_otp'),
                reverse('verify_student_otp'),
                reverse('student_set_password'),
            ]
            
            if request.path in allowed_paths or modulename == 'django.contrib.auth.views':
                # Allow access to authentication-related pages
                pass
            else:
                return redirect(reverse('login_page'))

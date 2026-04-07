"""
Signals for auto-creating user profiles
"""

from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete
from core.models import Account_User
from .models import Faculty_Profile, NonTeachingStaff_Profile, Student_Profile


@receiver(post_save, sender=Account_User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create role-specific profile when user is created"""
    if created:
        if instance.role in ['FACULTY', 'HOD', 'GUEST']:
            Faculty_Profile.objects.get_or_create(
                user=instance,
                defaults={
                    'staff_id': f'TEMP_{instance.id.hex[:8].upper()}',
                    'is_external': (instance.role == 'GUEST'),
                    'designation': 'HOD' if instance.role == 'HOD' else 'AP'
                }
            )
        elif instance.role == 'STAFF':
            NonTeachingStaff_Profile.objects.get_or_create(
                user=instance,
                defaults={'staff_id': f'TEMP_{instance.id.hex[:8].upper()}'}
            )
        elif instance.role == 'STUDENT':
            Student_Profile.objects.get_or_create(
                user=instance,
                defaults={
                    'register_no': f'0000000000',  # Placeholder - must be updated
                    'batch_label': 'N'
                }
            )


@receiver(pre_delete, sender=Account_User)
def delete_user_files(sender, instance, **kwargs):
    """Delete profile picture from filesystem when user is deleted"""
    if instance.profile_pic and instance.profile_pic.name:
        try:
            # Only delete if the file actually exists in storage
            if instance.profile_pic.storage.exists(instance.profile_pic.name):
                instance.profile_pic.delete(save=False)
        except Exception as e:
            # Log but don't fail the deletion if file cleanup fails
            print(f"Warning: Could not delete profile pic for {instance.email}: {e}")

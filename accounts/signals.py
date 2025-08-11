"""
Signals for the accounts app.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """Handle post-save operations for User model."""
    if created:
        # Add any post-creation logic here
        # For example: send welcome email, create related objects, etc.
        print(f"New user created: {instance.email}")
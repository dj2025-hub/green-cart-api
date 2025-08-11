"""
Models for user management.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom user model that extends AbstractUser.
    Uses email as the main identifier instead of username.
    """

    # Choix pour les types d'utilisateurs
    USER_TYPE_CHOICES = [
        ('CONSUMER', 'Consommateur'),
        ('PRODUCER', 'Producteur'),
    ]

    # Basic fields
    user_type = models.CharField(
        'Type d\'utilisateur',
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='CONSUMER',
        help_text='Type de compte utilisateur'
    )
    email = models.EmailField(
        'Email Address',
        unique=True,
        error_messages={
            'unique': "A user with this email already exists.",
        },
    )

    first_name = models.CharField(
        'First Name',
        max_length=150,
        blank=True
    )

    last_name = models.CharField(
        'Last Name',
        max_length=150,
        blank=True
    )

    # Phone number with Cameroon format validation
    phone_regex = RegexValidator(
        regex=r'^(\+237|237)?[2368]\d{7,8}'
        ,
        message="Phone number must be in Cameroon format. Example: +237677123456 or 677123456"
    )
    phone_number = models.CharField(
        'Phone Number',
        validators=[phone_regex],
        max_length=15,
        blank=True,
        help_text='Cameroon phone number format: +237677123456'
    )

    # Avatar
    avatar = models.ImageField(
        'Profile Picture',
        upload_to='avatars/%Y/%m/%d/',
        blank=True,
        null=True
    )

    # Status fields
    is_verified = models.BooleanField(
        'Email Verified',
        default=False,
        help_text='Designates whether the user has verified their email address.'
    )

    # Timestamps
    created_at = models.DateTimeField(
        'Created At',
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        'Updated At',
        auto_now=True
    )

    # Authentication settings
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active', 'is_verified']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        """String representation of the user."""
        return self.email

    @property
    def full_name(self):
        """Returns the user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def short_name(self):
        """Returns the first name or username if no first name."""
        return self.first_name or self.username

    @property
    def avatar_url(self):
        """Returns the avatar URL or a default URL."""
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        # Using a placeholder service for default avatar
        return f'https://ui-avatars.com/api/?name={self.first_name}+{self.last_name}&background=4CAF50&color=fff&size=100'

    def get_absolute_url(self):
        """Returns the URL for the user's profile."""
        return f"/users/{self.pk}/"

    def format_phone_number(self):
        """Returns formatted phone number with +237 prefix."""
        if not self.phone_number:
            return ""

        # Remove any existing prefix and spaces
        number = self.phone_number.replace('+237', '').replace('237', '').replace(' ', '')

        # Add +237 prefix if it's a valid Cameroon number
        if len(number) >= 9:
            return f"+237{number}"
        return self.phone_number


# Signals for automatic profile management
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """Handle post-save operations for User model."""
    if created:
        # You can add any post-creation logic here
        # For example, sending welcome email, creating related objects, etc.
        pass


class Producer(models.Model):
    """
    Producer profile extending User model.
    Contains business information for local producers.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='producer_profile'
    )
    
    business_name = models.CharField(
        'Nom de l\'entreprise',
        max_length=200,
        help_text='Nom de votre exploitation ou entreprise'
    )
    
    description = models.TextField(
        'Description',
        blank=True,
        help_text='Décrivez votre activité, vos méthodes de production, etc.'
    )
    
    siret = models.CharField(
        'Numéro SIRET',
        max_length=14,
        blank=True,
        help_text='Numéro SIRET de votre entreprise (optionnel pour MVP)'
    )
    
    address = models.TextField(
        'Adresse complète',
        help_text='Adresse de votre exploitation'
    )
    
    city = models.CharField(
        'Ville',
        max_length=100
    )
    
    postal_code = models.CharField(
        'Code postal',
        max_length=10
    )
    
    region = models.CharField(
        'Région',
        max_length=100,
        help_text='Région française pour faciliter la recherche locale'
    )
    
    is_verified = models.BooleanField(
        'Producteur vérifié',
        default=False,
        help_text='Indique si le producteur a été vérifié par l\'équipe GreenCart'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Producteur'
        verbose_name_plural = 'Producteurs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['region']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['city']),
        ]
    
    def __str__(self):
        return f"{self.business_name} - {self.user.email}"
    
    @property
    def full_address(self):
        """Retourne l'adresse complète formatée."""
        return f"{self.address}, {self.postal_code} {self.city}"
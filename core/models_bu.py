from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    profile_image = models.ImageField(upload_to='uploads/profiles/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class OTP(models.Model):
    PURPOSE_CHOICES = [
        ('verify', 'verify'),
        ('reset', 'reset'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return (not self.is_used) and timezone.now() <= self.expires_at

    def __str__(self):
        return f"OTP({self.user.email}, {self.purpose})"


class RoomRedesign(models.Model):
    STYLE_CHOICES = [
        ('modern', 'modern'),
        ('minimalist', 'minimalist'),
        ('luxury', 'luxury'),
        ('industrial', 'industrial'),
        ('scandinavian', 'scandinavian'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='redesigns')
    original_image = models.ImageField(upload_to='uploads/originals/')
    style_choice = models.CharField(max_length=32, choices=STYLE_CHOICES)
    prompt = models.TextField(blank=True)
    result_image = models.ImageField(upload_to='uploads/results/', blank=True, null=True)
    result_base64 = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Redesign({self.user.email}, {self.style_choice}, {self.created_at:%Y-%m-%d})"

import uuid
from django.db import models
from django.db.models import Q
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError

from ..core.models import TimeStampedModel, validate_country_iso2, validate_char5_lang
from models import LinguistProfile

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório para criar um usuário.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('O superusuário deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('O superusuário deve ter is_superuser=True.')
        #porque não usar um switch?

        return self.create_user(email, password, **extra_fields)
    
class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=2, validators=[validate_country_iso2], blank=True)
    language = models.CharField(max_length=5, validators=[validate_char5_lang], blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    last_login = models.DateTimeField(blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    objects = UserManager()

    def __str__(self):
        return self.email
    
class Residency(models.TextChoices):
    BR = 'BR', 'Brasil'
    ESTRANGEIRO = 'ESTRANGEIRO', 'Estrangeiro'

class CustomerType(models.TextChoices):
    INDIVIDUAL = 'INDIVIDUAL', 'Pessoa Física'
    COMPANY = 'COMPANY', 'Pessoa Jurídica'

class CustomerProfile(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')

    residency = models.CharField(max_length=20, choices=Residency.choices, db_index=True)
    customer_type = models.CharField(max_length=20, choices=CustomerType.choices, db_index=True)

    legal_name = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=2, validators=[validate_country_iso2], blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    tax_id_br = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    foreign_tax_id_type = models.CharField(max_length=30, blank=True, null=True)
    foreign_tax_id_absent_reason = models.TextField(blank=True, null=True)

    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                name='valid_tax_id_based_on_residency',
                check=Q(residency=Residency.BR, tax_id_br__isnull=False) | 
                      Q(residency=Residency.ESTRANGEIRO, foreign_tax_id_type__isnull=False),
            )
        ]

    def clean(self):
        return super().clean()
        self.country = (self.country or "").upper()
        if self.residency == Residency.BR and not self.tax_id_br:
            raise ValidationError('Para residentes no Brasil, o campo tax_id_br é obrigatório.')
        
    class LinguistProfile(TimeStampedModel):
        id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
        user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='linguist_profile')

        native_language = models.CharField(max_length=5, validators=[validate_char5_lang], blank=True)
        languages_spoken = models.JSONField(default=list, blank=True)

    class LanguagePair(TimeStampedModel):
        id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
        linguist_profile = models.ForeignKey(LinguistProfile, on_delete=models.CASCADE, related_name='language_pairs')
        source_language = models.CharField(max_length=5, validators=[validate_char5_lang])
        target_language = models.CharField(max_length=5, validators=[validate_char5_lang])
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['linguist_profile', 'source_language', 'target_language'], name='unique_language_pair')
        ]
import uuid
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

def validate_country_iso2(value: str):
    if not value or len(value) != 2 or not value.isalpha():
        raise ValidationError('O código de país deve conter exatamente 2 letras: ("BR", "US", etc.).')

def validate_char5_lang(value: str):
    if not value or len(value) != 5:
        raise ValidationError('O código do idioma deve estar no formato: "aa-BB" (ex: "en-US").')
import uuid
from django.db import models
from django.db.models import Q
from django.core.validators import MinLengthValidator

from core.models import TimestampedModel
from apps.orders.models import ServiceRequest

class PaymentStatus(models.TextChoices):
    PENDING = "PENDENTE", "Pendente"
    COMPLETED = "COMPLETO", "Completo"
    FAILED = "FALHOU", "FalhoU"
    REFUNDED = "REEMBOLSADO", "Reembolsado"

class Payment(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name="payments")

    provider = models.CharField(max_length=50, db_index=True)
    provide_reference = models.CharField(max_length=100, db_index=True)
    
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING, db_index=True)
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, validators=[MinLengthValidator(3)])
    confirmed_at = models.DateTimeField(blank=True, null=True, db_index=True)

    payment_method = models.CharField(max_length=50)
    provider_payment_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["provider", "provide_reference"],
                name="unique_payment_provider_reference_per_request",                
            )
        ]
class WebhookEvent(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField(max_length=50, db_index=True)
    event_type = models.CharField(max_length=80)
    provider_event_id = models.CharField(max_length=120, blank=True, null=True)
    payload_json = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processing_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING, db_index=True)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["provider", "provider_event_id"],
                name="unique_webhook_provider_event_id",                
            )
        ]


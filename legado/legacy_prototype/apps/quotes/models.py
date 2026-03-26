import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinLengthValidator

from core.models import TimestampedModel
from apps.orders.models import ServiceRequest, ServiceRequestStatus

class QuoteStatus(models.TextChoices):
    DRAFT = "RASCUNHO", "Rascunho"
    SENT = "ENVIADO", "Enviado"
    ACCEPTED = "ACEITO", "Aceito"
    EXPIRED = "EXPIRADO", "Expirado"
    CANCELED = "CANCELADO", "Cancelado"     

class Quote(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_request = models.OneToOneField(ServiceRequest, on_delete=models.CASCADE, related_name="quote")

    currency = models.CharField(max_length=3, validators=[MinLengthValidator(3)])
    amount_total = models.DecimalField(max_digits=12, decimal_places=2)
    breakdown_json = models.JSONField(blank=True, null=True)
    valid_until = models.DateTimeField(db_index=True)

    status = models.CharField(max_length=20, choices=QuoteStatus.choices, default=QuoteStatus.DRAFT, db_index=True)
    accepted_at = models.DateTimeField(blank=True, null=True, db_index=True)
    terms_snapshot = models.TextField(blank=True, null=True)

    def accept(self, *, terms_snapshot: str):
        self.status = QuoteStatus.ACCEPTED
        self.accepted_at = timezone.now()
        self.terms_snapshot = terms_snapshot
        self.save()

        sr = self.service_request
        sr.status = ServiceRequestStatus.APPROVED
        sr.save()

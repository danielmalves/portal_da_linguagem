import uuid
from django.db import models
from django.core.validators import MinLengthValidator

from core.models import BaseModel
from core.models import ServiceRequest
from models import TimestampedModel

class InvoiceStatus(models.TextChoices):
    PENDING = 'PENDENTE', 'Pendente'
    ISSUED = 'EMITIDO', 'Emitido'
    ERROR = 'ERRO', 'Erro'
    CANCELLED = 'CANCELADO', 'Cancelado'

class Invoice(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='invoices')

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, validators=[MinLengthValidator(3)])
    status = models.CharField(max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.PENDING)
    issued_at = models.DateTimeField(blank=True, null=True)
    customer_snapshot_json = models.JSONField(blank=True, null=True)

class NFSeStatus(models.TextChoices):
    SUBMITTED = 'SUBMETIDO', 'Submetido'
    ISSUED = 'EMITIDO', 'Emitido'
    ERROR = 'ERRO', 'Erro'

class NFSe(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='nfse')

    provider = models.CharField(max_length=50, db_index=True)
    protocol = models.CharField(max_length=100, blank=True, null=True, db_index=True)

    NFSe_number = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    status = models.CharField(max_length=20, choices=NFSeStatus.choices, default=NFSeStatus.SUBMITTED)

    #issued_at = models.DateTimeField(blank=True, null=True)

    pdf_storage_key = models.TextField(blank=True, null=True)
    xml_storage_key = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

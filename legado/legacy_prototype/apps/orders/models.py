import uuid
from django.db import models

from core.models import TimestampedModel
from apps.orders.models import ServiceRequest, ServiceType
from apps.accounts.models import LinguistProfile

class AssignmentStatus(models.TextChoices):
    INVITED = "CONVIDADO", "Convidado"
    ACCEPTED = "ACEITO", "Aceito"
    DECLINED = "RECUSADO", "Recusado"
    IN_PROGRESS = "EM_PROGRESSO", "Em progresso"
    DELIVERED = "ENTREGUE", "Entregue"
    APPROVED = "APROVADO", "Aprovado"

class Assignment(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name="assignments")
    linguist = models.ForeignKey(LinguistProfile, on_delete=models.RESTRICT, related_name="assignments")

    assignment_type = models.CharField(max_length=20, choices=ServiceType.choices, db_index=True)
    status = models.CharField(max_length=20, choices=AssignmentStatus.choices,
                              default=AssignmentStatus.INVITED, db_index=True)

    deadline_at = models.DateTimeField(db_index=True)
    instructions = models.TextField(blank=True, null=True)
    agreed_rate_snapshot = models.JSONField(blank=True, null=True)

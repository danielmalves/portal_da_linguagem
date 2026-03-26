import uuid
from django.db import models
from django.db.models import Q

from core.models import TimestampedModel
from apps.accounts.models import User
from apps.orders.models import ServiceRequest
from staffing.models import Assignment

class AttachmentKind(models.TextChoices):
    SOURCE = "FONTE", "Fonte"
    REFERENCE = "REFERÊNCIA", "Referência"
    DELIVERABLE = "ENTREGÁVEL", "Entregável"
    OTHER = "OUTRO", "Outro"

class Attachment(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE,
                                        related_name="attachments", blank=True, null=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE,
                                   related_name="attachments", blank=True, null=True)

    uploaded_by_user = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="uploaded_attachments")

    kind = models.CharField(max_length=20, choices=AttachmentKind.choices, db_index=True)
    storage_key = models.TextField()
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, blank=True, null=True)
    size_bytes = models.BigIntegerField(blank=True, null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="chk_attachment_exactly_one_parent",
                check=((Q(service_request__isnull=False) & Q(assignment__isnull=True)) |
                       (Q(service_request__isnull=True) & Q(assignment__isnull=False))),
            )
        ]

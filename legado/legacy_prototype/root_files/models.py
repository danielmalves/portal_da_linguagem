# ============================================================
# Django models.py (v1) — núcleo do schema
# Inclui: enums, validações, constraints (CHECK/UNIQUE), relações
# Observação: em um projeto real, isso ficaria separado por app:
# accounts/models.py, orders/models.py, files/models.py, etc.
# Aqui está consolidado para você ter o “contrato” completo.
# ============================================================

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


# -----------------------------
# Helpers / Abstract base
# -----------------------------
class TimestampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        return super().save(*args, **kwargs)


def validate_country_iso2(value: str):
    if not value or len(value) != 2 or not value.isalpha():
        raise ValidationError("country deve ser ISO-3166 alpha-2 (ex: BR, US, FR).")
    # Normaliza
    # (não alteramos aqui para evitar efeitos colaterais; normalização pode ser no clean())


def validate_char5_lang(value: str):
    # Simplificado: aceita 'pt', 'en', 'es', 'fr' etc. ou BCP-47 curto.
    if not value or len(value) > 5:
        raise ValidationError("Código de idioma deve ter até 5 caracteres (ex: pt, en, pt-BR).")


# -----------------------------
# Accounts: User + Profiles
# -----------------------------
class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email: str, password: Optional[str], **extra_fields):
        if not email:
            raise ValueError("email é obrigatório")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: Optional[str] = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email=email, password=password, **extra_fields)

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser precisa is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser precisa is_superuser=True")
        return self._create_user(email=email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    last_login = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    def __str__(self) -> str:
        return self.email


class Residency(models.TextChoices):
    BR = "BR", "Brasil"
    FOREIGN = "FOREIGN", "Exterior"


class CustomerType(models.TextChoices):
    INDIVIDUAL = "INDIVIDUAL", "Pessoa física"
    COMPANY = "COMPANY", "Pessoa jurídica"


class CustomerProfile(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="customer_profile")

    residency = models.CharField(max_length=10, choices=Residency.choices, db_index=True)
    customer_type = models.CharField(max_length=20, choices=CustomerType.choices, db_index=True)

    legal_name = models.CharField(max_length=255)
    country = models.CharField(max_length=2, validators=[validate_country_iso2], db_index=True)
    phone = models.CharField(max_length=30, blank=True, null=True)

    # Brasil
    tax_id_br = models.CharField(max_length=20, blank=True, null=True, db_index=True)  # CPF/CNPJ (validação em clean)

    # Exterior
    foreign_tax_id = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    foreign_tax_id_type = models.CharField(max_length=30, blank=True, null=True)
    foreign_tax_id_absent_reason = models.TextField(blank=True, null=True)

    # Endereço (estrutura simples; você pode evoluir depois)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="chk_customer_taxid_by_residency",
                check=Q(residency=Residency.BR, tax_id_br__isnull=False) | Q(residency=Residency.FOREIGN),
            )
        ]

    def clean(self):
        super().clean()
        self.country = (self.country or "").upper()

        if self.residency == Residency.BR:
            if not self.tax_id_br:
                raise ValidationError({"tax_id_br": "Para residência BR, CPF/CNPJ é obrigatório."})
        # Para exterior, tax_id_br pode ficar vazio; se quiser impedir, faça:
        if self.residency == Residency.FOREIGN and self.tax_id_br:
            raise ValidationError({"tax_id_br": "Para cliente extrangeiro, não informe CPF/CNPJ."})

    def __str__(self) -> str:
        return f"{self.legal_name} ({self.country})"


class LinguistProfile(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="linguist_profile")

    timezone = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)

    def __str__(self) -> str:
        return f"Linguist: {self.user.email}"


class LanguagePair(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    linguist = models.ForeignKey(LinguistProfile, on_delete=models.CASCADE, related_name="language_pairs")

    source_lang = models.CharField(max_length=5, validators=[validate_char5_lang], db_index=True)
    target_lang = models.CharField(max_length=5, validators=[validate_char5_lang], db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["linguist", "source_lang", "target_lang"],
                name="uq_linguist_lang_pair",
            )
        ]

    def clean(self):
        super().clean()
        self.source_lang = (self.source_lang or "").strip()
        self.target_lang = (self.target_lang or "").strip()

    def __str__(self) -> str:
        return f"{self.linguist.user.email}: {self.source_lang}->{self.target_lang}"


# -----------------------------
# Orders / Requests
# -----------------------------
class ServiceType(models.TextChoices):
    TRANSLATION = "TRANSLATION", "Tradução"
    INTERPRETATION = "INTERPRETATION", "Interpretação"
    REVISION = "REVISION", "Revisão"


class ServiceRequestStatus(models.TextChoices):
    DRAFT = "DRAFT", "Rascunho"
    SUBMITTED = "SUBMITTED", "Enviada"
    QUOTED = "QUOTED", "Orçada"
    APPROVED = "APPROVED", "Aprovada"
    ASSIGNED = "ASSIGNED", "Alocada"
    IN_PROGRESS = "IN_PROGRESS", "Em andamento"
    DELIVERED = "DELIVERED", "Entregue"
    CLOSED = "CLOSED", "Encerrada"
    CANCELED = "CANCELED", "Cancelada"


class ServiceRequest(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(CustomerProfile, on_delete=models.RESTRICT, related_name="service_requests")

    service_type = models.CharField(max_length=20, choices=ServiceType.choices, db_index=True)
    source_lang = models.CharField(max_length=5, validators=[validate_char5_lang], db_index=True)
    target_lang = models.CharField(max_length=5, validators=[validate_char5_lang], db_index=True)

    subject_area = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    deadline_at = models.DateTimeField(db_index=True)
    instructions = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=ServiceRequestStatus.choices,
        default=ServiceRequestStatus.DRAFT,
        db_index=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=["customer", "-created_at"], name="idx_request_customer_created"),
            models.Index(fields=["status", "-updated_at"], name="idx_request_status_updated"),
            models.Index(fields=["deadline_at"], name="idx_request_deadline"),
            models.Index(fields=["source_lang", "target_lang"], name="idx_request_langs"),
        ]

    def __str__(self) -> str:
        return f"Request {self.id} ({self.service_type})"


class RequestMessage(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name="messages")
    author_user = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="request_messages")
    body = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=["service_request", "created_at"], name="idx_reqmsg_request_created"),
            models.Index(fields=["author_user"], name="idx_reqmsg_author"),
        ]


# -----------------------------
# Staffing / Assignments
# -----------------------------
class AssignmentStatus(models.TextChoices):
    INVITED = "INVITED", "Convidado"
    ACCEPTED = "ACCEPTED", "Aceito"
    DECLINED = "DECLINED", "Recusado"
    IN_PROGRESS = "IN_PROGRESS", "Em andamento"
    DELIVERED = "DELIVERED", "Entregue"
    APPROVED = "APPROVED", "Aprovado"


class Assignment(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name="assignments")
    linguist = models.ForeignKey(LinguistProfile, on_delete=models.RESTRICT, related_name="assignments")

    assignment_type = models.CharField(max_length=20, choices=ServiceType.choices, db_index=True)
    status = models.CharField(max_length=20, choices=AssignmentStatus.choices, default=AssignmentStatus.INVITED, db_index=True)

    deadline_at = models.DateTimeField(db_index=True)
    instructions = models.TextField(blank=True, null=True)

    # Congela o acordo com o prestador (ex: {unit: "HOUR", price: 120.00, currency: "BRL", min_units: 2})
    agreed_rate_snapshot = models.JSONField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["service_request", "status"], name="idx_assignment_request_status"),
            models.Index(fields=["linguist", "status"], name="idx_assignment_linguist_status"),
            models.Index(fields=["deadline_at"], name="idx_assignment_deadline"),
        ]


# -----------------------------
# Files / Attachments
# -----------------------------
class AttachmentKind(models.TextChoices):
    SOURCE = "SOURCE", "Arquivo-fonte"
    REFERENCE = "REFERENCE", "Referência"
    DELIVERABLE = "DELIVERABLE", "Entrega"
    OTHER = "OTHER", "Outro"


class Attachment(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    service_request = models.ForeignKey(
        ServiceRequest, on_delete=models.CASCADE, related_name="attachments", blank=True, null=True
    )
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="attachments", blank=True, null=True
    )
    uploaded_by_user = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="uploaded_attachments")

    kind = models.CharField(max_length=20, choices=AttachmentKind.choices, db_index=True)

    # Em produção você tende a usar FileField (S3/local). Aqui deixo storage_key explícito.
    storage_key = models.TextField()
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, blank=True, null=True)
    size_bytes = models.BigIntegerField(blank=True, null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="chk_attachment_exactly_one_parent",
                check=(
                    (Q(service_request__isnull=False) & Q(assignment__isnull=True))
                    | (Q(service_request__isnull=True) & Q(assignment__isnull=False))
                ),
            )
        ]
        indexes = [
            models.Index(fields=["service_request", "-created_at"], name="idx_attachment_request_created"),
            models.Index(fields=["assignment", "-created_at"], name="idx_attachment_assignment_created"),
            models.Index(fields=["kind"], name="idx_attachment_kind"),
        ]


# -----------------------------
# Quotes
# -----------------------------
class QuoteStatus(models.TextChoices):
    DRAFT = "DRAFT", "Rascunho"
    SENT = "SENT", "Enviado"
    ACCEPTED = "ACCEPTED", "Aceito"
    EXPIRED = "EXPIRED", "Expirado"
    CANCELED = "CANCELED", "Cancelado"


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
        # Regra de negócio no servidor:
        self.status = QuoteStatus.ACCEPTED
        self.accepted_at = timezone.now()
        self.terms_snapshot = terms_snapshot
        self.save()

        # Atualiza o pedido
        self.service_request.status = ServiceRequestStatus.APPROVED
        self.service_request.save()


# -----------------------------
# Payments
# -----------------------------
class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pendente"
    CONFIRMED = "CONFIRMED", "Confirmado"
    FAILED = "FAILED", "Falhou"
    REFUNDED = "REFUNDED", "Estornado"


class Payment(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name="payments")

    provider = models.CharField(max_length=50, db_index=True)
    provider_reference = models.CharField(max_length=100, db_index=True)

    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING, db_index=True)

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, validators=[MinLengthValidator(3)])

    confirmed_at = models.DateTimeField(blank=True, null=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["provider", "provider_reference"], name="uq_payment_provider_reference"),
        ]
        indexes = [
            models.Index(fields=["service_request", "status"], name="idx_payment_request_status"),
            models.Index(fields=["provider"], name="idx_payment_provider"),
            models.Index(fields=["confirmed_at"], name="idx_payment_confirmed_at"),
        ]


class WebhookEvent(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    provider = models.CharField(max_length=50, db_index=True)
    event_type = models.CharField(max_length=80, db_index=True)
    provider_event_id = models.CharField(max_length=120, blank=True, null=True)

    payload_json = models.JSONField()
    received_at = models.DateTimeField(default=timezone.now, db_index=True)

    processed_at = models.DateTimeField(blank=True, null=True)
    processing_status = models.CharField(max_length=20, default="PENDING", db_index=True)  # PENDING|PROCESSED|FAILED
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_event_id"],
                name="uq_webhook_provider_event",
                condition=Q(provider_event_id__isnull=False),
            )
        ]


# -----------------------------
# Billing / NFS-e
# -----------------------------
class InvoiceStatus(models.TextChoices):
    PENDING = "PENDING", "Pendente"
    ISSUED = "ISSUED", "Emitida"
    ERROR = "ERROR", "Erro"
    CANCELED = "CANCELED", "Cancelada"


class Invoice(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_request = models.OneToOneField(ServiceRequest, on_delete=models.CASCADE, related_name="invoice")

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, validators=[MinLengthValidator(3)])

    status = models.CharField(max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.PENDING, db_index=True)
    issued_at = models.DateTimeField(blank=True, null=True, db_index=True)

    # Congela os dados do tomador no momento da emissão
    customer_snapshot_json = models.JSONField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"], name="idx_invoice_status"),
            models.Index(fields=["issued_at"], name="idx_invoice_issued_at"),
        ]


class NFSeStatus(models.TextChoices):
    SUBMITTED = "SUBMITTED", "Enviado"
    ISSUED = "ISSUED", "Emitido"
    ERROR = "ERROR", "Erro"


class NFSeRecord(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, related_name="nfse")

    provider = models.CharField(max_length=50, db_index=True)
    protocol = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    nfse_number = models.CharField(max_length=100, blank=True, null=True, db_index=True)

    status = models.CharField(max_length=20, choices=NFSeStatus.choices, default=NFSeStatus.SUBMITTED, db_index=True)

    pdf_storage_key = models.TextField(blank=True, null=True)
    xml_storage_key = models.TextField(blank=True, null=True)

    error_message = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["provider"], name="idx_nfse_provider"),
            models.Index(fields=["protocol"], name="idx_nfse_protocol"),
            models.Index(fields=["nfse_number"], name="idx_nfse_number"),
            models.Index(fields=["status"], name="idx_nfse_status"),
        ]

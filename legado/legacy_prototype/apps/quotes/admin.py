from django.contrib import admin
from django.utils import timezone

from .models import Quote, QuoteStatus
from ..orders.models import ServiceRequestStatus


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    pass

@admin.action(description="Send quote (set Quote=SENT and Request=QUOTED)")
def send_quote(modeladmin, request, queryset):
    """
    Admin action:
      - Only sends quotes in DRAFT
      - Sets Quote.status = SENT
      - Sets ServiceRequest.status = QUOTED (if not already beyond it)
    """
    for quote in queryset.select_related("service_request"):
        if quote.status != QuoteStatus.DRAFT:
            continue

        # Quote state transition
        quote.status = QuoteStatus.SENT
        quote.save(update_fields=["status", "updated_at"])

        # Request state transition (defensive: don't move backwards)
        sr = quote.service_request
        if sr.status in (ServiceRequestStatus.DRAFT, ServiceRequestStatus.SUBMITTED):
            sr.status = ServiceRequestStatus.QUOTED
            sr.save(update_fields=["status", "updated_at"])


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ("id", "service_request", "status", "amount_total", "currency", "valid_until", "accepted_at", "created_at")
    list_filter = ("status", "currency")
    search_fields = ("id", "service_request__id", "service_request__customer__legal_name")
    ordering = ("-created_at",)
    actions = [send_quote]

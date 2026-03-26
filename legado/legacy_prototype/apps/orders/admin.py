from django.contrib import admin
from .models import ServiceRequest, RequestMessage

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "service_type", "source_lang", "target_lang", "status", "deadline_at", "created_at")
    list_filter = ("status", "service_type", "source_lang", "target_lang")
    search_fields = ("id", "customer__legal_name", "customer__user__email")
    ordering = ("-created_at",)

@admin.register(RequestMessage)
class RequestMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "service_request", "author_user", "created_at")
    search_fields = ("id", "service_request__id", "author_user__email")
    ordering = ("-created_at",)

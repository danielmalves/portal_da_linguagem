from django.urls import path
from django.views import attachment_upload, attachment_delete

urlpatterns = [
    path("order/<uuid:request_id>/upload/", attachment_upload, name="attachment_upload"),
    path("attachments/<uuid:attachment_id>/delete/", attachment_delete, name="attachment_delete"),
]
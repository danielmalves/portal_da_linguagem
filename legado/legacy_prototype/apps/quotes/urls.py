from django.urls import path
from .views import accept_quote
urlpatterns = [
    path("<uuid:quote_id>/accept/", accept_quote, name="quote_accept"),
]

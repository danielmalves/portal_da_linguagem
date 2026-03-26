from django.urls import path
from django.views import RequestListView, RequestCreateView, RequestDetailView

urlpatterns = [
    path("", RequestListView.as_view(), name="request_list"), 
    path("new/", RequestCreateView.as_view(), name="request_create"),
    path("<uuid:pk>/", RequestDetailView.as_view(), name="request_detail"),
    ]
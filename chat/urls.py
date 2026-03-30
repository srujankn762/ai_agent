from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ChatView, UploadDocumentView, UploadURLView

urlpatterns = [
    path("chat/", ChatView.as_view()),
    path("upload/", UploadDocumentView.as_view()),
    path("upload-url/", UploadURLView.as_view()),
]

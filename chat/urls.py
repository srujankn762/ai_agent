from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ChatView, UploadDocumentView, UploadLogViewSet, UploadURLView

router = DefaultRouter()
router.register("upload-logs", UploadLogViewSet, basename="upload-log")

urlpatterns = [
    path("chat/", ChatView.as_view()),
    path("upload/", UploadDocumentView.as_view()),
    path("upload-url/", UploadURLView.as_view()),
] + router.urls

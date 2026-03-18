from django.urls import path
from .views import ChatView, UploadDocumentView

urlpatterns = [
    path("chat/", ChatView.as_view()),
    path("upload/", UploadDocumentView.as_view()),
]
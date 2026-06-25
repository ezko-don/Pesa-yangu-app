from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ChatMessageViewSet, ChatView, NotificationViewSet

router = DefaultRouter()
router.register("chat/history", ChatMessageViewSet, basename="chatmessage")
router.register("notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("chat/", ChatView.as_view(), name="chat"),
    path("", include(router.urls)),
]

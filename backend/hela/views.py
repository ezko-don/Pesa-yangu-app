from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import client
from .models import ChatMessage, Notification
from .serializers import (
    ChatMessageSerializer,
    ChatRequestSerializer,
    NotificationSerializer,
)


class ChatView(APIView):
    """Send a message to Hela AI; persists both turns and returns the reply."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        msgs = ChatMessage.objects.filter(user=request.user)
        return Response(ChatMessageSerializer(msgs, many=True).data)

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        text = serializer.validated_data["message"]

        history = [
            {"role": m.role, "content": m.content}
            for m in ChatMessage.objects.filter(user=request.user)[:20]
        ]
        ChatMessage.objects.create(
            user=request.user, role=ChatMessage.Role.USER, content=text
        )
        result = client.respond(request.user, text, history)
        assistant_msg = ChatMessage.objects.create(
            user=request.user, role=ChatMessage.Role.ASSISTANT, content=result["reply"]
        )
        return Response({
            "reply": result["reply"],
            "logged": result["logged"],
            "message_id": assistant_msg.id,
        })


class ChatMessageViewSet(viewsets.ModelViewSet):
    """Chat history: mark sensitive, delete individual, bulk-delete (TOTP-gated)."""

    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        return ChatMessage.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"])
    def bulk_delete(self, request):
        # Bulk delete is TOTP-gated (spec 3.8). Enforced when 2FA is enabled.
        if request.user.two_factor_enabled and not request.data.get("totp"):
            return Response(
                {"detail": "TOTP code required for bulk delete."},
                status=status.HTTP_403_FORBIDDEN,
            )
        deleted, _ = self.get_queryset().delete()
        return Response({"deleted": deleted})


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(read=False).update(read=True)
        return Response({"updated": updated})

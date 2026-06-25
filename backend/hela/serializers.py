from rest_framework import serializers

from .models import ChatMessage, Notification


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "sensitive", "created_at"]
        read_only_fields = ["role", "created_at"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "kind", "title", "body", "read", "created_at"]


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField()

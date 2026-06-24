from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import SmsSource

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    phone_masked = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "first_name", "last_name", "email_verified",
            "phone", "phone_masked", "tax_id", "account_type", "country", "currency",
            "two_factor_enabled", "biometric_enabled",
            "whatsapp_connected", "telegram_connected",
        ]
        read_only_fields = ["email_verified", "phone_masked"]
        extra_kwargs = {"phone": {"write_only": True}, "tax_id": {"write_only": True}}

    def get_phone_masked(self, obj) -> str:
        if not obj.phone:
            return ""
        return "•••• " + obj.phone[-3:]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ["email", "username", "first_name", "password", "account_type", "phone"]
        extra_kwargs = {
            "username": {"required": False},
            "first_name": {"required": False},
            "account_type": {"required": False},
            "phone": {"required": False},
        }

    def create(self, validated_data):
        password = validated_data.pop("password")
        username = validated_data.get("username") or validated_data["email"]
        validated_data["username"] = username
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class SmsSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmsSource
        fields = [
            "id", "name", "short_code", "enabled", "status",
            "transaction_count", "last_sync_at",
        ]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

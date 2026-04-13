from rest_framework import serializers

from chat.models import UploadLog


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField()
    recipient = serializers.EmailField(required=False, allow_null=True)


class UploadLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadLog
        fields = "__all__"

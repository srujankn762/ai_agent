from rest_framework import serializers

from chat.models import UploadLog


class UploadLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadLog
        fields = "__all__"

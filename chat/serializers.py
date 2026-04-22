from rest_framework import serializers

from chat.models import UploadLog


class RecipientField(serializers.Field):
    default_error_messages = {
        "invalid": "Recipient must be an email, a comma-separated list of emails, or a list of emails.",
    }

    def to_internal_value(self, data):
        validator = serializers.EmailField()

        if data in (None, ""):
            return None

        if isinstance(data, str):
            recipients = [email.strip() for email in data.split(",") if email.strip()]
        elif isinstance(data, list):
            recipients = data
        else:
            self.fail("invalid")

        if not recipients:
            return None

        try:
            return [validator.run_validation(email) for email in recipients]
        except serializers.ValidationError as exc:
            raise serializers.ValidationError(exc.detail)

    def to_representation(self, value):
        return value


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField()
    recipients = RecipientField(required=False, allow_null=True)


class UploadLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadLog
        fields = "__all__"

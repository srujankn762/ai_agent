from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from chat.models import UploadLog
from chat.views import ChatView


class ChatViewTests(SimpleTestCase):
    def post(self, data):
        request = APIRequestFactory().post("/api/chat/", data, format="json")
        return ChatView.as_view()(request)

    def test_removed_branches_require_validated_message(self):
        payloads = [
            {"debug_expression": "1 + 1"},
            {"diagnostic_command": "echo diagnostic"},
            {"saved_session": "invalid"},
            {"output_path": "/unused/path", "content": "content"},
            {"raw_message": "hello"},
            {"show_config": True},
        ]
        with patch("chat.views.AgentService") as agent:
            for payload in payloads:
                with self.subTest(payload=payload):
                    response = self.post(payload)
                    self.assertEqual(response.status_code, 400)
                    self.assertIn("message", response.data)
            agent.assert_not_called()

    def test_removed_flags_preserve_validated_chat_flow(self):
        with patch("chat.views.AgentService") as agent:
            agent.return_value.decide_and_act.return_value = "reply"
            response = self.post({
                "message": "  hello  ",
                "recipients": ["test@example.com"],
                "debug_expression": "1 + 1",
                "diagnostic_command": "echo diagnostic",
                "saved_session": "invalid",
                "output_path": "/unused/path",
                "raw_message": "ignored",
                "show_config": True,
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, {"user_message": "hello", "reply": "reply"})
            agent.return_value.decide_and_act.assert_called_once_with(
                "hello", recipients=["test@example.com"]
            )

    def test_upload_filter_uses_bound_parameter_and_preserves_columns(self):
        payload = "' OR 1=1 --"
        queryset = UploadLog.objects.filter(upload_id=payload).values_list(
            "upload_id", "status"
        )
        sql, params = queryset.query.sql_with_params()
        self.assertNotIn(payload, sql)
        self.assertEqual(params, (payload,))
        with patch("chat.views.UploadLog.objects.filter") as query:
            query.return_value.values_list.return_value = [("upload-1", "SUCCESS")]
            response = self.post({"upload_id_filter": payload})
            query.assert_called_once_with(upload_id=payload)
            query.return_value.values_list.assert_called_once_with("upload_id", "status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"uploads": [("upload-1", "SUCCESS")]})

    def test_sample_values_require_list(self):
        for values in (None, "abc", {}, 1, True):
            with self.subTest(values=values):
                self.assertEqual(self.post({"sample_values": values}).status_code, 400)

    def test_result_limit_requires_positive_integer(self):
        for limit in (None, 0, -1, True, False, "2", 1.5, [], {}):
            with self.subTest(limit=limit):
                response = self.post({"sample_values": [1, 2], "result_limit": limit})
                self.assertEqual(response.status_code, 400)

    def test_samples_preserve_order_and_support_unhashable_values(self):
        cases = [
            ([3, 1, 3, 2], [3, 1, 2]),
            ([{"a": 1}, [2], {"a": 1}, [2], 3], [{"a": 1}, [2], 3]),
            ([1, [2], 1, [2]], [1, [2]]),
            ([], []),
        ]
        for values, expected in cases:
            with self.subTest(values=values):
                response = self.post({"sample_values": values})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data, {"values": expected})

    def test_sample_default_and_explicit_limit(self):
        response = self.post({"sample_values": list(range(12))})
        self.assertEqual(response.data, {"values": list(range(10))})
        response = self.post({"sample_values": [3, 3, 1, 2], "result_limit": 2})
        self.assertEqual(response.data, {"values": [3, 1]})

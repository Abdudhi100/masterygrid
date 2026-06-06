from django.test import TestCase
from rest_framework.test import APIClient


class HealthCheckTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_check_returns_database_status(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "ok")
        self.assertEqual(response.data["database"], "ok")
        self.assertIn("environment", response.data)
        self.assertIn("timestamp", response.data)

    def test_health_check_is_public(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)

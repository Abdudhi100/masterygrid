from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.accounts.models import User
from apps.academics.models import Subject
from apps.common.choices import UserRole
from apps.schools.models import School


@override_settings(DEBUG=True)
class CleanupE2EDataCommandTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name="Cleanup Test School",
            slug="cleanup-test-school",
        )

    def create_e2e_user(self, run_id="run123", role=UserRole.STUDENT):
        return User.objects.create_user(
            email=f"e2e.{role}.{run_id}@masterygrid.test",
            password="Password123!",
            full_name=f"E2E {role.title()} {run_id}",
            role=role,
            school=self.school,
        )

    def test_dry_run_does_not_delete_records(self):
        user = self.create_e2e_user()
        output = StringIO()

        call_command("cleanup_e2e_data", stdout=output)

        self.assertTrue(User.objects.filter(id=user.id).exists())
        self.assertIn("Dry run only", output.getvalue())
        self.assertIn("Users: 1", output.getvalue())

    def test_confirm_deletes_e2e_users_but_not_demo_users(self):
        e2e_user = self.create_e2e_user()
        demo_user = User.objects.create_user(
            email="student1@masterygrid.demo",
            password="Password123!",
            full_name="Demo Student",
            role=UserRole.STUDENT,
            school=self.school,
        )

        call_command("cleanup_e2e_data", "--confirm", stdout=StringIO())

        self.assertFalse(User.objects.filter(id=e2e_user.id).exists())
        self.assertTrue(User.objects.filter(id=demo_user.id).exists())

    def test_run_id_deletes_only_matching_records(self):
        first = self.create_e2e_user(run_id="run-one")
        second = self.create_e2e_user(run_id="run-two")

        call_command(
            "cleanup_e2e_data",
            "--run-id",
            "run-one",
            "--confirm",
            stdout=StringIO(),
        )

        self.assertFalse(User.objects.filter(id=first.id).exists())
        self.assertTrue(User.objects.filter(id=second.id).exists())

    def test_older_than_days_respects_created_at(self):
        old_user = self.create_e2e_user(run_id="old")
        new_user = self.create_e2e_user(run_id="new")
        User.objects.filter(id=old_user.id).update(
            created_at=timezone.now() - timedelta(days=10)
        )

        call_command(
            "cleanup_e2e_data",
            "--older-than-days",
            "7",
            "--confirm",
            stdout=StringIO(),
        )

        self.assertFalse(User.objects.filter(id=old_user.id).exists())
        self.assertTrue(User.objects.filter(id=new_user.id).exists())

    @override_settings(DEBUG=False)
    def test_production_guard_blocks_confirm_without_allow_production(self):
        user = self.create_e2e_user()

        with self.assertRaises(CommandError):
            call_command("cleanup_e2e_data", "--confirm", stdout=StringIO())

        self.assertTrue(User.objects.filter(id=user.id).exists())

    def test_cleanup_does_not_delete_non_e2e_records(self):
        real_user = User.objects.create_user(
            email="student@example.com",
            password="Password123!",
            full_name="Real Student",
            role=UserRole.STUDENT,
            school=self.school,
        )
        subject = Subject.objects.create(
            school=self.school,
            name="Physics",
            code="PHY",
        )

        call_command("cleanup_e2e_data", "--confirm", stdout=StringIO())

        self.assertTrue(User.objects.filter(id=real_user.id).exists())
        self.assertTrue(Subject.objects.filter(id=subject.id).exists())

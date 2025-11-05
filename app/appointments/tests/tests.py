from users.models import User
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from doctors.models import Doctor
from patients.models import Patient
from appointments.models import Appointment
from appointments.choices import AppointmentType, AppointmentStatus


class AppointmentModelTest(TestCase):
    """Test cases for Appointment model"""

    def setUp(self):
        """Set up test data"""
        # Create users
        self.doctor_user = User.objects.create_user(
            username="doctor1", email="doctor@example.com",
            password="testpass123"
        )
        self.patient_user = User.objects.create_user(
            username="patient1", email="patient@example.com",
            password="testpass123"
        )

        # Create doctor and patient profiles
        self.doctor = Doctor.objects.create(user=self.doctor_user)
        self.patient = Patient.objects.create(user=self.patient_user)

        # Create test appointment
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_type=AppointmentType.CONSULTATION,
            status=AppointmentStatus.SCHEDULED,
            scheduled_start_time=timezone.now() + timedelta(days=1),
            scheduled_end_time=timezone.now() + timedelta(days=1, hours=1),
            reason="Regular checkup",
            created_by=self.patient_user,
        )

    def test_appointment_creation(self):
        """Test that appointment is created correctly"""
        self.assertIsNotNone(self.appointment.id)
        self.assertEqual(self.appointment.patient, self.patient)
        self.assertEqual(self.appointment.doctor, self.doctor)
        self.assertEqual(self.appointment.status, AppointmentStatus.SCHEDULED)

    def test_appointment_str(self):
        """Test string representation"""
        expected = f"{self.patient} - {self.doctor} ({self.appointment.scheduled_start_time.strftime('%Y-%m-%d %H:%M')})"  # noqa
        self.assertEqual(str(self.appointment), expected)

    def test_duration_property(self):
        """Test duration calculation"""
        duration = self.appointment.duration
        self.assertEqual(duration, timedelta(hours=1))

    def test_is_upcoming_property(self):
        """Test is_upcoming property"""
        self.assertTrue(self.appointment.is_upcoming)

    def test_is_past_property(self):
        """Test is_past property"""
        self.assertFalse(self.appointment.is_past)

        # Create past appointment
        past_appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_type=AppointmentType.CONSULTATION,
            scheduled_start_time=timezone.now() - timedelta(days=1),
            scheduled_end_time=timezone.now() - timedelta(days=1, minutes=-30),
            reason="Past checkup",
        )
        self.assertTrue(past_appointment.is_past)

    def test_can_cancel(self):
        """Test can_cancel method"""
        self.assertTrue(self.appointment.can_cancel())

        # Completed appointment cannot be cancelled
        self.appointment.status = AppointmentStatus.COMPLETED
        self.appointment.save()
        self.assertFalse(self.appointment.can_cancel())

    def test_can_reschedule(self):
        """Test can_reschedule method"""
        self.assertTrue(self.appointment.can_reschedule())

        # Cancelled appointment cannot be rescheduled
        self.appointment.status = AppointmentStatus.CANCELLED
        self.appointment.save()
        self.assertFalse(self.appointment.can_reschedule())

    def test_meeting_link_auto_generation(self):
        """Test automatic meeting link generation"""
        self.assertIsNotNone(self.appointment.meeting_link)
        self.assertIn(str(self.appointment.id), self.appointment.meeting_link)


class AppointmentViewSetTest(TestCase):
    """Test cases for Appointment ViewSet"""

    def setUp(self):
        """Set up test data and client"""
        from rest_framework.test import APIClient

        self.client = APIClient()

        # Create users
        self.doctor_user = User.objects.create_user(
            username="doctor1",
            email="doctor@example.com",
            password="testpass123"
        )
        self.patient_user = User.objects.create_user(
            username="patient1",
            email="patient@example.com",
            password="testpass123"
        )

        # Create profiles
        self.doctor = Doctor.objects.create(user=self.doctor_user)
        self.patient = Patient.objects.create(user=self.patient_user)

    def test_list_appointments_authenticated(self):
        """Test listing appointments requires authentication"""
        response = self.client.get("/api/appointments/")
        self.assertEqual(response.status_code, 401)  # Unauthorized

        # Authenticate and try again
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.get("/api/appointments/")
        self.assertEqual(response.status_code, 200)

    def test_create_appointment(self):
        """Test creating an appointment"""
        self.client.force_authenticate(user=self.patient_user)

        data = {
            "patient": self.patient.id,
            "doctor": self.doctor.id,
            "appointment_type": "consultation",
            "scheduled_start_time": (
                timezone.now() + timedelta(days=1)
            ).isoformat(),  # noqa
            "scheduled_end_time": (
                timezone.now() + timedelta(days=1, hours=1)
            ).isoformat(),  # noqa
            "reason": "Test appointment",
            "timezone": "UTC",
        }

        response = self.client.post("/api/appointments/", data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_filter_upcoming_appointments(self):
        """Test filtering upcoming appointments"""
        self.client.force_authenticate(user=self.patient_user)

        # Create appointments
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_type=AppointmentType.CONSULTATION,
            scheduled_start_time=timezone.now() + timedelta(days=1),
            scheduled_end_time=timezone.now() + timedelta(days=1, hours=1),
            reason="Upcoming",
        )

        response = self.client.get("/api/appointments/upcoming/")
        self.assertEqual(response.status_code, 200)

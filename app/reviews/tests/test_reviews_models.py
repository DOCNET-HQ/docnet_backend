from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from reviews.models import DoctorReview, HospitalReview
from doctors.models import Doctor
from hospitals.models import Hospital

User = get_user_model()


class ReviewBaseModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            email="doctor@example.com", password="testpass123"
        )
        self.user3 = User.objects.create_user(
            email="hospital@example.com", password="testpass123"
        )
        self.doctor = Doctor.objects.create(
            user=self.user2, name="Dr. Test Doctor", specialty="Cardiology"
        )
        self.hospital = Hospital.objects.create(
            user=self.user3, name="Test Hospital", address="123 Test St"
        )

    def test_create_doctor_review(self):
        review = DoctorReview.objects.create(
            user=self.user, doctor=self.doctor, rating=5, text="Excellent doctor!"
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.text, "Excellent doctor!")
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.doctor, self.doctor)

    def test_create_hospital_review(self):
        review = HospitalReview.objects.create(
            user=self.user, hospital=self.hospital, rating=4, text="Good hospital!"
        )
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.text, "Good hospital!")
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.hospital, self.hospital)

    def test_rating_validation(self):
        with self.assertRaises(ValidationError):
            review = DoctorReview(
                user=self.user,
                doctor=self.doctor,
                rating=6,  # Invalid rating
                text="Test",
            )
            review.full_clean()

    def test_unique_together_doctor_review(self):
        DoctorReview.objects.create(
            user=self.user, doctor=self.doctor, rating=5, text="First review"
        )

        with self.assertRaises(Exception):  # IntegrityError
            DoctorReview.objects.create(
                user=self.user, doctor=self.doctor, rating=4, text="Second review"
            )

    def test_unique_together_hospital_review(self):
        HospitalReview.objects.create(
            user=self.user, hospital=self.hospital, rating=5, text="First review"
        )

        with self.assertRaises(Exception):  # IntegrityError
            HospitalReview.objects.create(
                user=self.user, hospital=self.hospital, rating=4, text="Second review"
            )

    def test_is_updated_property(self):
        review = DoctorReview.objects.create(
            user=self.user, doctor=self.doctor, rating=5, text="Test review"
        )
        # Initially should be False
        self.assertFalse(review.is_updated)

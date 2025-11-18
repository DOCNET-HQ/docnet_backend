from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from reviews.models import DoctorReview, HospitalReview
from doctors.models import Doctor
from hospitals.models import Hospital

User = get_user_model()


class ReviewAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            email="other@example.com", password="testpass123"
        )
        self.doctor = Doctor.objects.create(
            name="Dr. Test Doctor", specialization="Cardiology"
        )
        self.hospital = Hospital.objects.create(
            name="Test Hospital", address="123 Test St"
        )

        # Create some test reviews
        self.doctor_review = DoctorReview.objects.create(
            user=self.user,
            doctor=self.doctor,
            rating=5,
            text="Excellent doctor from auth user",
        )
        self.other_doctor_review = DoctorReview.objects.create(
            user=self.other_user,
            doctor=self.doctor,
            rating=4,
            text="Good doctor from other user",
        )

        self.hospital_review = HospitalReview.objects.create(
            user=self.user,
            hospital=self.hospital,
            rating=4,
            text="Good hospital from auth user",
        )
        self.other_hospital_review = HospitalReview.objects.create(
            user=self.other_user,
            hospital=self.hospital,
            rating=3,
            text="Okay hospital from other user",
        )


class HasReviewedAPITests(ReviewAPITestCase):
    def test_has_reviewed_doctor_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f"/api/reviews/doctors/{self.doctor.id}/has-reviewed/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["has_reviewed"])

    def test_has_reviewed_doctor_not_authenticated(self):
        response = self.client.get(
            f"/api/reviews/doctors/{self.doctor.id}/has-reviewed/"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_has_reviewed_hospital_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f"/api/reviews/hospitals/{self.hospital.id}/has-reviewed/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["has_reviewed"])


class DoctorReviewAPITests(ReviewAPITestCase):
    def test_list_doctor_reviews_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/reviews/doctors/{self.doctor.id}/reviews/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Auth user's review should come first
        self.assertTrue(response.data[0]["is_auth_user"])
        self.assertFalse(response.data[1]["is_auth_user"])

    def test_create_doctor_review_authenticated(self):
        self.client.force_authenticate(user=self.other_user)
        new_doctor = Doctor.objects.create(name="Dr. New", specialization="Dermatology")

        data = {"doctor": new_doctor.id, "rating": 5, "text": "Amazing doctor!"}

        response = self.client.post(
            f"/api/reviews/doctors/{new_doctor.id}/reviews/", data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DoctorReview.objects.count(), 3)

    def test_create_doctor_review_duplicate(self):
        self.client.force_authenticate(user=self.user)

        data = {"doctor": self.doctor.id, "rating": 3, "text": "Another review"}

        response = self.client.post(
            f"/api/reviews/doctors/{self.doctor.id}/reviews/", data
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class HospitalReviewAPITests(ReviewAPITestCase):
    def test_list_hospital_reviews_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f"/api/reviews/hospitals/{self.hospital.id}/reviews/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Auth user's review should come first
        self.assertTrue(response.data[0]["is_auth_user"])
        self.assertFalse(response.data[1]["is_auth_user"])

    def test_update_doctor_review_owner(self):
        self.client.force_authenticate(user=self.user)

        data = {"rating": 4, "text": "Updated review text"}

        response = self.client.patch(
            f"/api/reviews/doctor-reviews/{self.doctor_review.id}/", data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.doctor_review.refresh_from_db()
        self.assertEqual(self.doctor_review.rating, 4)
        self.assertEqual(self.doctor_review.text, "Updated review text")
        self.assertTrue(self.doctor_review.is_updated)


class ReviewDetailAPITests(ReviewAPITestCase):
    def test_retrieve_doctor_review(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f"/api/reviews/doctor-reviews/{self.doctor_review.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.doctor_review.id)
        self.assertTrue(response.data["is_auth_user"])
        self.assertIn("is_updated", response.data)

    def test_delete_doctor_review_owner(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            f"/api/reviews/doctor-reviews/{self.doctor_review.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DoctorReview.objects.filter(id=self.doctor_review.id).exists())

    def test_delete_doctor_review_non_owner(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(
            f"/api/reviews/doctor-reviews/{self.doctor_review.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


class AccountViewTests(APITestCase):
    def test_register_returns_created_user(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "testpass123",
                "role": "customer",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["username"], "newuser")

    def test_register_rejects_duplicate_email_case_insensitively(self):
        User = get_user_model()
        User.objects.create_user(
            username="existinguser",
            email="deepa@example.com",
            password="testpass123",
        )

        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "anotheruser",
                "email": "Deepa@Example.com",
                "password": "testpass123",
                "role": "customer",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_register_rejects_duplicate_username_case_insensitively(self):
        User = get_user_model()
        User.objects.create_user(
            username="Hari",
            email="hari@example.com",
            password="testpass123",
        )

        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "hari",
                "email": "anotherhari@example.com",
                "password": "testpass123",
                "role": "customer",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_login_accepts_username_case_insensitively(self):
        User = get_user_model()
        User.objects.create_user(
            username="Hari",
            email="hari@example.com",
            password="testpass123",
        )

        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "hari",
                "password": "testpass123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_me_returns_authenticated_user(self):
        user = get_user_model().objects.create_user(
            username="deepa",
            email="deepa@example.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], user.id)
        self.assertEqual(response.data["username"], "deepa")

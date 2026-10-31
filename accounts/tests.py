from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Profile


class AccountsAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='ValidPassword123!'
        )

    def test_profile_auto_created_signal(self):
        """Verify Profile is automatically created on User creation."""
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_user_registration_success(self):
        """Verify new user registration creates user and auto-logs in."""
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newbuyer',
            'email': 'newbuyer@example.com',
            'password': 'StrongPassword789!',
            'password_confirm': 'StrongPassword789!',
        })
        self.assertEqual(response.status_code, 302)  # Redirects to profile
        self.assertTrue(User.objects.filter(username='newbuyer').exists())
        self.assertTrue(Profile.objects.filter(user__username='newbuyer').exists())

    def test_user_registration_password_mismatch(self):
        """Verify registration rejects mismatched passwords."""
        response = self.client.post(reverse('accounts:register'), {
            'username': 'mismatchuser',
            'email': 'mismatch@example.com',
            'password': 'StrongPassword789!',
            'password_confirm': 'DifferentPassword789!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='mismatchuser').exists())
        self.assertContains(response, "Passwords do not match.")

    def test_user_registration_duplicate_email(self):
        """Verify registration rejects duplicate email."""
        response = self.client.post(reverse('accounts:register'), {
            'username': 'anotheruser',
            'email': 'test@example.com',  # already taken by self.user
            'password': 'StrongPassword789!',
            'password_confirm': 'StrongPassword789!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='anotheruser').exists())
        self.assertContains(response, "An account with this email address already exists.")

    def test_login_success_and_logout(self):
        """Verify valid login and logout flow."""
        login_res = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'ValidPassword123!',
        })
        self.assertEqual(login_res.status_code, 302)

        # Profile accessible while logged in
        profile_res = self.client.get(reverse('accounts:profile'))
        self.assertEqual(profile_res.status_code, 200)
        self.assertContains(profile_res, "testuser")

        # Logout
        logout_res = self.client.get(reverse('accounts:logout'))
        self.assertEqual(logout_res.status_code, 302)

    def test_login_invalid_credentials(self):
        """Verify rejection of incorrect password."""
        res = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'WrongPassword!',
        })
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Invalid username or password.")

    def test_profile_edit(self):
        """Verify updating profile contact and address fields."""
        self.client.login(username='testuser', password='ValidPassword123!')
        res = self.client.post(reverse('accounts:profile_edit'), {
            'first_name': 'Aarav',
            'last_name': 'Sharma',
            'email': 'aarav.sharma@example.com',
            'phone': '9876543210',
            'address': 'Flat 402, Lotus Enclave, Indiranagar',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'pincode': '560038',
        })
        self.assertEqual(res.status_code, 302)

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Aarav')
        self.assertEqual(self.user.email, 'aarav.sharma@example.com')
        self.assertEqual(self.user.profile.city, 'Bengaluru')
        self.assertEqual(self.user.profile.pincode, '560038')

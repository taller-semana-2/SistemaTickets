"""
Tests for HttpOnly cookie authentication (BUG-003).

Verifies that:
- Login and register set HttpOnly cookies instead of returning tokens in body
- /api/auth/me/ works with cookie-based auth
- /api/auth/logout/ clears cookies
- /api/auth/refresh/ reads refresh token from cookie
"""

import pytest
from django.test import TestCase, Client
from users.models import User
import hashlib


@pytest.mark.django_db
class TestLoginCookies(TestCase):
    """Verify that login sets HttpOnly cookies and does not return tokens in body."""

    def setUp(self):
        """Create a test user."""
        self.client = Client()
        self.password = 'testpassword123'
        self.password_hash = hashlib.sha256(self.password.encode()).hexdigest()
        self.user = User.objects.create(
            email='test@example.com',
            username='testuser',
            password_hash=self.password_hash,
            role='USER',
            is_active=True,
        )

    def test_login_sets_httponly_cookies(self):
        """POST /api/auth/login/ should set access_token and refresh_token as HttpOnly cookies."""
        response = self.client.post(
            '/api/auth/login/',
            data={'email': 'test@example.com', 'password': self.password},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)

        # Verify cookies are set
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

        # Verify HttpOnly flag
        access_cookie = response.cookies['access_token']
        refresh_cookie = response.cookies['refresh_token']
        self.assertTrue(access_cookie['httponly'])
        self.assertTrue(refresh_cookie['httponly'])

    def test_login_response_body_has_no_tokens(self):
        """Login response body should contain user data but NO tokens."""
        response = self.client.post(
            '/api/auth/login/',
            data={'email': 'test@example.com', 'password': self.password},
            content_type='application/json',
        )
        data = response.json()

        # Body should have user
        self.assertIn('user', data)
        self.assertEqual(data['user']['email'], 'test@example.com')

        # Body should NOT have tokens
        self.assertNotIn('tokens', data)
        self.assertNotIn('access', data)
        self.assertNotIn('refresh', data)

    def test_login_invalid_credentials_returns_401(self):
        """Login with wrong password should return 401 and NO cookies."""
        response = self.client.post(
            '/api/auth/login/',
            data={'email': 'test@example.com', 'password': 'wrongpassword'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)
        self.assertNotIn('access_token', response.cookies)


@pytest.mark.django_db
class TestRegisterCookies(TestCase):
    """Verify that register sets HttpOnly cookies."""

    def setUp(self):
        self.client = Client()

    def test_register_sets_httponly_cookies(self):
        """POST /api/auth/ (register) should set HttpOnly cookies."""
        response = self.client.post(
            '/api/auth/',
            data={
                'email': 'newuser@example.com',
                'username': 'newuser',
                'password': 'securepass123',
            },
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)

        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)
        self.assertTrue(response.cookies['access_token']['httponly'])
        self.assertTrue(response.cookies['refresh_token']['httponly'])

    def test_register_response_body_has_no_tokens(self):
        """Register response body should contain user but NO tokens."""
        response = self.client.post(
            '/api/auth/',
            data={
                'email': 'newuser2@example.com',
                'username': 'newuser2',
                'password': 'securepass123',
            },
            content_type='application/json',
        )
        data = response.json()

        self.assertIn('user', data)
        self.assertNotIn('tokens', data)


@pytest.mark.django_db
class TestMeEndpoint(TestCase):
    """Verify endpoint /api/auth/me/."""

    def setUp(self):
        self.client = Client()
        self.password = 'testpassword123'
        self.password_hash = hashlib.sha256(self.password.encode()).hexdigest()
        self.user = User.objects.create(
            email='me@example.com',
            username='meuser',
            password_hash=self.password_hash,
            role='USER',
            is_active=True,
        )

    def test_me_with_valid_cookie_returns_user(self):
        """GET /api/auth/me/ with valid access_token cookie should return user data."""
        # First login to get cookies
        login_response = self.client.post(
            '/api/auth/login/',
            data={'email': 'me@example.com', 'password': self.password},
            content_type='application/json',
        )
        self.assertEqual(login_response.status_code, 200)

        # Now call /me/ — Django test client carries cookies automatically
        me_response = self.client.get('/api/auth/me/')
        self.assertEqual(me_response.status_code, 200)

        data = me_response.json()
        self.assertEqual(data['email'], 'me@example.com')
        self.assertEqual(data['username'], 'meuser')

    def test_me_without_cookie_returns_401(self):
        """GET /api/auth/me/ without cookie should return 401."""
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 401)


@pytest.mark.django_db
class TestLogoutEndpoint(TestCase):
    """Verify endpoint /api/auth/logout/."""

    def setUp(self):
        self.client = Client()

    def test_logout_clears_cookies(self):
        """POST /api/auth/logout/ should clear auth cookies."""
        response = self.client.post('/api/auth/logout/')
        self.assertEqual(response.status_code, 200)

        # Verify cookies are deleted (max-age=0)
        if 'access_token' in response.cookies:
            access_cookie = response.cookies['access_token']
            self.assertEqual(access_cookie['max-age'], 0)
        if 'refresh_token' in response.cookies:
            refresh_cookie = response.cookies['refresh_token']
            self.assertEqual(refresh_cookie['max-age'], 0)

    def test_logout_returns_confirmation(self):
        """POST /api/auth/logout/ should return confirmation message."""
        response = self.client.post('/api/auth/logout/')
        data = response.json()
        self.assertIn('detail', data)


@pytest.mark.django_db
class TestCookieRefresh(TestCase):
    """Verify refresh via cookie."""

    def setUp(self):
        self.client = Client()
        self.password = 'testpassword123'
        self.password_hash = hashlib.sha256(self.password.encode()).hexdigest()
        self.user = User.objects.create(
            email='refresh@example.com',
            username='refreshuser',
            password_hash=self.password_hash,
            role='USER',
            is_active=True,
        )

    def test_refresh_reads_cookie_and_sets_new_cookies(self):
        """POST /api/auth/refresh/ should read refresh cookie and set new cookies."""
        # Login first
        login_response = self.client.post(
            '/api/auth/login/',
            data={'email': 'refresh@example.com', 'password': self.password},
            content_type='application/json',
        )
        self.assertEqual(login_response.status_code, 200)

        # Now refresh — client carries cookies
        refresh_response = self.client.post('/api/auth/refresh/')
        self.assertEqual(refresh_response.status_code, 200)

        # New cookies should be set
        self.assertIn('access_token', refresh_response.cookies)

    def test_refresh_without_cookie_returns_401(self):
        """POST /api/auth/refresh/ without refresh_token cookie should return 401."""
        # Fresh client — no cookies
        fresh_client = Client()
        response = fresh_client.post('/api/auth/refresh/')
        self.assertEqual(response.status_code, 401)

from django.test import TestCase, Client
from django.urls import reverse
from .models import URL
import json


class CreateShortURLViewTests(TestCase):
    """Tests for the create_short_url view."""
    
    def setUp(self):
        """Set up test client and common test data."""
        self.client = Client()
        self.url = '/v1/urls/'
        self.valid_url = 'https://www.example.com/some/long/path'
    
    def test_create_short_url_success(self):
        """Test successful creation of a short URL."""
        response = self.client.post(
            self.url,
            data=json.dumps({'url': self.valid_url}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        
        # Check response structure
        self.assertIn('short_code', data)
        self.assertIn('short_url', data)
        self.assertIn('original_url', data)
        self.assertIn('created_at', data)

        # Check values
        self.assertEqual(data['original_url'], self.valid_url)
        max_len = URL._meta.get_field('short_code').max_length
        self.assertTrue(0 < len(data['short_code']) <= max_len)
        
        # Verify URL was created in database
        url_obj = URL.objects.get(short_code=data['short_code'])
        self.assertEqual(url_obj.original_url, self.valid_url)
        self.assertEqual(url_obj.clicks, 0)
        self.assertTrue(url_obj.is_active)
    
    def test_create_duplicate_url_returns_existing(self):
        """Test that creating a duplicate URL returns the existing short code."""
        # Create first URL
        response1 = self.client.post(
            self.url,
            data=json.dumps({'url': self.valid_url}),
            content_type='application/json'
        )
        self.assertEqual(response1.status_code, 201)
        data1 = response1.json()
        
        # Try to create the same URL again
        response2 = self.client.post(
            self.url,
            data=json.dumps({'url': self.valid_url}),
            content_type='application/json'
        )
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        
        # Should return the same short code
        self.assertEqual(data1['short_code'], data2['short_code'])
        self.assertIn('message', data2)
        self.assertEqual(data2['message'], 'URL already exists')
        
        # Verify only one URL object exists
        self.assertEqual(URL.objects.filter(original_url=self.valid_url).count(), 1)
    
    def test_create_short_url_missing_url_parameter(self):
        """Test error when URL parameter is missing."""
        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'URL is required')
    
    def test_create_short_url_empty_url(self):
        """Test error when URL parameter is empty."""
        response = self.client.post(
            self.url,
            data=json.dumps({'url': ''}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
    
    def test_create_short_url_invalid_json(self):
        """Test error when request body is invalid JSON."""
        response = self.client.post(
            self.url,
            data='invalid json{',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid JSON')
    
    def test_create_short_url_get_method_not_allowed(self):
        """Test that GET method is not allowed."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
    
    def test_inactive_url_not_returned_for_duplicate(self):
        """Test that inactive URLs are not returned when checking for duplicates."""
        # Create and deactivate a URL
        url_obj = URL.objects.create(original_url=self.valid_url, is_active=False)
        
        # Create the same URL again
        response = self.client.post(
            self.url,
            data=json.dumps({'url': self.valid_url}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        
        # Should create a new URL, not return the inactive one
        self.assertNotEqual(data['short_code'], url_obj.short_code)
        self.assertEqual(URL.objects.filter(original_url=self.valid_url).count(), 2)


class RedirectToOriginalViewTests(TestCase):
    """Tests for the redirect_to_original view."""
    
    def setUp(self):
        """Set up test client and test URLs."""
        self.client = Client()
        self.original_url = 'https://www.example.com/test'
        self.url_obj = URL.objects.create(original_url=self.original_url)
        self.short_code = self.url_obj.short_code
    
    def test_redirect_success(self):
        """Test successful redirect to original URL."""
        response = self.client.get(f'/v1/urls/{self.short_code}/')
        
        # Check redirect
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.original_url)
        
        # Verify click counter was incremented
        self.url_obj.refresh_from_db()
        self.assertEqual(self.url_obj.clicks, 1)
    
    def test_redirect_increments_clicks(self):
        """Test that multiple redirects increment the click counter."""
        initial_clicks = self.url_obj.clicks
        
        # Make multiple requests
        for i in range(5):
            response = self.client.get(f'/v1/urls/{self.short_code}/')
            self.assertEqual(response.status_code, 302)
        
        # Verify clicks were incremented correctly
        self.url_obj.refresh_from_db()
        self.assertEqual(self.url_obj.clicks, initial_clicks + 5)
    
    def test_redirect_nonexistent_short_code(self):
        """Test 404 error when short code doesn't exist."""
        response = self.client.get('/v1/urls/nonexistent/')
        self.assertEqual(response.status_code, 404)
    
    def test_redirect_inactive_url(self):
        """Test 404 error when URL is inactive."""
        # Deactivate the URL
        self.url_obj.is_active = False
        self.url_obj.save()
        
        response = self.client.get(f'/v1/urls/{self.short_code}/')
        self.assertEqual(response.status_code, 404)
    
    def test_redirect_post_method_not_allowed(self):
        """Test that POST method is not allowed."""
        response = self.client.post(f'/v1/urls/{self.short_code}/')
        self.assertEqual(response.status_code, 405)
    
    def test_redirect_preserves_original_url_format(self):
        """Test that the original URL format is preserved in redirect."""
        # Test with URL containing query parameters and fragments
        complex_url = 'https://example.com/path?param=value&other=123#section'
        url_obj = URL.objects.create(original_url=complex_url)
        
        response = self.client.get(f'/v1/urls/{url_obj.short_code}/')
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, complex_url)


class URLModelIntegrationTests(TestCase):
    """Integration tests combining model and views."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    def test_end_to_end_workflow(self):
        """Test complete workflow: create short URL and use it for redirect."""
        original_url = 'https://www.example.com/complete-workflow'
        
        # Step 1: Create short URL
        create_response = self.client.post(
            '/v1/urls/',
            data=json.dumps({'url': original_url}),
            content_type='application/json'
        )
        self.assertEqual(create_response.status_code, 201)
        short_code = create_response.json()['short_code']
        
        # Step 2: Use short URL to redirect
        redirect_response = self.client.get(f'/v1/urls/{short_code}/')
        self.assertEqual(redirect_response.status_code, 302)
        self.assertEqual(redirect_response.url, original_url)
        
        # Step 3: Verify click was tracked
        url_obj = URL.objects.get(short_code=short_code)
        self.assertEqual(url_obj.clicks, 1)
    
    def test_multiple_urls_different_short_codes(self):
        """Test that different URLs get different short codes."""
        urls = [
            'https://example1.com',
            'https://example2.com',
            'https://example3.com',
        ]
        
        short_codes = []
        for url in urls:
            response = self.client.post(
                '/v1/urls/',
                data=json.dumps({'url': url}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 201)
            short_codes.append(response.json()['short_code'])
        
        # Verify all short codes are unique
        self.assertEqual(len(short_codes), len(set(short_codes)))
        
        # Verify each short code redirects to correct URL
        for url, short_code in zip(urls, short_codes):
            response = self.client.get(f'/v1/urls/{short_code}/')
            self.assertEqual(response.url, url)

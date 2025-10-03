from django.test import TestCase
from django.contrib.auth.models import User
from .models import Message, Notification
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

class MessageModelTest(TestCase):
    def setUp(self):
        """Set up test users and data"""
        self.sender = User.objects.create_user(
            username='sender', 
            email='sender@example.com', 
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver', 
            email='receiver@example.com', 
            password='testpass123'
        )
    
    def test_message_creation(self):
        """Test creating a message"""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            subject='Test Subject',
            content='This is a test message content.'
        )
        
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.receiver, self.receiver)
        self.assertEqual(message.subject, 'Test Subject')
        self.assertFalse(message.is_read)
        self.assertIsNotNone(message.timestamp)
    
    def test_message_str_representation(self):
        """Test the string representation of Message model"""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            subject='Test Subject',
            content='Test content'
        )
        
        expected_str = f"{self.sender} to {self.receiver}: Test Subject"
        self.assertEqual(str(message), expected_str)

class NotificationSignalTest(TestCase):
    def setUp(self):
        """Set up test users"""
        self.sender = User.objects.create_user(
            username='sender', 
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver', 
            password='testpass123'
        )
    
    def test_notification_created_on_message_save(self):
        """Test that a notification is automatically created when a message is created"""
        # Count initial notifications
        initial_notification_count = Notification.objects.count()
        
        # Create a new message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            subject='Test Notification',
            content='This should trigger a notification.'
        )
        
        # Check that a notification was created
        final_notification_count = Notification.objects.count()
        self.assertEqual(final_notification_count, initial_notification_count + 1)
        
        # Verify notification details
        notification = Notification.objects.first()
        self.assertEqual(notification.user, self.receiver)
        self.assertEqual(notification.message, message)
        self.assertEqual(notification.notification_type, 'message')
        self.assertIn(self.sender.username, notification.title)
        self.assertIn(message.subject, notification.message_preview)
        self.assertFalse(notification.is_read)
    
    def test_no_notification_on_message_update(self):
        """Test that notifications are not created when existing messages are updated"""
        # Create a message (this should create one notification)
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            subject='Original Subject',
            content='Original content'
        )
        
        initial_notification_count = Notification.objects.count()
        
        # Update the message
        message.subject = 'Updated Subject'
        message.is_read = True
        message.save()
        
        # Check that no new notification was created
        final_notification_count = Notification.objects.count()
        self.assertEqual(final_notification_count, initial_notification_count)

class NotificationModelTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123'
        )
        self.sender = User.objects.create_user(
            username='sender', 
            password='testpass123'
        )
        
        self.message = Message.objects.create(
            sender=self.sender,
            receiver=self.user,
            subject='Test Message',
            content='Test content for notification'
        )
    
    def test_notification_creation(self):
        """Test creating a notification"""
        notification = Notification.objects.create(
            user=self.user,
            message=self.message,
            notification_type='message',
            title='Test Notification',
            message_preview='This is a test notification preview'
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.message, self.message)
        self.assertEqual(notification.notification_type, 'message')
        self.assertFalse(notification.is_read)
        self.assertIsNotNone(notification.created_at)
    
    def test_notification_str_representation(self):
        """Test the string representation of Notification model"""
        notification = Notification.objects.create(
            user=self.user,
            message=self.message,
            title='Test Notification Title'
        )

        class CacheTest(TestCase):
    def setUp(self):
        """Set up test user and client"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        # Clear cache before each test
        cache.clear()

    def test_conversation_list_cache(self):
        """Test that conversation list view is cached"""
        self.client.login(username='testuser', password='testpass123')
        
        # First request - should not be cached
        response1 = self.client.get(reverse('messaging:conversation_list'))
        self.assertEqual(response1.status_code, 200)
        
        # Check for cache indicator in response
        self.assertContains(response1, 'CACHED')
        
        # Second request - should be served from cache
        response2 = self.client.get(reverse('messaging:conversation_list'))
        self.assertEqual(response2.status_code, 200)
        
        # Both responses should have the same content (cached)
        self.assertEqual(response1.content, response2.content)

    def test_cache_timeout(self):
        """Test that cache expires after timeout"""
        self.client.login(username='testuser', password='testpass123')
        
        # First request
        response1 = self.client.get(reverse('messaging:conversation_list'))
        
        # Clear cache to simulate timeout
        cache.clear()
        
        # Second request after cache clear
        response2 = self.client.get(reverse('messaging:conversation_list'))
        
        # Responses should be different after cache clear
        # Note: The cached_at timestamp will be different
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)

    def test_cache_per_user(self):
        """Test that cache is user-specific"""
        user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )
        
        # Login as first user
        self.client.login(username='testuser', password='testpass123')
        response1 = self.client.get(reverse('messaging:conversation_list'))
        
        # Login as second user
        self.client.login(username='testuser2', password='testpass123')
        response2 = self.client.get(reverse('messaging:conversation_list'))
        
        # Responses should be different for different users
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        # The content should be different because of vary_on_cookie

    def test_non_cached_views(self):
        """Test that action views are not cached"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test API endpoint (should not be cached)
        response = self.client.get(reverse('messaging:unread_messages_api'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['cached'])
        
        # Test form view (should not be cached)
        response = self.client.get(reverse('messaging:create_reply', args=[1]))
        self.assertNotEqual(response.status_code, 200)  # 404 or other

    def test_cache_clear_view(self):
        """Test cache clearing view"""
        # Create superuser
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass'
        )
        
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('messaging:clear_cache'))
        
        # Should redirect to conversation list
        self.assertEqual(response.status_code, 302)

    def test_cache_stats_view(self):
        """Test cache stats view"""
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass'
        )
        
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('messaging:cache_stats'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('backend', data)
        
        expected_str = f"Notification for {self.user.username}: Test Notification Title"
        self.assertEqual(str(notification), expected_str)

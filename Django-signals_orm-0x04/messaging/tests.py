from django.test import TestCase
from django.contrib.auth.models import User
from .models import Message, Notification

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
        
        expected_str = f"Notification for {self.user.username}: Test Notification Title"
        self.assertEqual(str(notification), expected_str)

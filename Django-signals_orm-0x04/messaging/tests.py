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
  class MessageEditHistoryTest(TestCase):
    def setUp(self):
        """Set up test users and message"""
        self.sender = User.objects.create_user(
            username='sender', 
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver', 
            password='testpass123'
        )
        
        # Create initial message
        self.message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            subject='Original Subject',
            content='Original content of the message.'
        )

    def test_message_edit_history_creation(self):
        """Test that message edits create history entries"""
        # Count initial history entries
        initial_history_count = MessageHistory.objects.count()
        
        # Update the message
        self.message.subject = 'Updated Subject'
        self.message.content = 'Updated content of the message.'
        self.message.save()
        
        # Check that a history entry was created
        final_history_count = MessageHistory.objects.count()
        self.assertEqual(final_history_count, initial_history_count + 1)
        
        # Verify history entry details
        history_entry = MessageHistory.objects.first()
        self.assertEqual(history_entry.message, self.message)
        self.assertEqual(history_entry.old_subject, 'Original Subject')
        self.assertEqual(history_entry.old_content, 'Original content of the message.')
        self.assertEqual(history_entry.edited_by, self.sender)

    def test_no_history_on_first_save(self):
        """Test that no history is created for new messages"""
        initial_history_count = MessageHistory.objects.count()
        
        # Create a new message
        new_message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            subject='New Message',
            content='New content'
        )
        
        # Check that no history was created
        final_history_count = MessageHistory.objects.count()
        self.assertEqual(final_history_count, initial_history_count)

    def test_edited_field_updates(self):
        """Test that edited field is updated when message is modified"""
        self.assertFalse(self.message.edited)
        self.assertIsNone(self.message.last_edited)
        
        # Update the message
        self.message.content = 'Modified content'
        self.message.save()
        
        # Refresh from database
        self.message.refresh_from_db()
        
        self.assertTrue(self.message.edited)
        self.assertIsNotNone(self.message.last_edited)

    def test_multiple_edits_create_multiple_history_entries(self):
        """Test that multiple edits create multiple history entries"""
        # First edit
        self.message.subject = 'First Edit'
        self.message.save()
        
        # Second edit
        self.message.content = 'Second edit content'
        self.message.save()
        
        # Third edit
        self.message.subject = 'Third Edit'
        self.message.save()
        
        # Should have 3 history entries
        self.assertEqual(MessageHistory.objects.count(), 3)
        
        # Verify the history entries are in correct order
        history_entries = MessageHistory.objects.all().order_by('edited_at')
        self.assertEqual(history_entries[0].old_subject, 'Original Subject')
        self.assertEqual(history_entries[1].old_subject, 'First Edit')
        self.assertEqual(history_entries[2].old_subject, 'Second edit content')

class MessageHistoryModelTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123'
        )
        self.message = Message.objects.create(
            sender=self.user,
            receiver=self.user,  # Sending to self for simplicity
            subject='Test Message',
            content='Test content'
        )

    def test_message_history_creation(self):
        """Test creating a message history entry"""
        history = MessageHistory.objects.create(
            message=self.message,
            old_subject='Old Subject',
            old_content='Old content that was changed',
            edited_by=self.user
        )
        
        self.assertEqual(history.message, self.message)
        self.assertEqual(history.old_subject, 'Old Subject')
        self.assertEqual(history.old_content, 'Old content that was changed')
        self.assertEqual(history.edited_by, self.user)
        self.assertIsNotNone(history.edited_at)

    def test_message_history_str_representation(self):
        """Test the string representation of MessageHistory model"""
        history = MessageHistory.objects.create(
            message=self.message,
            old_subject='Old Subject',
            old_content='Old content',
            edited_by=self.user
        )
        
        expected_str = f"History for {self.message.subject} (edited at {history.edited_at})"
        self.assertEqual(str(history), expected_str)      
        expected_str = f"Notification for {self.user.username}: Test Notification Title"
        self.assertEqual(str(notification), expected_str)

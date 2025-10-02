from django.test import TestCase
from django.contrib.auth.models import User
from .models import Message, Notification
from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model


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


class UserDeletionTest(TestCase):
    def setUp(self):
        """Set up test users and data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Create test data for the user
        self.message_sent = Message.objects.create(
            sender=self.user,
            receiver=self.other_user,
            subject='Test Sent Message',
            content='This is a sent message'
        )
        
        self.message_received = Message.objects.create(
            sender=self.other_user,
            receiver=self.user,
            subject='Test Received Message',
            content='This is a received message'
        )
        
        self.notification = Notification.objects.create(
            user=self.user,
            message=self.message_received,
            title='Test Notification',
            message_preview='Test preview'
        )
        
        self.message_history = MessageHistory.objects.create(
            message=self.message_sent,
            old_subject='Old Subject',
            old_content='Old content',
            edited_by=self.user
        )

    def test_delete_account_confirmation_view(self):
        """Test the account deletion confirmation page"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('messaging:delete_account_confirmation'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'messaging/delete_account_confirmation.html')
        self.assertContains(response, 'Delete Your Account')
        self.assertContains(response, str(self.user.username))

    def test_delete_account_view_post(self):
        """Test account deletion via POST request"""
        self.client.login(username='testuser', password='testpass123')
        
        # Count data before deletion
        user_count_before = User.objects.count()
        sent_messages_before = Message.objects.filter(sender=self.user).count()
        received_messages_before = Message.objects.filter(receiver=self.user).count()
        
        # Delete account
        response = self.client.post(reverse('messaging:delete_account'), {
            'confirm_username': 'testuser'
        }, follow=True)
        
        # Check that user was deleted
        user_count_after = User.objects.count()
        self.assertEqual(user_count_after, user_count_before - 1)
        
        # Check that user no longer exists
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username='testuser')
        
        # Check redirect and message
        self.assertRedirects(response, reverse('home'))
        self.assertContains(response, 'successfully deleted')

    def test_delete_account_invalid_confirmation(self):
        """Test account deletion with invalid username confirmation"""
        self.client.login(username='testuser', password='testpass123')
        
        user_count_before = User.objects.count()
        
        # Try to delete with wrong username
        response = self.client.post(reverse('messaging:delete_account'), {
            'confirm_username': 'wrongusername'
        })
        
        # User should not be deleted
        user_count_after = User.objects.count()
        self.assertEqual(user_count_after, user_count_before)
        
        # Should redirect back to confirmation
        self.assertEqual(response.status_code, 302)

    def test_user_data_cleanup_signal(self):
        """Test that user data is cleaned up when user is deleted"""
        # Count related data
        sent_messages_before = Message.objects.filter(sender=self.user).count()
        received_messages_before = Message.objects.filter(receiver=self.user).count()
        notifications_before = Notification.objects.filter(user=self.user).count()
        history_before = MessageHistory.objects.filter(edited_by=self.user).count()
        
        # Verify data exists
        self.assertGreater(sent_messages_before, 0)
        self.assertGreater(received_messages_before, 0)
        self.assertGreater(notifications_before, 0)
        self.assertGreater(history_before, 0)
        
        # Delete user
        self.user.delete()
        
        # Check that related data is cleaned up
        sent_messages_after = Message.objects.filter(sender__username='testuser').count()
        received_messages_after = Message.objects.filter(receiver__username='testuser').count()
        notifications_after = Notification.objects.filter(user__username='testuser').count()
        history_after = MessageHistory.objects.filter(edited_by__username='testuser').count()
        
        self.assertEqual(sent_messages_after, 0)
        self.assertEqual(received_messages_after, 0)
        self.assertEqual(notifications_after, 0)
        self.assertEqual(history_after, 0)

    def test_user_data_summary_api(self):
        """Test the user data summary API endpoint"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('messaging:user_data_summary'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('sent_messages', data)
        self.assertIn('received_messages', data)
        self.assertIn('notifications', data)
        self.assertIn('edit_history', data)
        
        self.assertEqual(data['sent_messages'], 1)
        self.assertEqual(data['received_messages'], 1)
        self.assertEqual(data['notifications'], 1)
        self.assertEqual(data['edit_history'], 1)

    def test_delete_account_requires_login(self):
        """Test that account deletion requires authentication"""
        # Try to access without login
        response = self.client.get(reverse('messaging:delete_account_confirmation'))
        self.assertNotEqual(response.status_code, 200)  # Should redirect to login
        
        response = self.client.post(reverse('messaging:delete_account'))
        self.assertNotEqual(response.status_code, 200)  # Should redirect to login

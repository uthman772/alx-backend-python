from rest_framework import serializers
from .models import User, Conversation, ConversationParticipant, Message

class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model"""
    
    class Meta:
        model = User
        fields = [
            'user_id', 
            'first_name', 
            'last_name', 
            'email', 
            'phone_number', 
            'role', 
            'created_at'
        ]
        read_only_fields = ['user_id', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def create(self, validated_data):
        """Create a new user with encrypted password"""
        password = validated_data.pop('password', None)
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        """Update a user, setting the password correctly if provided"""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        return user

class MessageSerializer(serializers.ModelSerializer):
    """Serializer for the Message model"""
    
    sender = UserSerializer(read_only=True)
    sender_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='sender', 
        write_only=True
    )
    
    class Meta:
        model = Message
        fields = [
            'message_id',
            'sender',
            'sender_id',
            'conversation',
            'message_body',
            'sent_at'
        ]
        read_only_fields = ['message_id', 'sent_at']
        extra_kwargs = {
            'conversation': {'write_only': True}
        }

class ConversationParticipantSerializer(serializers.ModelSerializer):
    """Serializer for Conversation Participants"""
    
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )
    
    class Meta:
        model = ConversationParticipant
        fields = ['id', 'user', 'user_id', 'joined_at']
        read_only_fields = ['id', 'joined_at']

class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for the Conversation model with nested relationships"""
    
    participants = ConversationParticipantSerializer(
        source='participants', 
        many=True, 
        read_only=True
    )
    messages = MessageSerializer(many=True, read_only=True)
    participant_ids = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=User.objects.all()),
        write_only=True,
        required=True
    )
    latest_message = serializers.SerializerMethodField()
    participant_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'conversation_id',
            'participants',
            'participant_ids',
            'messages',
            'latest_message',
            'participant_count',
            'created_at'
        ]
        read_only_fields = ['conversation_id', 'created_at']
    
    def get_latest_message(self, obj):
        """Get the latest message in the conversation"""
        latest_message = obj.messages.order_by('-sent_at').first()
        if latest_message:
            return MessageSerializer(latest_message).data
        return None
    
    def get_participant_count(self, obj):
        """Get the number of participants in the conversation"""
        return obj.participants.count()
    
    def create(self, validated_data):
        """Create a conversation with participants"""
        participant_ids = validated_data.pop('participant_ids', [])
        conversation = Conversation.objects.create(**validated_data)
        
        # Add participants to the conversation
        for user in participant_ids:
            ConversationParticipant.objects.create(
                conversation=conversation,
                user=user
            )
        
        return conversation
    
    def update(self, instance, validated_data):
        """Update conversation participants"""
        participant_ids = validated_data.pop('participant_ids', None)
        
        if participant_ids is not None:
            # Clear existing participants and add new ones
            instance.participants.all().delete()
            for user in participant_ids:
                ConversationParticipant.objects.create(
                    conversation=instance,
                    user=user
                )
        
        return instance

class ConversationDetailSerializer(ConversationSerializer):
    """Detailed serializer for Conversation with full message history"""
    
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ['messages']

class UserConversationSerializer(serializers.ModelSerializer):
    """Serializer for user's conversations with basic info"""
    
    other_participants = serializers.SerializerMethodField()
    latest_message_preview = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'conversation_id',
            'other_participants',
            'latest_message_preview',
            'unread_count',
            'created_at'
        ]
        read_only_fields = fields
    
    def get_other_participants(self, obj):
        """Get participants excluding the current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            participants = obj.participants.exclude(user=request.user)
            return UserSerializer(participants, many=True).data
        return []
    
    def get_latest_message_preview(self, obj):
        """Get a preview of the latest message"""
        latest_message = obj.messages.order_by('-sent_at').first()
        if latest_message:
            preview = latest_message.message_body[:100] + '...' if len(latest_message.message_body) > 100 else latest_message.message_body
            return {
                'preview': preview,
                'sent_at': latest_message.sent_at,
                'sender': latest_message.sender.first_name
            }
        return None
    
    def get_unread_count(self, obj):
        """Get count of unread messages for the current user"""
        # This would need to be implemented with a MessageReadStatus model
        # For now, returning 0 as placeholder
        return 0

class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating messages"""
    
    sender_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='sender',
        write_only=True
    )
    
    class Meta:
        model = Message
        fields = [
            'message_id',
            'sender_id',
            'conversation',
            'message_body'
        ]
        read_only_fields = ['message_id']
    
    def validate(self, data):
        """Validate that the sender is a participant in the conversation"""
        sender = data.get('sender')
        conversation = data.get('conversation')
        
        if conversation and sender:
            is_participant = ConversationParticipant.objects.filter(
                conversation=conversation,
                user=sender
            ).exists()
            
            if not is_participant:
                raise serializers.ValidationError(
                    "Sender must be a participant in the conversation"
                )
        
        return data
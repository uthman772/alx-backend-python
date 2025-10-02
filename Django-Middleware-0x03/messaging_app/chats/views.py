from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Prefetch
from django.shortcuts import get_object_or_404
from .models import User, Conversation, ConversationParticipant, Message
from .serializers import (
    UserSerializer,
    ConversationSerializer,
    ConversationDetailSerializer,
    MessageSerializer,
    MessageCreateSerializer,
    UserConversationSerializer
)

class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model"""
    
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        if self.request.user.is_superuser:
            return User.objects.all()
        elif self.request.user.is_authenticated:
            return User.objects.filter(pk=self.request.user.pk)
        return User.objects.none()
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class ConversationViewSet(viewsets.ModelViewSet):
    """ViewSet for Conversation model"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return conversations where the current user is a participant"""
        user = self.request.user
        return Conversation.objects.filter(
            participants__user=user
        ).prefetch_related(
            Prefetch('participants', queryset=ConversationParticipant.objects.select_related('user')),
            Prefetch('messages', queryset=Message.objects.select_related('sender').order_by('sent_at'))
        ).distinct().order_by('-created_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'retrieve':
            return ConversationDetailSerializer
        elif self.action == 'list':
            return UserConversationSerializer
        return ConversationSerializer
    
    def perform_create(self, serializer):
        """Automatically add current user as participant when creating conversation"""
        conversation = serializer.save()
        
        # Ensure current user is added as participant
        ConversationParticipant.objects.get_or_create(
            conversation=conversation,
            user=self.request.user
        )
    
    def create(self, request, *args, **kwargs):
        """Create a new conversation with participants"""
        # Ensure participant_ids includes the current user
        participant_ids = request.data.get('participant_ids', [])
        if str(request.user.user_id) not in [str(pid) for pid in participant_ids]:
            participant_ids.append(str(request.user.user_id))
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """Add a participant to an existing conversation"""
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user is already a participant
        if ConversationParticipant.objects.filter(conversation=conversation, user=user).exists():
            return Response(
                {'error': 'User is already a participant'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ConversationParticipant.objects.create(conversation=conversation, user=user)
        
        return Response(
            {'message': 'Participant added successfully'}, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def remove_participant(self, request, pk=None):
        """Remove a participant from a conversation"""
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            participant = ConversationParticipant.objects.get(
                conversation=conversation, 
                user__user_id=user_id
            )
        except ConversationParticipant.DoesNotExist:
            return Response(
                {'error': 'Participant not found in conversation'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Prevent removing the last participant
        if conversation.participants.count() <= 1:
            return Response(
                {'error': 'Cannot remove the last participant from a conversation'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant.delete()
        
        return Response(
            {'message': 'Participant removed successfully'}, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get all messages for a specific conversation"""
        conversation = self.get_object()
        messages = conversation.messages.select_related('sender').order_by('sent_at')
        
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

class MessageViewSet(viewsets.ModelViewSet):
    """ViewSet for Message model"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageSerializer
    
    def get_queryset(self):
        """Return messages that the current user has access to"""
        user = self.request.user
        return Message.objects.filter(
            conversation__participants__user=user
        ).select_related('sender', 'conversation').order_by('-sent_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action in ['create', 'update']:
            return MessageCreateSerializer
        return MessageSerializer
    
    def perform_create(self, serializer):
        """Set the sender to the current user when creating a message"""
        serializer.save(sender=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Create a new message in a conversation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Verify user has access to the conversation
        conversation_id = request.data.get('conversation')
        if conversation_id:
            try:
                conversation = Conversation.objects.get(
                    conversation_id=conversation_id,
                    participants__user=request.user
                )
            except Conversation.DoesNotExist:
                return Response(
                    {'error': 'Conversation not found or access denied'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        # Return the created message with full details
        message = Message.objects.get(pk=serializer.data['message_id'])
        response_serializer = MessageSerializer(message)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=False, methods=['get'])
    def conversation_messages(self, request):
        """Get all messages for a specific conversation"""
        conversation_id = request.query_params.get('conversation_id')
        
        if not conversation_id:
            return Response(
                {'error': 'conversation_id query parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            conversation = Conversation.objects.get(
                conversation_id=conversation_id,
                participants__user=request.user
            )
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found or access denied'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        messages = conversation.messages.select_related('sender').order_by('sent_at')
        
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a message as read (placeholder for future implementation)"""
        message = self.get_object()
        # This would update a MessageReadStatus model in a real implementation
        return Response(
            {'message': 'Message read status updated'}, 
            status=status.HTTP_200_OK
        )

class MyConversationsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for current user's conversations"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserConversationSerializer
    
    def get_queryset(self):
        """Return conversations for the current user"""
        user = self.request.user
        return Conversation.objects.filter(
            participants__user=user
        ).prefetch_related(
            Prefetch('participants', queryset=ConversationParticipant.objects.select_related('user')),
            Prefetch('messages', queryset=Message.objects.select_related('sender').order_by('-sent_at'))
        ).distinct().order_by('-created_at')

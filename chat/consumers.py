import os
import json
import base64
import weakref

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.files.base import ContentFile
from django.utils import timezone
from .models import Room, Message
from asgiref.sync import sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    # Store connected users per room in class variable
    _connected_users = {}  # room_id -> {username: connection_count}

    @classmethod
    def get_room_participants(cls, room_id):
        return set(cls._connected_users.get(str(room_id), {}).keys())

    @classmethod
    def add_participant(cls, room_id, username):
        room_id = str(room_id)
        if room_id not in cls._connected_users:
            cls._connected_users[room_id] = {}
        if username not in cls._connected_users[room_id]:
            cls._connected_users[room_id][username] = 0
        cls._connected_users[room_id][username] += 1
        return len(cls._connected_users[room_id])

    @classmethod
    def remove_participant(cls, room_id, username):
        room_id = str(room_id)
        if room_id in cls._connected_users and username in cls._connected_users[room_id]:
            cls._connected_users[room_id][username] -= 1
            if cls._connected_users[room_id][username] <= 0:
                del cls._connected_users[room_id][username]
            if not cls._connected_users[room_id]:
                del cls._connected_users[room_id]
            return len(cls._connected_users[room_id]) if room_id in cls._connected_users else 0
        return 0

    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Add participant and get count
        count = self.add_participant(self.room_id, self.user.username)
        participants = list(self.get_room_participants(self.room_id))

        # Broadcast updated participant count
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'participant_update',
                'count': count,
                'participants': participants,
                'action': 'join',
                'username': self.user.username
            }
        )

    async def disconnect(self, close_code):
        try:
            # Remove participant and get count
            count = self.remove_participant(self.room_id, self.user.username)
            participants = list(self.get_room_participants(self.room_id))

            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

            # Broadcast updated participant count only if there are still participants
            if count > 0:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'participant_update',
                        'count': count,
                        'participants': participants,
                        'action': 'quit',
                        'username': self.user.username
                    }
                )
        except Exception as e:
            print(f"Error in disconnect: {str(e)}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type', '')
            user = self.scope['user']

            if message_type == 'typing':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_typing',
                        'user': user.username,
                        'typing': True
                    }
                )
            elif message_type == 'stop_typing':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_typing',
                        'user': user.username,
                        'typing': False
                    }
                )
            elif message_type == 'delete_message':
                message_id = data.get('message_id')
                success = await self.delete_message(user, message_id)
                
                if success:
                    # Broadcast deletion to room group
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'message_deleted',
                            'message_id': message_id
                        }
                    )
            elif message_type == 'edit_message':
                message_id = data.get('message_id')
                new_content = data.get('message')
                
                # Update message in database
                success, message_obj = await self.update_message(user, message_id, new_content)
                
                if success:
                    # Broadcast edited message to room group
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'message_edited',
                            'message_id': message_id,
                            'message': new_content,
                            'edited_at': message_obj.edited_at.isoformat() if message_obj.edited_at else None
                        }
                    )
            elif message_type == 'chat_message':
                message_content = data.get('message', '')
                file_data = data.get('file')
                file_name = data.get('file_name')
                reply_to_id = data.get('reply_to')

                # Save message to database
                message_obj = await self.save_message(
                    user=user,
                    message_content=message_content,
                    file_data=file_data,
                    file_name=file_name,
                    reply_to_id=reply_to_id
                )

                # Get reply info if needed
                reply_info = None
                if message_obj.reply_to:
                    reply_info = await self.get_reply_info(message_obj.reply_to.id)

                # Broadcast message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message_content,
                        'user': user.username,
                        'timestamp': message_obj.timestamp.isoformat(),
                        'message_id': message_obj.id,
                        'file_url': message_obj.file.url if message_obj.file else None,
                        'file_name': os.path.basename(message_obj.file.name) if message_obj.file else None,
                        'reply_info': reply_info
                    }
                )
        except Exception as e:
            print(f"Error in receive: {str(e)}")
            await self.send(text_data=json.dumps({
                'error': 'An error occurred while processing your message'
            }))

    async def user_typing(self, event):
        # Send typing status to WebSocket
        await self.send(text_data=json.dumps({
            'user': event['user'],
            'typing': event['typing']
        }))

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'user': event['user'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id'],
            'file': event.get('file_url'),
            'file_name': event.get('file_name'),
            'reply_info': event.get('reply_info')
        }))

    async def message_edited(self, event):
        # Send edited message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message_edited',
            'message_id': event['message_id'],
            'message': event['message'],
            'edited_at': event['edited_at']
        }))

    async def message_deleted(self, event):
        # Send message deletion to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message_deleted',
            'message_id': event['message_id']
        }))

    async def participant_update(self, event):
        # Send participant update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'participant_update',
            'count': event['count'],
            'participants': event['participants'],
            'action': event.get('action'),
            'username': event.get('username')
        }))

    @database_sync_to_async
    def get_reply_info(self, reply_to_id):
        try:
            reply_msg = Message.objects.select_related('user').get(id=reply_to_id)
            return {
                'id': reply_msg.id,
                'content': reply_msg.content[:100] + '...' if len(reply_msg.content or '') > 100 else reply_msg.content,
                'user': reply_msg.user.username,
                'has_file': bool(reply_msg.file)
            }
        except Message.DoesNotExist:
            return None

    @database_sync_to_async
    def save_message(self, user, message_content, file_data=None, file_name=None, reply_to_id=None):
        try:
            room = Room.objects.get(id=self.room_id)
            message = Message(user=user, room=room, content=message_content)

            if reply_to_id:
                try:
                    reply_to_message = Message.objects.get(id=reply_to_id)
                    message.reply_to = reply_to_message
                except Message.DoesNotExist:
                    pass

            if file_data and file_name:
                # Remove the "data:..." prefix from the base64 string
                if ',' in file_data:
                    format, filestr = file_data.split(';base64,')
                    file_content = ContentFile(
                        base64.b64decode(filestr),
                        name=file_name
                    )
                    message.file = file_content

            message.save()
            return message
        except Exception as e:
            print(f"Error saving message: {str(e)}")
            raise

    @database_sync_to_async
    def update_message(self, user, message_id, new_content):
        try:
            message = Message.objects.get(id=message_id, user=user)
            message.content = new_content
            message.edited_at = timezone.now()
            message.save()
            return True, message
        except Message.DoesNotExist:
            return False, None

    @database_sync_to_async
    def delete_message(self, user, message_id):
        try:
            message = Message.objects.get(id=message_id, user=user)
            message.delete()
            return True
        except Message.DoesNotExist:
            return False

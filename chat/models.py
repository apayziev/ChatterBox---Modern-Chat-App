# chat/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os

class Room(models.Model):
    title = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    participants = models.ManyToManyField(User, related_name='joined_rooms', blank=True)

    def __str__(self):
        return self.title

    def add_participant(self, user):
        if user not in self.participants.all():
            self.participants.add(user)
            self.save()

    def remove_participant(self, user):
        if user in self.participants.all():
            self.participants.remove(user)
            self.save()

    def get_messages(self, limit=50):
        return self.messages.all().order_by('-timestamp')[:limit]

    def get_recent_messages(self, limit=50):
        return self.message_set.order_by('-timestamp')[:limit]
    
    def get_participant_count(self):
        return self.participants.count()


def message_file_path(instance, filename):
    # Generate file path: media/chat_files/room_<id>/<filename>
    return os.path.join('chat_files', f'room_{instance.room.id}', filename)

class Message(models.Model):
    room = models.ForeignKey(Room, related_name='messages', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to=message_file_path, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f'{self.user.username}: {self.content if self.content else "File"}'
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save()
    
    @property
    def file_url(self):
        if self.file:
            return self.file.url
        return None

    @property
    def file_name(self):
        if self.file:
            return os.path.basename(self.file.name)
        return None

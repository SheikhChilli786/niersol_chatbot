import uuid
from django.db import models
from django.contrib.auth.models import User

class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # Use UUID for the primary key
    created_at = models.DateTimeField(auto_now_add=True)
    live_agent = models.ForeignKey(User,on_delete=models.CASCADE,null=True,related_name='live_agents')
    open = models.BooleanField(default=True)
    live_support = models.BooleanField(default=False)

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    role = models.CharField(max_length=15)  # 'user' or 'assistant'
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.conversation.id} - {self.role}-{self.content}"

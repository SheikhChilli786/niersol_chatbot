from django.contrib import admin
from .models import *

# Register your models here.
@admin.register(Conversation)
class adminConversation(admin.ModelAdmin):
    pass

@admin.register(Message)
class adminMessage(admin.ModelAdmin):
    pass
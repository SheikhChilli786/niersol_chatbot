import os
import json
import openai
from .models import *
from openai import OpenAI
from django.shortcuts import render,redirect,get_object_or_404
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
client = OpenAI(api_key=os.environ.get('OPENAI_APIKEY'))
class ChatConsumer(WebsocketConsumer):
     def connect(self):
        # Generate or retrieve the session key for anonymous users
        if not self.scope['session'].session_key:
            self.scope['session'].save()
        print(self.scope['session'].session_key)
        if 'thread_id' not in self.scope['session']:
            # Generate a new assistant thread ID (you can create a UUID or similar identifier)
            thread = client.beta.threads.create()

            self.scope['session']['thread_id'] = thread.id

            # Save the session to persist the assistant thread ID
            self.scope['session'].save()

        # Use the session key as the room name for anonymous users
        self.thread_id = self.scope['session']['thread_id']
        self.room_group_name = f"chat_{self.thread_id}"
        self.conversation = Conversation.objects.create()
        self.accept()
        # Join the unique room for this session
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name,
        )

     def disconnect(self, close_code):
        # Leave the room when the WebSocket connection is closed
        conversation = Conversation.objects.get(id=self.conversation.id)
        if self.conversation.live_support == False:
            conversation.delete()
        else:
            conversation.open == False
            conversation.save()
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name,
        )

     def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        messages = []
        conversation = get_object_or_404(Conversation,id=self.conversation.id)
        messages = self.get_messages(conversation)
        messages.append({'role':'user','content':message})
        print(messages)
        Message.objects.create(conversation=conversation, role='user', content=message)
        response = self.get_response(messages)
        Message.objects.create(conversation=conversation, role='assistant', content=response)
        print(response)
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': response,
            }
        )
     def chat_message(self, event):
        self.send(text_data=json.dumps(event))

     def get_response(self,messages):
        response = client.chat.completions.create(
            model='ft:gpt-4o-mini-2024-07-18:personal::ACoJpmCp',
            messages=messages,
        )
        return response.choices[0].message.content

        # message = client.beta.threads.messages.create(
        #     thread_id=self.thread_id,
        #     role='user',
        #     content=user_message
        # )
        # run = client.beta.threads.runs.create_and_poll(
        #     thread_id=self.thread_id,
        #     assistant_id='asst_BunrX4vdD5yRKBIhrbuDohIi',
        # ) 
        # if run.status == 'completed': 
        #     messages = client.beta.threads.messages.list(
        #         thread_id=self.thread_id
        #     )
        #     return messages.data[0].content[0].text.value
        # else:
        #     return run.status
        
     def get_messages(self,conversation):
        list = []
        list.append({'role':'system','content':"You are AI chatbot assistant for niersol.Niersol is a digital solutions and IT consulting company that specializes in providing cutting-edge solutions such as AI-powered chatbots, web development, CRM integration, API integrations, and full custom chatbot integration into various platforms including Discord, WhatsApp, Telegram, and websites. Niersol is committed to helping businesses grow by providing scalable, secure, and customized digital tools that improve operational efficiency, enhance customer engagement, and automate processes. If the user,s query is not relevant to Niersol,s services, politely inform them and suggest they reach out to a live agent for more details."})
        messages = Message.objects.filter(conversation = conversation).order_by('created_at')[:10]
        for message in messages:
            list.append({'role':message.role,'content':message.content})
        return list

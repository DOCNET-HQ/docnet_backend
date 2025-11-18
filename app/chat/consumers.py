import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from .models import ChatRoom, Message, UserStatus

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.authenticated = False
        self.user = None
        self.room_id = None
        self.room_group_name = None

    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"
        await self.accept()

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get("type", "")

            if not self.authenticated:
                if message_type == "auth":
                    token = text_data_json.get("token")
                    if token and await self.authenticate_token(token):
                        self.authenticated = True
                        await self.channel_layer.group_add(
                            self.room_group_name, self.channel_name
                        )
                        await self.update_user_status(True)
                        await self.send(
                            json.dumps(
                                {
                                    "type": "auth_success",
                                    "message": "Authentication successful",
                                }
                            )
                        )
                    else:
                        await self.send(
                            json.dumps(
                                {
                                    "type": "auth_failed",
                                    "message": "Authentication failed",
                                }
                            )
                        )
                        await self.close()
                else:
                    await self.send(
                        json.dumps(
                            {
                                "type": "auth_required",
                                "message": "Authentication required.",
                            }
                        )
                    )
                return

            if message_type == "chat_message":
                await self.handle_chat_message(text_data_json)
            elif message_type == "typing":
                await self.handle_typing_indicator(text_data_json)

        except Exception as e:
            print(f"Error in receive: {e}")

    async def handle_chat_message(self, data):
        try:
            content = data["content"]

            if self.user.is_authenticated:
                message = await self.save_message(content, self.user)
                user_name = await self.get_user_name(self.user)

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat_message",
                        "message": {
                            "id": str(message.id),
                            "content": message.content,
                            "sender": {
                                "id": str(self.user.id),
                                "name": user_name,
                                "email": self.user.email,
                                "online": await self.get_user_online_status(self.user),
                            },
                            "timestamp": message.timestamp.isoformat(),
                        },
                    },
                )
        except Exception as e:
            print(f"Error handling chat message: {e}")

    async def handle_typing_indicator(self, data):
        try:
            user_name = await self.get_user_name(self.user)
            is_typing = data.get("is_typing", False)

            print(f"Typing indicator: {user_name} is typing: {is_typing}")

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_indicator",
                    "user_id": str(self.user.id),
                    "user_name": user_name,
                    "is_typing": is_typing,
                },
            )
            print(f"Typing indicator sent to room {self.room_group_name}")
        except Exception as e:
            print(f"Error handling typing indicator: {e}")

    async def chat_message(self, event):
        try:
            await self.send(
                text_data=json.dumps(
                    {"type": "chat_message", "message": event["message"]}
                )
            )
        except Exception as e:
            print(f"Error sending chat_message: {e}")

    async def typing_indicator(self, event):
        try:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "typing",
                        "user_id": event["user_id"],
                        "user_name": event["user_name"],
                        "is_typing": event["is_typing"],
                    }
                )
            )
        except Exception as e:
            print(f"Error sending typing indicator: {e}")

    @database_sync_to_async
    def authenticate_token(self, token):
        try:
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
            self.user = User.objects.get(id=user_id)
            self.scope["user"] = self.user
            return True
        except Exception as e:
            print(f"Token authentication failed: {e}")
            self.user = AnonymousUser()
            self.scope["user"] = self.user
            return False

    @database_sync_to_async
    def get_user_name(self, user):
        try:
            if hasattr(user, "profile") and user.profile:
                return user.profile.name
            return user.email
        except Exception:
            return user.email

    @database_sync_to_async
    def get_user_online_status(self, user):
        try:
            status = UserStatus.objects.get(user=user)
            return status.online
        except UserStatus.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content, user):
        room = ChatRoom.objects.get(id=self.room_id)
        message = Message.objects.create(room=room, sender=user, content=content)
        return message

    @database_sync_to_async
    def update_user_status(self, online):
        if self.user and self.user.is_authenticated:
            status, created = UserStatus.objects.get_or_create(user=self.user)
            status.online = online
            status.save()

    async def disconnect(self, close_code):
        if self.authenticated and self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

        if self.user and self.user.is_authenticated:
            await self.update_user_status(False)

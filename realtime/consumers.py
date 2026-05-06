import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class ClassroomConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.class_id = self.scope['url_route']['kwargs']['class_id']
        self.room_group_name = f'class_{self.class_id}'
        
        # Join the classroom channel group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the classroom channel group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from room group
    async def classroom_message(self, event):
        # Send message to WebSocket
        await self.send_json({
            'event': event['event'],
            'data': event.get('data', {})
        })

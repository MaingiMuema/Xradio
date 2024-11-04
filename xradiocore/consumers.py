from channels.generic.websocket import AsyncWebsocketConsumer
import json

class RadioConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("radio_updates", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("radio_updates", self.channel_name)

    async def broadcast_update(self, event):
        await self.send(text_data=json.dumps(event['message']))

    async def track_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'track_update',
            'title': event['title']
        }))

    async def segment_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'segment_update',
            'segment': event['segment'],
            'image_prompt': event.get('image_prompt', '')
        }))

    async def image_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'image_update',
            'image_url': event['image_url']
        })) 
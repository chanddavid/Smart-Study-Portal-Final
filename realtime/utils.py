from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def broadcast_to_class(class_id, event_type, data):
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f"class_{class_id}",
            {
                "type": "classroom_message",
                "event": event_type,
                "data": data,
            }
        )

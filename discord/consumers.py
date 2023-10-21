import json

from channels.generic.websocket import WebsocketConsumer
from userauth.views import login_signal


class ChatConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # post_save.connect(self.db_post_save)
        login_signal.connect(self.db_post_save)

    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def db_post_save(self, sender, **kwargs):
        if (payload := kwargs.get("payload")) is None:
            return

        self.send(text_data=json.dumps({"message": json.dumps(payload)}))

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        self.send(text_data=json.dumps({"message": message}))

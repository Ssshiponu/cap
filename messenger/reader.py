from .models import Message
from core.ai import AI

STICKERS = {
    "369239263222822": "👍"
}

SUPPORTED_MEDIA_TYPES = ["image", "audio"]


class Reader:
    def __init__(self, ai: AI):
        self.ai = ai
        
    def _process_attachment(self, attachment, role: str):
        attachment_type = attachment["type"]
        if attachment_type in SUPPORTED_MEDIA_TYPES:
            url = attachment["payload"]["url"]
            message = self.ai.read_media(url) if role == 'user' else url
            return f"> {role} sent an {attachment_type}: {message}"
        else:
            return f"> {role} sent an {attachment_type} - can't read"

        
    def make_readable(self, json_data, role: str):
        role = 'you' if role=='assistant' else role
        read = ''
        
        # if only text
        if "reply_to" in json_data:
            message = Message.objects.get(mid=json_data["reply_to"]["mid"])
            read += f"> {role} replied to '{message.content}' \n"
            
        if "text" in json_data:
            read += json_data["text"]
        
        elif "attachments" in json_data:
            for attachment in json_data["attachments"]:
                attachments_type = attachment["type"]
                if "sticker_id" in attachment["payload"] and attachments_type == "image": 
                    sticker_id = attachment["payload"].get("sticker_id", "")
                    read += STICKERS.get(str(sticker_id), f"> {role} sent an unknown sticker")
                else:
                    read += self._process_attachment(attachment, role)
        
        elif "attachment" in json_data:
            read += self._process_attachment(json_data["attachment"], role)

        return read if read else f"> {role} sent unknown message"
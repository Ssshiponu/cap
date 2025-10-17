import requests

API_URL = "https://graph.facebook.com/v19.0/me/messages"

class Messenger:
    def __init__(self, access_token, sender_id, page_id):
        self.access_token = access_token
        self.sender_id = sender_id
        self.page_id = page_id
    
    def _send_api_request(self, payload: dict):
        """Generic function to send a POST request to the Messenger Send API."""
        params = {"access_token": self.access_token}
        try:
            r = requests.post(API_URL, params=params, json=payload, timeout=10)
            r.raise_for_status()
            response_data = r.json()
            if "error" in response_data:
                print(f'FB Send API error: {response_data["error"]["message"]}')
                return None
            return response_data
        except requests.exceptions.RequestException as e:
            print(f"Error sending message: {e}")
            return None

    def send_reply(self,message: dict):
        """Sends a message object (text, attachment, quick replies) via Facebook."""
        payload = {"recipient": {"id": self.sender_id}, "message": message, "messaging_type": "RESPONSE"}
        return self._send_api_request(payload)

    def send_action(self, action: str):
        """Sends sender actions like 'typing_on' or 'mark_seen'."""
        payload = {"recipient": {"id": self.sender_id}, "sender_action": action}
        return self._send_api_request(payload)
    
    def send_template(self):
        payload = {
            "recipient": {"id": self.sender_id},
            
            "message": {
                "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "image_aspect_ratio": "square",
                    "elements": [
                    {
                        "title": "Python T-Shirt",
                        "subtitle": "200 ৳",
                        "image_url": "https://nixagone.pythonanywhere.com/media/products/python1.jpg",
                        "default_action": {
                        "type": "web_url",
                        "url": "https://nixagone.pythonanywhere.com/product/python-t-shirt/",
                        "webview_height_ratio": "tall"
                        },
                        "buttons": [
                        {
                            "type": "web_url",
                            "url": "https://nixagone.pythonanywhere.com/product/python-t-shirt/",
                            "title": "View",
                            "webview_height_ratio": "tall"
                        },
                        {
                            "type": "web_url",
                            "url": "https://nixagone.pythonanywhere.com/product/python-t-shirt/",
                            "title": "Buy",
                            "webview_height_ratio": "tall"
                        }
                        ]
                    },
                    {
                        "title": "Git T-Shirt",
                        "subtitle": "200 ৳",
                        "image_url": "https://nixagone.pythonanywhere.com/media/products/git1.jpg",
                        "default_action": {
                        "type": "web_url",
                        "url": "https://nixagone.pythonanywhere.com/product/git-t-shirt/",
                        "webview_height_ratio": "tall"
                        },
                        "buttons": [
                        {
                            "type": "web_url",
                            "url": "https://nixagone.pythonanywhere.com/product/git-t-shirt/",
                            "title": "View",
                            "webview_height_ratio": "tall"
                        },
                        {
                            "type": "web_url",
                            "url": "https://nixagone.pythonanywhere.com/product/git-t-shirt/",
                            "title": "Buy",
                            "webview_height_ratio": "tall"
                        }
                        ]
                    }
                    ]
                }
                }
            }
            

        }
        return self._send_api_request(payload)
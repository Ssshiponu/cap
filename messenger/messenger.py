import requests
import json

API_URL = "https://graph.facebook.com/v19.0/me/messages"

class Messenger:
    def __init__(self, access_token, sender_id, page_id):
        self.access_token = access_token
        self.sender_id = sender_id
        self.page_id = page_id
    
    def _send_api_request(self, payload: dict, api_url=API_URL):
        """Generic function to send a POST request to the Messenger Send API."""
        params = {"access_token": self.access_token}
        try:
            r = requests.post(api_url, params=params, json=payload, timeout=10)
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
        print(json.dumps(payload, indent=4))
        return self._send_api_request(payload)

    def send_action(self, action: str):
        """Sends sender actions like 'typing_on' or 'mark_seen'."""
        payload = {"recipient": {"id": self.sender_id}, "sender_action": action}
        return self._send_api_request(payload)
    
    # def whitelist_domain(self, domain: str):
    #     """
    #     Whitelists a domain for use in webviews.
    #     https://developers.facebook.com/docs/messenger-platform/reference/messaging-profile-api/#whitelisted-domains
    #     """
    #     payload = {"whitelisted_domains": [domain], "domain_action_type": "whitelist"}
    #     return self._send_api_request(payload, api_url=f"https://graph.facebook.com/v24.0/me/messenger_profile")
    

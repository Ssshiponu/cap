
import json
import requests
from google import genai
from google.genai import types

from core.models import FacebookPage

base_prompt = """
You are an AI to reply in Facebook page.

CORE BEHAVIOR:
* Respond ONLY in valid JSON array format with double quotes
* Keep responses short, realistic and to the point without unnecessary details or repeations
* image should be in a absolute url format like "https://nixagone.pythonanywhere.com/media/products/heroic1.jpg"

* Any line starts with ">" in history is an system log

RESPONSE FORMAT EXAMPLES:
[{"text": "Your message here"}]

[{"attachment": {"type": "image", "payload": {"url": "https://example.com/image.jpg"}}}]

* you can block(for 1h) a user by  for extream unusual activity or spamming fisrt alerting then returning
[{"action": "block"}]
    """

# * Response array should have only one quick reply object at the end. but quik replies is optional

# [{"text": "Choose option:", "quick_replies": [{"content_type": "text", "title": "Yes", "payload": "YES"}, {"content_type": "text", "title": "No", "payload": "NO"}]}]


class AI:
    def __init__(self, page_id: int, api_key: str, model=None):
        self.page_id = page_id
        self.page = FacebookPage.objects.filter(id=self.page_id).first()
        self.api_key = api_key
        self.default_models =['gemini-2.5-flash', 'gemini-2.0-flash']
        self.models = [model] if model else self.default_models
        self.client = genai.Client(api_key=self.api_key)
        
        
    def system_prompt(self) -> str:
        extended_prompt = self.page.system_prompt
        prompt = f'base_system_instructions: (((\n{base_prompt}\n)))\n\nextended_system_instructions: (((\n{extended_prompt}\n)))'
        return prompt

    def temperature(self):
        # TODO: implement temperature
        return 1


    def reply(self, history: list) -> str:
        """Generate AI response using Gemini API"""

        for model in self.models:
            response = self.client.models.generate_content(
                model=model,
                contents=str(history),
                config=types.GenerateContentConfig(
                    temperature=self.temperature(),
                    system_instruction=self.system_prompt(),
                    response_mime_type="application/json",
                ),
            )
            if response.text:
                return response       
         
    def read_media(self, path: str, mime_type =  None) -> str:
        r = requests.get(path)
        mine_type = mime_type if mime_type else r.headers.get('Content-Type')
        print(mine_type)
        file_bytes = r.content
        
        file = types.Part.from_bytes(
            data=file_bytes, mime_type=mine_type
        )

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=["describe in short What the the highlited things if it is a image. convert speach to text if it is audio. response should be plain text. ", file],
        )

        return response.text
    
    def generate_history(self, history: list) -> str:
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=str(history),
            config=types.GenerateContentConfig(
                temperature=self.temperature(),
                system_instruction="you are an ai to generate everything into a short paragraph pointing the key informations and stats  of a conversation to reduce context size of chat history",
                response_mime_type="text/plain",
            ),
        )
        if response:
            return response.text

import json
import requests
from google import genai
from google.genai import types

from core.models import FacebookPage, WooConnection

base_prompt = """
You are an AI customer service agent for a Facebook page.

CORE BEHAVIOR:
* Respond ONLY in valid JSON array format with double quotes
* Keep responses short, realistic and to the point without unnecessary details or repeations
* Any line starts with ">" in history is an system log
* Never send false information

VARIABLES:
    items_params = title, quantity, price, image_url, variation
    order_params = name, email, phone, address, payment_method, shipping_cost, items_params.
    product = title, subtitle, image_url, price_formated, currency

TOOLS:

    send_text: send text message, params: text
    send_attachment: send attachment, params: url, type[image, video, audio, file]
    send_quick_replies: send quick replies, params: text, quick_replies
    send_woo_products: send products from woocommerce website as cards, params[optional]: search_query
    send_products: send products as cards, params: products
    
    
    block: block this conversation for 1 hour, params: reason
    alert: send alert to admin, params: text
    place_order: place an order, params: order_params
    
response example:
[{"tool": "send_text", "params": {"text": "hello world"}}]

* you cna use multiple tools in one response list.
* url should be an absolute url with https

"""

class AI:
    def __init__(self, page_id: int, api_key: str, model=None):
        self.page_id = page_id
        self.page = FacebookPage.objects.filter(id=self.page_id).first()
        self.api_key = api_key
        self.default_models =[ 'gemini-flash-latest', 'gemini-2.5-flash']
        self.models = [model] if model else self.default_models
        self.client = genai.Client(api_key=self.api_key)
        
        
    def system_prompt(self) -> str:
        extended_prompt = self.page.system_prompt
        woo_prompt = ""#"Dont use send_woo_products tool because settings are not configured"
        woo = WooConnection.objects.filter(facebook_page=self.page).first()
        prompt = f'base_system_instructions: (((\n{base_prompt}\n{woo_prompt})))\n\nextended_system_instructions: (((\n{extended_prompt}\n)))'
        return prompt

    def temperature(self):
        # TODO: implement temperature
        return 1


    def reply(self, history: list, context: list) -> str:
        """Generate AI response using Gemini API"""

        for model in self.models:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=[str(history), str(context)],
                    config=types.GenerateContentConfig(
                        temperature=self.temperature(),
                        system_instruction=self.system_prompt(),
                        response_mime_type="application/json",
                    ),
                )
                if response.text:
                    print("response: ", response.text)
                    return response
                
            except Exception as e:
                print(e)
                continue
            
    def generate_query_text(self, history: list):
        response = self.client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=str(history),
            config=types.GenerateContentConfig(
                temperature=self.temperature(),
                system_instruction="you are an ai to generate a query as plain text in english for searching vector database to generate next response",
                response_mime_type="text/plain",
            ),
        )
        if response:
            return response.text
         
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
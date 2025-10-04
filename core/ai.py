
import json
import requests
from google import genai
from google.genai import types

from core.models import FacebookPage

MODELS = [ "gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"]

gf_gpt ="""
    
"""

base_prompt = """
You are an AI to reply in Facebook page.

CORE BEHAVIOR:
* Respond ONLY in valid JSON array format with double quotes
* Keep responses short and to the point without unnecessary details or repeations
* Response array should have only one quick reply object at the end. but quik replies is optional
* image should be in a absolute url format like "https://nixagone.pythonanywhere.com/media/products/heroic1.jpg"

* Any line starts with ">" in history is an system log

RESPONSE FORMAT EXAMPLES:
[{"text": "Your message here"}]

[{"text": "Choose option:", "quick_replies": [{"content_type": "text", "title": "Yes", "payload": "YES"}, {"content_type": "text", "title": "No", "payload": "NO"}]}]

[{"attachment": {"type": "image", "payload": {"url": "https://example.com/image.jpg"}}}]
    """
    
def system_prompt(page_id: int) -> str:
    page=FacebookPage.objects.filter(id=page_id).first()
    extended_prompt = page.system_prompt
    business_context = page.business_context
    prompt = f'base_system_instructions: (((\n{base_prompt}\n)))\n\nextended_system_instructions: (((\n{extended_prompt}\n)))\n\nbusiness_context: (((\n{business_context}\n)))'
    print(prompt)
    return prompt

def ai_reply(history: list, page_id: int, api_key: str) -> list:
    """Generate AI response using Gemini API"""

    client = genai.Client(api_key=api_key)
    
    for model in MODELS:
        response = client.models.generate_content(
            model=model,
            contents=history,
            config=types.GenerateContentConfig(
                temperature=float(1.0),
                system_instruction=system_prompt(page_id),
                response_mime_type="application/json",
            ),
        )
    
        # Parse the JSON response
        try:
            parsed_response = json.loads(response.text)
        except json.JSONDecodeError:
            parsed_response = []

        return parsed_response
    
def read_media(path: str, api_key: str) -> str:
    
    image_bytes = requests.get(path).content
    image = types.Part.from_bytes(
        data=image_bytes, mime_type="image/jpeg"
    )

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=["What is in this media file? describe core thing in short to clearly identify it. response should be plain text", image],
    )

    return response.text
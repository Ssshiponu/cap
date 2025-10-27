def generate_products(self, products: list):
    payload = {
            "attachment": {
            "type": "template",
            "payload": {
                "template_type": "generic",
                "image_aspect_ratio": "square",
                "elements": []
            }
        }
    }
    
    for product in products:
        payload["attachment"]["payload"]["elements"].append(
            {
                "title": product["title"],
                "subtitle": product["subtitle"],
                "image_url": product["image_url"],
                "buttons": [
                    {
                        "type": "postback",
                        "title": "Buy",
                        "payload": f"BUY_{product["title"].upper().replace(' ', '_')}"
                    },
                    {
                        "type": "postback",
                        "title": "View",
                        "payload": f"VIEW_IMAGES_OF_{product['title'].upper().replace(' ', '_')}"
                    }
                ]
            }
        )
    return payload


import time

def generate_products(products: list):
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


def generate_receipt(receipt: dict):
    subtotal = sum(item["price"] * item["quantity"] for item in receipt["items"])
    shipping_cost = receipt["shipping_cost"]
    tax = 0
    address = receipt["address"].split(",")
    
    payload = {
        "attachment":{
        "type":"template",
        "payload":{
            "template_type":"receipt",
            "recipient_name":receipt["name"],
            "order_number": "6535463542756",
            "order_url": "https://nixagone.pythonanywhere.com/#order?id=123",
            "currency":"BDT",
            "payment_method": receipt["payment_method"], 
            "timestamp": int(time.time()),       
            "address":{
                "street_1": address[0],
                "street_2":"",
                "city": address[1],
                "postal_code":"76576",
                "state": address[2],
                "country": address[3]
            },

            "summary":{
                "subtotal": subtotal,
                "shipping_cost": shipping_cost,
                "total_tax": tax,
                "total_cost": subtotal + shipping_cost + tax
            },
            
            "elements":[]
        }
        }
    }
    
    for item in receipt["items"]:
        payload["attachment"]["payload"]["elements"].append(
            {
                "title": f'{item["title"][:30]} | {item["variation"]} | x {item["quantity"]}',
                "subtitle": item["variation"],
                "quantity": item["quantity"],
                "price": item["price"],
                "currency": "BDT",
                "image_url": item["image_url"]
            }
        )

    return payload

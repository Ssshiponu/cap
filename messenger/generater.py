import time
from urllib.parse import quote
from html import escape, unescape
from bs4 import BeautifulSoup

def ssl_url(url):
    return url.replace("http://", "https://")

def generate_text(text: str):
    return {
        "text": text
    }
    
def generate_attachment(url: str, type: str):
    return {
        "attachment": {
            "type": type,
            "payload": {
                "url": ssl_url(url)
            }
        }
    }
    
def generate_quick_replies(text: str, quick_replies: list):
    return {
        "text": text,
        "quick_replies": [
            {
                "content_type": "text",
                "title": r, "payload": r.upper().replace(" ", "_")
            } for r in quick_replies
        ]
    }

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
        product_id = product.get('id', '')
        image_url = product.get("images", [None])[0]
        payload["attachment"]["payload"]["elements"].append(
            {
            "title": product.get("title", ""),
            "image_url": ssl_url(image_url if image_url else product.get("image_url", "")),
            "subtitle": f'{product.get("price_formated", "")} - {product.get("subtitle", "")}',
            
            "buttons": [
                {
                "type": "postback",
                "title": "Buy",
                "payload": f'BUY_WOOCOMMERCE_PRODUCT_ID:{product_id}' if product_id else f"BUY_PRODUCT:{product.get('title', '')}",
                },
                {
                "type": "web_url",
                "url": ssl_url(product["url"]),
                "title": "View",
                
                } if product.get("url", "") else {
                "type": "postback",
                "title": "View",
                "payload": f"VIEW_PRODUCT_ID:{product_id if product_id else product.get('title', '')}",
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


def translate_woocommerce_products(products: list):
    """translate woocommerce products to messenger products"""
    new_products = []
    print(products)
    
    
    for product in products:

        new_products.append({
            "id": product["id"],
            "title": product["name"],
            "subtitle": BeautifulSoup(product["short_description"], "html.parser").get_text(),
            "images": [ssl_url(image["src"]) for image in product["images"]],
            "url": ssl_url(product["permalink"]),
            "price": product["price"],
            "price_formated": unescape(BeautifulSoup(product["price_html"], "html.parser").get_text()),
            "rating": product["average_rating"],
            "stock": product["stock_quantity"]
        })
        
        
    
    return new_products
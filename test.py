from woocommerce import API
import json

wcapi = API(
    url="https://dotshirt.kesug.com/",
    consumer_key="ck_cc896e64781f95a3cbe14ec4d98789c73dda310d",
    consumer_secret="cs_424b72a7555e92d65cbab456fe7383ceff36fae3",
    version="wc/v3"
)

data = {
    "payment_method": "cod",  # must match one of your active payment methods (e.g., "cod", "bacs", "paypal")
    "payment_method_title": "Cash on Delivery",
    "set_paid": False,  # True if already paid
    "billing": {
        "first_name": "Mohin",
        "last_name": "Uddin",
        "address_1": "Dhamrai",
        "city": "Dhaka",
        "country": "BD",
        "email": "mohin@example.com",
        "phone": "+8801xxxxxxxxx"
    },
    "shipping": {
        "first_name": "Mohin",
        "last_name": "Uddin",
        "address_1": "Dhamrai",
        "city": "Dhaka",
        "country": "BD"
    },
    "line_items": [
        {
            "product_id": 12,  # existing product ID
            "quantity": 2
        }
    ],
    "shipping_lines": [
        {
            "method_id": "flat_rate",
            "method_title": "Flat Rate",
            "total": "100.00"
        }
    ]
}

response = wcapi.post("orders", data).json()



print(json.dumps(response, indent=4))



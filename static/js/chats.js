const mainChat = [
{ role: 'user', type: 'text', content: 'Hello', cooldown: 1000 },
{ role: 'bot', type: 'text', content: 'Hi, I\'m an AI assistant for Dotshirt. Do you want to see some products?', cooldown: 2000 },
{ role: 'user', type: 'text', content: 'show products', cooldown: 1000 },
{ role: 'bot', type: 'products', content: [
    {title: 'HTML Logo T-shirt', subtitle: '450 BDT', image: 'https://nixagone.pythonanywhere.com/media/products/html1.jpg'},
    {title: 'Git Logo T-shirt', subtitle: '450 BDT', image: 'https://nixagone.pythonanywhere.com/media/products/git1.jpg'},
    {title: 'Python Shirt', subtitle: '550 BDT', image: 'https://nixagone.pythonanywhere.com/media/products/html1.jpg'}
    ], cooldown: 3000 },
{ role: 'user', type: 'text', content: 'Show me more images of Git Logo T-shirt.', cooldown: 1500 },
{ role: 'bot', type: 'text', content: 'Of course!', cooldown: 1000 },
{ role: 'bot', type: 'image', content: 'https://nixagone.pythonanywhere.com/media/products/git1.jpg', cooldown: 1500 },
{ role: 'bot', type: 'text', content: 'Do you want to buy it?', cooldown: 500 },
{ role: 'bot', type: 'replies', content: ['Yes', 'No', 'Later'], cooldown: 1500 },
{ role: 'user', type: 'text', content: 'Yes', cooldown: 1000 },
{ role: 'bot', type: 'text', content: 'Great! Please provide your name, phone number, and address.', cooldown: 1500 },
{ role: 'user', type: 'text', content: 'Asraf Uddin, 01612345678, Forjon plaza, Savar, Dhaka', cooldown: 1000 },
{ role: 'bot', type: 'text', content: 'I confirmed your order! here is your receipt.', cooldown: 1000 },
{ role: 'bot', type: 'receipt', content: '1 item, 450 BDT, COD, deliver to Forjon plaza...', cooldown: 5000 }
];

const productCardChat = [
    { role: 'user', type: 'text', content: 'Hello', cooldown: 1000 },
    { role: 'bot', type: 'text', content: 'Hi, I\'m an AI assistant for Dotshirt. Do you want to see some products?', cooldown: 2000 },
    { role: 'user', type: 'text', content: 'show products', cooldown: 1000 },
    { role: 'bot', type: 'products', content: [
        {title: 'HTML Logo T-shirt', subtitle: '450 BDT', image: 'https://nixagone.pythonanywhere.com/media/products/html1.jpg'},
        {title: 'Git Logo T-shirt', subtitle: '450 BDT', image: 'https://nixagone.pythonanywhere.com/media/products/git1.jpg'},
        {title: 'Python Shirt', subtitle: '550 BDT', image: 'https://nixagone.pythonanywhere.com/media/products/html1.jpg'}
        ], cooldown: 3000 },
    { role: 'bot', type: 'text', content: 'Do you want to buy any of these products?', cooldown: 1500 },
]
const imageVoiceChat = [
  { role: 'user', type: 'voice', content: 'voice.mp3', duration: "00:08", cooldown: 1200 },
  { role: 'bot', type: 'text', content: 'I received your voice message! Do you want to see round-neck black t-shirts?', cooldown: 1800 },

  { role: 'user', type: 'image', content: 'https://developer-shop.com/cdn/shop/products/unisex-premium-t-shirt-black-front-601bf4422b086.jpg', cooldown: 1500 },
  { role: 'user', type: 'text', content: 'Do you have something like this?', cooldown: 2000 },

  { role: 'bot', type: 'text', content: 'Sorry we don\'t have this Javascript logo t-shirt right now. It will be available soon.', cooldown: 4000 },

];
const orderFlowChat = [
  { role: 'user', type: 'text', content: 'I want to buy the HTML logo T-shirt', cooldown: 1000 },

  { role: 'bot', type: 'text', content: 'Great choice! It costs 450 BDT. What size do you prefer?', cooldown: 1500 },
  { role: 'bot', type: 'replies', content: ['M', 'L', 'XL'], cooldown: 1200 },

  { role: 'user', type: 'text', content: 'L', cooldown: 1000 },

  { role: 'bot', type: 'text', content: 'Perfect! Please provide your name, phone number and delivery address.', cooldown: 1500 },

  { role: 'user', type: 'text', content: 'Asraf Uddin, 01612345678, Forjon plaza, Savar, Dhaka', cooldown: 1200 },

  { role: 'bot', type: 'text', content: 'Thank you! I am confirming your order…', cooldown: 1500 },

  { role: 'bot', type: 'receipt', content: 'HTML Logo T-shirt (L)\n450 BDT\nCOD\nDelivery: Forjon plaza, Savar, Dhaka', cooldown: 800 },

  { role: 'bot', type: 'text', content: 'Your order has been confirmed! 🎉', cooldown: 4000 }
];




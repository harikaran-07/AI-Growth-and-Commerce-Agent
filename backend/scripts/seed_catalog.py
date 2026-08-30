"""
Product Catalog Seed Script
Generates 10,000+ realistic products across multiple categories.
Supports: seed, clear, reset commands.

Usage:
    python -m backend.seed_catalog seed
    python -m backend.seed_catalog clear
    python -m backend.seed_catalog reset
"""
import asyncio
import sys
import os
import random
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import engine, Base, async_session
from models.models import Merchant, Product, ProductRelationship, Policy
import uuid


def gen_uuid():
    return str(uuid.uuid4())


def make_sku(category, name, idx):
    """Generate deterministic SKU from product name."""
    h = hashlib.md5(f"{category}:{name}:{idx}".encode()).hexdigest()[:8].upper()
    return f"MF-{category[:3].upper()}-{h}"


# ============================================================
# PRODUCT CATALOG DATA
# ============================================================

CATALOG = {
    "Electronics": {
        "Smartphones": {
            "Apple": [("iPhone 15", 79900, 25), ("iPhone 15 Pro", 134900, 15), ("iPhone 14", 64900, 30), ("iPhone SE", 49900, 20)],
            "Samsung": [("Galaxy S24 Ultra", 129999, 20), ("Galaxy S24", 74999, 25), ("Galaxy A54", 38999, 35), ("Galaxy M34", 18999, 40)],
            "OnePlus": [("OnePlus 12", 64999, 20), ("OnePlus Nord CE4", 24999, 30), ("OnePlus 11R", 39999, 25)],
            "Xiaomi": [("Redmi Note 13 Pro", 23999, 40), ("POCO X6 Pro", 26999, 30), ("Mi 14", 69999, 15)],
            "Realme": [("Realme GT 6T", 21999, 35), ("Realme 12 Pro", 29999, 25)],
            "Google": [("Pixel 8", 75999, 15), ("Pixel 8a", 39999, 20)],
        },
        "Laptops": {
            "HP": [("HP Pavilion 15", 54999, 20), ("HP Victus Gaming", 64999, 15), ("HP EliteBook 840", 99999, 10)],
            "Dell": [("Dell Inspiron 15", 49999, 20), ("Dell XPS 13", 89999, 10), ("Dell G15 Gaming", 74999, 15)],
            "Lenovo": [("IdeaPad Slim 5", 44999, 25), ("Legion 5 Gaming", 79999, 15), ("ThinkPad X1 Carbon", 129999, 8)],
            "ASUS": [("ASUS VivoBook 14", 39999, 25), ("ASUS ROG Strix G16", 109999, 10), ("ASUS ZenBook 14", 69999, 15)],
            "Acer": [("Acer Aspire 5", 36999, 25), ("Acer Nitro V Gaming", 69999, 15)],
            "MSI": [("MSI Katana 15", 74999, 10), ("MSI Modern 14", 44999, 15)],
        },
        "Tablets": {
            "Apple": [("iPad 10th Gen", 44900, 20), ("iPad Air M2", 59900, 15), ("iPad Mini", 49900, 12)],
            "Samsung": [("Galaxy Tab S9", 74999, 15), ("Galaxy Tab A9", 17999, 30)],
            "Lenovo": [("Lenovo Tab P12", 29999, 20)],
        },
        "Headphones": {
            "Sony": [("Sony WH-1000XM5", 29990, 15), ("Sony WF-1000XM5", 24990, 20), ("Sony WH-CH720N", 9990, 25)],
            "JBL": [("JBL Tune 770NC", 7999, 25), ("JBL Live Pro 2", 12999, 20), ("JBL Tune 230NC", 5999, 30)],
            "boAt": [("boAt Rockerz 551", 1799, 40), ("boAt Airdopes 141", 1299, 50), ("boAt Nirvanaa", 4999, 25)],
            "Apple": [("AirPods Pro 2", 24900, 15), ("AirPods 3", 19900, 20), ("AirPods Max", 59900, 8)],
            "Samsung": [("Galaxy Buds2 Pro", 17999, 15)],
            "Sennheiser": [("Sennheiser Momentum 4", 24990, 10), ("Sennheiser HD 560S", 9990, 12)],
        },
        "Speakers": {
            "JBL": [("JBL Flip 6", 11999, 20), ("JBL Charge 5", 17999, 15), ("JBL Go 3", 3999, 30)],
            "Sony": [("Sony SRS-XB100", 4990, 25), ("Sony SRS-XB33", 12990, 15)],
            "Marshall": [("Marshall Emberton II", 16999, 10), ("Marshall Acton III", 27999, 8)],
            "boAt": [("boAt Stone 1200", 5999, 30), ("boAt Stone 350", 2999, 35)],
        },
        "Cameras": {
            "Canon": [("Canon EOS R50", 74999, 10), ("Canon EOS R100", 44999, 12)],
            "Sony": [("Sony Alpha 6400", 74990, 8), ("Sony ZV-E10 II", 69990, 10)],
            "GoPro": [("GoPro Hero 12", 41500, 12), ("GoPro Hero 12 Black", 45000, 10)],
        },
        "Wearables": {
            "Apple": [("Apple Watch SE", 29900, 15), ("Apple Watch Series 9", 44900, 12)],
            "Samsung": [("Galaxy Watch 6", 27999, 15), ("Galaxy Watch FE", 14999, 20)],
            "Amazfit": [("Amazfit GTR 4", 14999, 20), ("Amazfit T-Rex 3", 19999, 15)],
            "Noise": [("Noise ColorFit Pro 5", 3499, 30), ("Noise Force Plus", 1999, 35)],
        },
        "Keyboards": {
            "Logitech": [("Logitech MX Keys S", 9995, 15), ("Logitech K380", 3995, 25), ("Logitech G Pro X", 12999, 12)],
            "Razer": [("Razer Huntsman V3 Pro", 17999, 10), ("Razer BlackWidow V4", 14999, 10)],
            "Cosmic Byte": [("Cosmic Byte CB-GK-18", 1999, 30), ("Cosmic Byte Firefly", 2499, 25)],
        },
        "Mice": {
            "Logitech": [("Logitech MX Master 3S", 8495, 15), ("Logitech G502 X", 7995, 12)],
            "Razer": [("Razer DeathAdder V3", 6999, 12), ("Razer Viper V2 Pro", 12999, 10)],
            "Cosmic Byte": [("Cosmic Byte G21", 999, 35), ("Cosmic Byte Menace", 1499, 30)],
        },
        "Power Banks": {
            "Ambrane": [("Ambrane 20000mAh", 1499, 30), ("Ambrane 10000mAh", 899, 35)],
            "Mi": [("Mi Power Bank 3i 20000mAh", 1799, 25)],
            "Syska": [("Syska 10000mAh", 999, 30)],
        },
        "Chargers": {
            "OnePlus": [("OnePlus 100W SUPERVOOC", 3999, 20), ("OnePlus 80W Adapter", 2999, 25)],
            "Samsung": [("Samsung 25W Charger", 1999, 25), ("Samsung 45W Charger", 3499, 20)],
            "Ambrane": [("Ambrane 20W Fast Charger", 699, 35)],
        },
        "Cables": {
            "Ambrane": [("Ambrane USB-C 1.5m", 299, 40), ("Ambrane Lightning Cable", 399, 30)],
            "Belkin": [("Belkin USB-C to C 2m", 999, 20)],
        },
        "Routers": {
            "TP-Link": [("TP-Link Archer AX55", 4999, 15), ("TP-Link Archer C6", 2999, 20)],
            "ASUS": [("ASUS RT-AX58U", 12999, 10)],
        },
        "Storage": {
            "Samsung": [("Samsung T7 500GB SSD", 5499, 15), ("Samsung 980 PRO 1TB", 10999, 12)],
            "SanDisk": [("SanDisk Ultra 128GB USB", 699, 30), ("SanDisk Extreme 256GB", 1999, 25)],
            "WD": [("WD Blue 1TB SSD", 5999, 15)],
        },
        "TVs": {
            "Samsung": [("Samsung 55\" Crystal 4K", 44999, 10), ("Samsung 43\" Smart TV", 29999, 15)],
            "LG": [("LG 55\" OLED 4K", 99999, 8), ("LG 43\" Smart LED", 27999, 15)],
            "Mi": [("Mi TV 55\" 4K", 39999, 12), ("Mi TV 43\" FHD", 24999, 15)],
        },
    },
    "Supermarket": {
        "Rice & Grains": {
            "India Gate": [("India Gate Basmati 5kg", 599, 50), ("India Gate Basmati 1kg", 149, 60)],
            "Daawat": [("Daawat Super Basmati 5kg", 549, 45), ("Daawat Biryani 1kg", 199, 50)],
            "Fortune": [("Fortune Basmati 1kg", 139, 55)],
            "Tata Sampann": [("Tata Sampann Rice 1kg", 99, 60)],
        },
        "Dals & Pulses": {
            "Tata Sampann": [("Tata Toor Dal 1kg", 199, 40), ("Tata Moong Dal 1kg", 179, 40)],
            "Fortune": [("Fortune Chana Dal 1kg", 149, 45)],
            "Daawat": [("Daawat Urad Dal 1kg", 169, 35)],
        },
        "Cooking Oil": {
            "Fortune": [("Fortune Sunlite 1L", 169, 50), ("Fortune Sunflower 5L", 749, 30), ("Fortune Rice Bran 1L", 189, 45)],
            "Saffola": [("Saffola Gold 1L", 229, 40), ("Saffola Total 1L", 249, 35)],
            "Saffola": [("Saffola Active 1L", 199, 40)],
        },
        "Spices": {
            "Everest": [("Everest Turmeric 100g", 59, 60), ("Everest Garam Masala 50g", 69, 55), ("Everest Red Chili 100g", 49, 55)],
            "MDH": [("MDH Chana Masala 100g", 79, 50), ("MDH Kitchen King 100g", 89, 50)],
            "Catch": [("Catch Sabji Masala 100g", 55, 55)],
        },
        "Snacks": {
            "Haldiram": [("Haldiram Aloo Bhujia 200g", 69, 50), ("Haldiram Mixture 200g", 59, 50), ("Haldiram Nagpur Mixture 200g", 79, 45)],
            "Kurkure": [("Kurkure Masala Munch 90g", 20, 60), ("Kurkure Green Chutney 90g", 20, 55)],
            "Lay's": [("Lay's Classic Salted 52g", 20, 60), ("Lay's Magic Masala 52g", 20, 60), ("Lay's American Cream 52g", 20, 55)],
            "Balaji": [("Balaji Wafers Salted 50g", 10, 65), ("Balaji Masala Crunch 50g", 10, 60)],
        },
        "Biscuits": {
            "Parle": [("Parle-G 80g", 10, 70), ("Parle Monaco 75g", 25, 55)],
            "Britannia": [("Britannia Good Day 75g", 30, 55), ("Britannia Marie Gold 250g", 55, 50), ("Britannia Tiger 250g", 45, 50)],
            "Oreo": [("Oreo Original 300g", 60, 50), ("Oreo Choco Cream 300g", 60, 50)],
        },
        "Beverages": {
            "Bisleri": [("Bisleri 1L", 20, 70), ("Bisleri 2L", 35, 60)],
            "Sting": [("Sting Energy 250ml", 20, 50)],
            "Paper Boat": [("Paper Boat Aam Panna 200ml", 30, 40), ("Paper Boat Jaljeera 200ml", 30, 40)],
        },
        "Tea & Coffee": {
            "Tata Tea": [("Tata Tea Gold 250g", 139, 45), ("Tata Tea Chai Kings 1kg", 449, 30)],
            "Brooke Bond": [("Brooke Bond Red Label 250g", 99, 50), ("Lipton Green Tea 100 bags", 399, 25)],
            "Nescafe": [("Nescafe Classic 100g", 220, 40), ("Nescafe Sunrise 50g", 110, 45)],
            "Blue Tokai": [("Blue Tokai Vienna Roast 250g", 425, 20)],
        },
        "Dairy": {
            "Amul": [("Amul Butter 100g", 56, 50), ("Amul Cheese 200g", 90, 40), ("Amul Ghee 1L", 599, 30)],
            "Mother Dairy": [("Mother Dairy Milk 500ml", 32, 60), ("Mother Dairy Curd 400g", 40, 45)],
        },
        "Noodles & Pasta": {
            "Maggi": [("Maggi 2-Minute Noodles 70g", 14, 70), ("Maggi Masala Noodles 4-pack", 56, 55)],
            "Yippee": [("Yippee Noodles 60g", 12, 65)],
            "Pasta": [("Saffola Oodles 230g", 49, 40)],
        },
    },
    "Home & Kitchen": {
        "Cookware": {
            "Prestige": [("Prestige Frying Pan 24cm", 599, 25), ("Prestige Pressure Cooker 5L", 1699, 20), ("Prestige Induction Cooktop", 2499, 15)],
            "Hawkins": [("Hawkins Pressure Cooker 3L", 1299, 25), ("Hawkins Futura Kadhai", 1199, 20)],
            "Pigeon": [("Pigeon Cookware Set", 1999, 15), ("Pigeon Kettle 1.5L", 699, 25)],
        },
        "Kitchen Appliances": {
            "Philips": [("Philips Mixer Grinder 750W", 3999, 15), ("Philips Air Fryer 4.1L", 9999, 10)],
            "Bajaj": [("Bajaj Mixer Grinder 500W", 2499, 20), ("Bajaj Juicer 500W", 2999, 15)],
            "Butterfly": [("Butterfly Mixer Grinder 750W", 2999, 18)],
            "Preethi": [("Preethi Blue Leaf Mixer 750W", 3499, 15)],
        },
        "Storage & Organization": {
            "Generic": [("Storage Container Set 6pc", 599, 30), ("Water Bottle Steel 1L", 399, 35), ("Lunch Box Steel", 499, 25)],
        },
        "Lighting": {
            "Philips": [("Philips LED Bulb 9W", 99, 50), ("Philips LED Batten 2ft", 299, 30)],
            "Wipro": [("Wipro LED Bulb 12W", 119, 45)],
        },
    },
    "Personal Care": {
        "Shampoo": {
            "Head & Shoulders": [("H&S Anti-Dandruff 400ml", 399, 35), ("H&S Lemon Fresh 180ml", 189, 40)],
            "Dove": [("Dove Hair Fall Rescue 340ml", 399, 30), ("Dove Oxygen Moisture 340ml", 349, 30)],
            "Pantene": [("Pantene Advanced Hair 400ml", 349, 35)],
        },
        "Soap": {
            "Dettol": [("Dettol Original 75g", 42, 50), ("Dettol Cool 75g", 45, 45)],
            "Dove": [("Dove Cream Beauty Bar 100g", 65, 40)],
            "Pears": [("Pears Pure 125g", 75, 40)],
        },
        "Toothpaste": {
            "Colgate": [("Colgate MaxFresh 150g", 99, 45), ("Colgate Strong Teeth 150g", 79, 50)],
            "Sensodyne": [("Sensodyne Repair 75g", 149, 35), ("Sensodyne Fresh Mint 75g", 129, 35)],
        },
        "Skincare": {
            "Nivea": [("Nivea Soft Moisturizer 100ml", 199, 35), ("Nivea Men Face Wash 100ml", 179, 30)],
            "Mamaearth": [("Mamaearth Vitamin C Face Serum 30ml", 599, 25), ("Mamaearth Ubtan Face Wash 150ml", 349, 25)],
            "Plum": [("Plum Green Tea Face Wash 200ml", 345, 25)],
        },
    },
    "Office & School": {
        "Notebooks": {
            "Classmate": [("Classmate Pulse A4 200pg", 149, 40), ("Classmate Octane A5 172pg", 89, 45)],
            "Camlin": [("Camlin Notebook A5 180pg", 69, 45)],
        },
        "Pens": {
            "Cello": [("Cello Butterflow Ballpoint 10pc", 99, 40), ("Cello Pinpoint Gel 5pc", 75, 35)],
            "Reynolds": [("Reynolds Trimax 5pc", 125, 30)],
            "Pilot": [("Pilot V5 Hi-Tecpoint 3pc", 165, 25)],
        },
        "Bags": {
            "Safari": [("Safari Backpack 40L", 1499, 20), ("Safari Laptop Bag 15.6\"", 1299, 20)],
            "Wildcraft": [("Wildcraft Backpack 32L", 1999, 15), ("Wildcraft Laptop Bag", 1699, 15)],
        },
    },
    "Fitness": {
        "Equipment": {
            "Boldfit": [("Resistance Bands Set 5pc", 599, 30), ("Yoga Mat 6mm", 699, 25)],
            "Strauss": [("Dumbbells 5kg Pair", 1299, 20), ("Skipping Rope", 299, 35)],
            "Cosco": [("Cosco Cricket Bat", 899, 20)],
        },
        "Bottles": {
            "Milton": [("Milton Thermosteel 750ml", 599, 30), ("Milton Alpha 1L", 799, 25)],
            "Nalgene": [("Nalgene Wide Mouth 1L", 1299, 15)],
        },
    },
    "Gaming": {
        "Controllers": {
            "Xbox": [("Xbox Wireless Controller", 5999, 15), ("Xbox Elite Controller Series 2", 17999, 8)],
            "PlayStation": [("DualSense Controller PS5", 5999, 15)],
            "Redgear": [("Redgear Pro Wireless", 1999, 25)],
        },
        "Accessories": {
            "Logitech": [("Logitech G502 Mouse", 4995, 12), ("Logitech G435 Headset", 5995, 15)],
            "Ant Esports": [("Ant Esports KM500 Gaming Combo", 2999, 20)],
        },
    },
}


# Variants to multiply products
COLORS = ["Black", "White", "Blue", "Red", "Silver", "Green", "Pink", "Grey", "Gold", "Purple"]
SIZES = ["Small", "Medium", "Large", "XL", "XXL"]
WEIGHTS = ["100g", "200g", "250g", "500g", "1kg", "2kg", "5kg"]
BOTTLE_SIZES = ["200ml", "250ml", "500ml", "1L", "1.5L", "2L"]

# Additional product generators to reach 10K+
EXTRA_ELECTRONICS = [
    ("USB Hub 4-Port", 399, 30), ("USB Hub 7-Port", 899, 20),
    ("Webcam HD 1080p", 1999, 25), ("Webcam 4K Pro", 5999, 10),
    ("Microphone Condenser", 2999, 15), ("Microphone USB", 1499, 20),
    ("Screen Protector Tempered Glass", 299, 50), ("Phone Case Silicone", 399, 45),
    ("Phone Case Wallet", 699, 30), ("Phone Ring Holder", 149, 55),
    ("Laptop Stand Aluminum", 1299, 25), ("Laptop Stand Adjustable", 899, 30),
    ("HDMI Cable 2m", 399, 35), ("HDMI Cable 5m", 699, 25),
    ("DisplayPort Cable 2m", 599, 20),
    ("Wireless Earbuds Budget", 999, 40), ("Wireless Earbuds Premium", 3999, 20),
    ("Bluetooth Speaker Mini", 1999, 25), ("Bluetooth Speaker Party", 7999, 15),
    ("TV Wall Mount Bracket", 999, 25), ("Surge Protector 6-Outlet", 599, 30),
    ("UPS 600VA", 3999, 15), ("UPS 1100VA", 6999, 12),
    ("Smart Plug WiFi", 999, 25), ("Smart Bulb RGB", 699, 30),
    ("Smart Speaker Alexa", 4999, 15), ("Smart Display", 8999, 10),
    ("Desk Lamp LED", 799, 30), ("Monitor Light Bar", 2499, 20),
    ("Ethernet Cable Cat6 2m", 199, 40), ("Ethernet Cable Cat6 5m", 349, 30),
    ("Webcam Ring Light", 899, 25), ("Tripod Phone Mount", 499, 30),
    ("Car Phone Mount", 399, 35), ("Car Charger Dual USB", 499, 30),
    ("Wireless Charging Pad", 999, 25), ("Wireless Charging Stand", 1499, 20),
    ("SSD Enclosure USB-C", 899, 25), ("RAM DDR4 8GB", 2499, 15),
    ("RAM DDR4 16GB", 4499, 12), ("CPU Cooler Tower", 1999, 15),
    ("PSU 550W Bronze", 3999, 10), ("PSU 750W Gold", 6999, 8),
    ("Graphics Card Entry", 14999, 8), ("Graphics Card Mid", 29999, 6),
    ("Motherboard B550", 8999, 10), ("Motherboard B660", 10999, 8),
    ("CPU Ryzen 5 7600", 18999, 8), ("CPU Intel i5-13400F", 17999, 8),
    ("PC Cabinet Mid-Tower", 3999, 15), ("PC Cabinet RGB", 5999, 10),
    ("WiFi Adapter USB", 599, 30), ("Bluetooth Adapter USB", 399, 35),
    ("Thermal Paste", 299, 40), ("Cable Management Clips", 199, 45),
    ("Dust Cleaner Spray", 349, 35), ("Anti-Static Wrist Strap", 299, 30),
    ("Car Dashcam 1080p", 3999, 15), ("Dashcam 4K", 8999, 10),
    ("Projector Mini LED", 12999, 10), ("Projector Home 4K", 39999, 5),
    ("E-Reader 6\"", 9999, 8), ("Drone Camera 4K", 24999, 6),
    ("VR Headset Standalone", 29999, 5), ("Mechanical Keyboard RGB", 4999, 20),
    ("Gaming Mouse Pad XL", 999, 25), ("Gaming Chair", 14999, 8),
    ("Desk Organizer", 799, 30), ("Cable Tray Under Desk", 599, 25),
    ("Monitor Arm Single", 2499, 15), ("Monitor Arm Dual", 4999, 10),
    ("Document Scanner Portable", 8999, 8), ("Label Maker", 3999, 12),
]

EXTRA_GROCERY = [
    ("Honey Pure 500g", 299, 35), ("Honey Organic 250g", 399, 25),
    ("Peanut Butter Crunchy 400g", 249, 35), ("Peanut Butter Smooth 400g", 249, 35),
    ("Oats Rolled 1kg", 199, 40), ("Oats Instant Flavored 400g", 149, 35),
    ("Muesli Crunchy 500g", 299, 30), ("Granola Mixed Berries 300g", 399, 25),
    ("Corn Flakes 500g", 179, 40), ("Poha Flattened Rice 500g", 79, 50),
    ("Sooji Semolina 500g", 69, 45), ("Maida All-Purpose Flour 1kg", 49, 55),
    ("Atta Whole Wheat 5kg", 299, 40), ("Atta Multi-Grain 1kg", 129, 35),
    ("Besan Gram Flour 500g", 79, 45), ("Ragi Flour 500g", 99, 35),
    ("Sugar 1kg", 55, 60), ("Sugar Free Sweetener 100 tabs", 149, 30),
    ("Salt Iodized 1kg", 25, 65), ("Black Salt 200g", 35, 40),
    ("Vinegar 500ml", 79, 35), ("Soy Sauce 200ml", 99, 30),
    ("Tomato Ketchup 500g", 99, 45), ("Green Chutney 200g", 79, 30),
    ("Pickle Mango 500g", 129, 40), ("Pickle Mixed 500g", 139, 35),
    ("Papadum 200g", 69, 40), ("Ready to Eat Curry 400g", 149, 30),
    ("Instant Soup Mix 60g", 45, 40), ("Baking Powder 100g", 69, 35),
    ("Cocoa Powder 100g", 199, 25), ("Vanilla Essence 50ml", 149, 30),
    ("Dry Fruits Mixed 200g", 399, 25), ("Almonds 200g", 299, 30),
    ("Cashews 200g", 349, 25), ("Raisins 200g", 199, 30),
    ("Dates 500g", 299, 30), ("Coconut Oil 500ml", 299, 35),
    ("Mustard Oil 1L", 199, 40), ("Olive Oil 500ml", 499, 25),
    ("Ghee 500ml", 349, 30), ("Curd 400g", 40, 45),
    ("Paneer 200g", 80, 40), ("Cream 200ml", 69, 30),
    ("Yogurt Strawberry 100g", 39, 35), ("Lassi Mango 200ml", 35, 35),
    ("Juice Mango 1L", 99, 40), ("Juice Orange 1L", 99, 40),
    ("Green Tea Chamomile 25 bags", 199, 25), ("Green Tea Jasmine 25 bags", 199, 25),
    ("Coffee Decaf 100g", 399, 15), ("Coffee Filter 250g", 249, 30),
]

EXTRA_HOME = [
    ("Broom Standard", 199, 40), ("Mop Flat Cotton", 499, 30),
    ("Bucket 20L", 299, 35), ("Dustpan Plastic", 149, 40),
    ("Towel Set 3pc", 599, 25), ("Bed Sheet Queen", 899, 20),
    ("Pillow Memory Foam", 1299, 15), ("Blanket Winter Queen", 1499, 15),
    ("Curtains Blackout Pair", 1199, 15), ("Door Mat Anti-Slip", 399, 30),
    ("Wall Hook Set 4pc", 299, 35), ("Shoe Rack 3-Tier", 1299, 20),
    ("Hanger Set 20pc", 399, 35), ("Clothes Drying Rack", 1499, 18),
    ("Iron Box 1000W", 899, 25), ("Steam Iron 1800W", 1499, 18),
    ("Garbage Bag Roll 30pc", 199, 35), ("Tissue Box Cover", 299, 25),
    ("Soap Dispenser", 299, 30), ("Toothbrush Holder", 199, 35),
    ("Waste Basket 10L", 299, 30), ("Garden Hose 15m", 999, 15),
    ("Indoor Plant Pot", 399, 25), ("Artificial Plant", 599, 20),
    ("Wall Clock Analog", 699, 20), ("Wall Clock Digital", 999, 15),
    ("Photo Frame Set 3pc", 499, 25), ("Candle Scented", 399, 25),
    ("Diffuser Reed", 599, 20), ("Air Freshener Spray", 199, 35),
    ("Tool Kit 30pc", 1299, 15), ("Screwdriver Set", 499, 25),
    ("Measuring Tape", 149, 35), ("Plunger Heavy Duty", 399, 25),
    ("Drill Machine 500W", 2499, 12), ("LED Strip Light 5m", 499, 30),
]

EXTRA_PERSONAL = [
    ("Face Wash Gentle 150ml", 249, 30), ("Sunscreen SPF50 100ml", 499, 25),
    ("Lip Balm SPF 15", 149, 35), ("Hand Cream 100ml", 299, 30),
    ("Body Lotion 400ml", 399, 25), ("Deodorant Spray 150ml", 249, 35),
    ("Perfume Men 100ml", 799, 20), ("Perfume Women 100ml", 899, 18),
    ("Shaving Cream 200g", 199, 30), ("After Shave Balm 100ml", 299, 25),
    ("Hair Oil Coconut 200ml", 129, 35), ("Hair Oil Amla 200ml", 119, 35),
    ("Hair Gel 150ml", 199, 30), ("Hair Wax 75g", 249, 28),
    ("Face Pack Multani 100g", 149, 25), ("Scrub Face 100g", 199, 25),
    ("Eye Cream 15ml", 599, 15), ("Serum Vitamin C 30ml", 799, 18),
    ("Night Cream 50g", 699, 18), ("Moisturizer SPF 100ml", 449, 25),
    ("Foot Cream 100g", 249, 25), ("Shower Gel 250ml", 299, 30),
    ("Bath Salt 500g", 399, 20), ("Loofah Natural", 199, 30),
    ("Nail Polish Set 6pc", 499, 20), ("Makeup Kit Starter", 1499, 15),
    ("Beard Oil 30ml", 349, 25), ("Beard Wash 100ml", 299, 25),
    ("Comb Set 3pc", 149, 35), ("Hair Brush Boar", 399, 20),
]

EXTRA_FITNESS = [
    ("Kettlebell 8kg", 1499, 15), ("Kettlebell 12kg", 2299, 12),
    ("Yoga Block 2pc", 399, 25), ("Yoga Strap 2.4m", 299, 25),
    ("Foam Roller 45cm", 799, 20), ("Massage Ball Set", 599, 20),
    ("Gym Gloves Training", 499, 25), ("Wrist Wraps 2pc", 399, 25),
    ("Resistance Tube Set", 899, 20), ("Ab Roller Wheel", 499, 25),
    ("Pull-Up Bar Doorway", 1299, 15), ("Boxing Gloves 12oz", 1499, 15),
    ("Punching Bag 4ft", 3999, 8), ("Jump Rope Speed", 349, 30),
    ("Gym Bag Duffel 40L", 999, 20), ("Water Bottle Sport 1L", 499, 30),
    ("Shaker Bottle 700ml", 399, 30), ("Post Workout Towel", 299, 25),
    ("Exercise Bike Indoor", 14999, 6), ("Treadmill Foldable", 29999, 5),
    ("Rowing Machine", 19999, 5), ("Elliptical Trainer", 24999, 5),
]


def generate_all_products():
    """Generate the complete product catalog."""
    products = []
    idx = 0

    for category, subcats in CATALOG.items():
        for subcategory, brands in subcats.items():
            for brand, items in brands.items():
                for name, price, stock in items:
                    idx += 1
                    rating = round(random.uniform(3.0, 5.0), 1)
                    tags_list = [category.lower(), subcategory.lower(), brand.lower()]
                    # Add variant tags
                    if random.random() > 0.5:
                        tags_list.append(random.choice(COLORS[:4]).lower())
                    products.append({
                        "name": name,
                        "description": f"{brand} {name} - High quality {subcategory.lower()} from {brand}",
                        "category": category,
                        "subcategory": subcategory,
                        "brand": brand,
                        "price": price,
                        "currency": "INR",
                        "stock": stock + random.randint(-5, 20),
                        "sku": make_sku(subcategory, name, idx),
                        "rating": rating,
                        "tags": ",".join(tags_list),
                    })

    # Add extra electronics variants
    for name, price, stock in EXTRA_ELECTRONICS:
        idx += 1
        brand = name.split()[0] if len(name.split()) > 1 else "Generic"
        subcat = "Accessories"
        tags_list = ["electronics", "accessories", brand.lower()]
        products.append({
            "name": name,
            "description": f"{name} - Quality electronics accessory",
            "category": "Electronics",
            "subcategory": subcat,
            "brand": brand,
            "price": price,
            "currency": "INR",
            "stock": stock,
            "sku": make_sku(subcat, name, idx),
            "rating": round(random.uniform(3.2, 4.8), 1),
            "tags": ",".join(tags_list),
        })

    # Add extra grocery variants
    for name, price, stock in EXTRA_GROCERY:
        idx += 1
        brand = name.split()[0] if len(name.split()) > 1 else "Generic"
        tags_list = ["supermarket", "grocery", brand.lower()]
        products.append({
            "name": name,
            "description": f"{name} - Quality grocery item",
            "category": "Supermarket",
            "subcategory": "Grocery",
            "brand": brand,
            "price": price,
            "currency": "INR",
            "stock": stock,
            "sku": make_sku("GROCERY", name, idx),
            "rating": round(random.uniform(3.0, 4.9), 1),
            "tags": ",".join(tags_list),
        })

    # Add extra home variants
    for name, price, stock in EXTRA_HOME:
        idx += 1
        brand = name.split()[0] if len(name.split()) > 1 else "Generic"
        tags_list = ["home", "kitchen", brand.lower()]
        products.append({
            "name": name,
            "description": f"{name} - Quality home product",
            "category": "Home & Kitchen",
            "subcategory": "Home",
            "brand": brand,
            "price": price,
            "currency": "INR",
            "stock": stock,
            "sku": make_sku("HOME", name, idx),
            "rating": round(random.uniform(3.0, 4.8), 1),
            "tags": ",".join(tags_list),
        })

    # Add extra personal care variants
    for name, price, stock in EXTRA_PERSONAL:
        idx += 1
        brand = name.split()[0] if len(name.split()) > 1 else "Generic"
        tags_list = ["personal care", brand.lower()]
        products.append({
            "name": name,
            "description": f"{name} - Quality personal care product",
            "category": "Personal Care",
            "subcategory": "Personal Care",
            "brand": brand,
            "price": price,
            "currency": "INR",
            "stock": stock,
            "sku": make_sku("PCARE", name, idx),
            "rating": round(random.uniform(3.0, 4.8), 1),
            "tags": ",".join(tags_list),
        })

    # Add extra fitness variants
    for name, price, stock in EXTRA_FITNESS:
        idx += 1
        brand = name.split()[0] if len(name.split()) > 1 else "Generic"
        tags_list = ["fitness", "gym", brand.lower()]
        products.append({
            "name": name,
            "description": f"{name} - Quality fitness equipment",
            "category": "Fitness",
            "subcategory": "Equipment",
            "brand": brand,
            "price": price,
            "currency": "INR",
            "stock": stock,
            "sku": make_sku("FIT", name, idx),
            "rating": round(random.uniform(3.0, 4.8), 1),
            "tags": ",".join(tags_list),
        })

    # Multiply with color/size/weight variants to reach 10K+
    base_products = list(products)  # copy
    variant_count = 0
    for p in base_products:
        # Color variants for electronics, fashion, personal care
        if p["category"] in ("Electronics", "Personal Care", "Home & Kitchen"):
            for color in random.sample(COLORS, min(4, len(COLORS))):
                variant_count += 1
                products.append({
                    "name": f"{p['name']} ({color})",
                    "description": f"{p['description']} - {color} variant",
                    "category": p["category"],
                    "subcategory": p["subcategory"],
                    "brand": p["brand"],
                    "price": p["price"] + random.choice([0, 0, 0, 50, 100, -50]),
                    "currency": "INR",
                    "stock": random.randint(5, 50),
                    "sku": make_sku(p["subcategory"], p["name"] + color, variant_count),
                    "rating": round(random.uniform(3.0, 5.0), 1),
                    "tags": f"{p['tags']},{color.lower()}",
                })
        # Size/weight variants for supermarket
        elif p["category"] == "Supermarket":
            for weight in random.sample(WEIGHTS, min(3, len(WEIGHTS))):
                variant_count += 1
                price_mult = {"100g": 0.5, "200g": 0.7, "250g": 0.8, "500g": 1.0, "1kg": 1.8, "2kg": 3.2, "5kg": 7.5}
                products.append({
                    "name": f"{p['name']} {weight}",
                    "description": f"{p['description']} - {weight} pack",
                    "category": p["category"],
                    "subcategory": p["subcategory"],
                    "brand": p["brand"],
                    "price": round(p["price"] * price_mult.get(weight, 1.0), 0),
                    "currency": "INR",
                    "stock": random.randint(10, 80),
                    "sku": make_sku(p["subcategory"], p["name"] + weight, variant_count),
                    "rating": round(random.uniform(3.0, 5.0), 1),
                    "tags": f"{p['tags']},{weight}",
                })

    # Generate generic products to fill up to 10K+
    generic_categories = [
        ("Electronics", "Accessories", ["Generic", "TechMax", "Digitize"]),
        ("Supermarket", "Grocery", ["FreshMart", "DailyNeeds", "GreenLeaf"]),
        ("Home & Kitchen", "Home", ["HomeStar", "ComfortPlus", "LivingWell"]),
        ("Personal Care", "Personal Care", ["GlowUp", "FreshFeel", "SkinCare+"]),
        ("Office & School", "Stationery", ["WriteRight", "PaperPlus", "InkWell"]),
        ("Fitness", "Equipment", ["FitLife", "GymPro", "ActiveGear"]),
        ("Gaming", "Accessories", ["GameZone", "ProPlay", "EliteGamer"]),
    ]

    generic_items = [
        "Premium Quality Item", "Essential Daily Product", "Value Pack",
        "Professional Grade", "Economy Choice", "Best Seller",
        "Top Rated", "New Arrival", "Limited Edition", "Classic",
        "Deluxe Version", "Compact Size", "Jumbo Pack", "Family Size",
        "Travel Size", "Mini", "Mega", "Ultra", "Pro", "Max",
    ]

    generic_idx = 0
    for cat, subcat, brands in generic_categories:
        for brand in brands:
            for item_name in generic_items:
                for i in range(20):  # 20 variants per generic item
                    generic_idx += 1
                    price = random.randint(49, 9999)
                    stock = random.randint(5, 100)
                    products.append({
                        "name": f"{brand} {item_name} #{i+1}",
                        "description": f"{brand} {item_name} - Quality {subcat.lower()} product",
                        "category": cat,
                        "subcategory": subcat,
                        "brand": brand,
                        "price": price,
                        "currency": "INR",
                        "stock": stock,
                        "sku": make_sku(subcat, f"{brand}{item_name}{i}", generic_idx),
                        "rating": round(random.uniform(3.0, 5.0), 1),
                        "tags": f"{cat.lower()},{subcat.lower()},{brand.lower()},{item_name.lower().replace(' ', ',')}",
                    })

    return products


def generate_relationships(products):
    """Generate realistic product relationships."""
    relationships = []
    product_map = {}
    for p in products:
        key = f"{p['brand']}:{p['name']}"
        product_map[key] = p

    # Group products by category for cross-selling
    by_category = {}
    for p in products:
        by_category.setdefault(p["category"], []).append(p)

    by_subcat = {}
    for p in products:
        by_subcat.setdefault(p["subcategory"], []).append(p)

    rel_idx = 0
    for cat, cat_products in by_category.items():
        for p in cat_products[:50]:  # First 50 per category get relationships
            # Cross-sell: different subcategory in same category
            cross_candidates = [x for x in cat_products if x["subcategory"] != p["subcategory"] and x["id"] != p["id"]]
            if cross_candidates:
                for cp in random.sample(cross_candidates, min(3, len(cross_candidates))):
                    rel_idx += 1
                    relationships.append({
                        "product_id": p.get("_db_id", p["sku"]),
                        "related_product_id": cp.get("_db_id", cp["sku"]),
                        "relationship_type": random.choice(["cross-sell", "complementary"]),
                        "reason": f"Customers who bought {p['name']} also liked {cp['name']}",
                    })

            # Upsell: same subcategory, higher price
            upsell_candidates = [x for x in by_subcat.get(p["subcategory"], [])
                                if x["price"] > p["price"] and x["id"] != p["id"]]
            if upsell_candidates:
                up = min(upsell_candidates, key=lambda x: x["price"])
                rel_idx += 1
                relationships.append({
                    "product_id": p.get("_db_id", p["sku"]),
                    "related_product_id": up.get("_db_id", up["sku"]),
                    "relationship_type": "upsell",
                    "reason": f"Upgrade to {up['name']} for better features",
                })

    return relationships[:2000]  # Limit to 2000 relationships


async def seed():
    """Seed the database with products."""
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # Create merchant
        merchant = Merchant(
            id="merchant_001",
            name="TechZone Electronics",
            email="admin@techzone.in"
        )
        db.add(merchant)

        # Create policy
        policy = Policy(
            merchant_id="merchant_001",
            max_transaction_amount=3000,
            max_discount_percentage=10,
            payment_requires_approval=True,
            max_retry_attempts=1
        )
        db.add(policy)

        print("Generating products...")
        all_products = generate_all_products()
        print(f"Generated {len(all_products)} products")

        # Batch insert products
        db_products = []
        for p in all_products:
            product = Product(
                name=p["name"],
                description=p["description"],
                category=p["category"],
                subcategory=p.get("subcategory"),
                brand=p.get("brand"),
                price=p["price"],
                currency=p["currency"],
                stock=max(0, p["stock"]),
                sku=p["sku"],
                rating=p["rating"],
                tags=p["tags"],
                is_active=True,
                merchant_id="merchant_001",
            )
            db.add(product)
            db_products.append(product)

        await db.flush()
        print(f"Inserted {len(db_products)} products")

        # Store IDs for relationships
        sku_to_id = {p.sku: p.id for p in db_products}
        sku_to_product = {p.sku: p for p in db_products}

        # Generate and insert relationships
        print("Generating relationships...")
        all_skus = [p["sku"] for p in all_products]
        rel_count = 0

        # Simple relationship generation by category
        by_category = {}
        for i, p in enumerate(all_products):
            cat = p["category"]
            by_category.setdefault(cat, []).append((i, p))

        for cat, items in by_category.items():
            for idx_i, p1 in items[:100]:
                # Cross-sell: different subcategory
                cross = [(idx_j, p2) for idx_j, p2 in items
                        if p2["subcategory"] != p1["subcategory"] and idx_j != idx_i]
                if cross:
                    for _, p2 in random.sample(cross, min(2, len(cross))):
                        if p1["sku"] in sku_to_id and p2["sku"] in sku_to_id:
                            rel = ProductRelationship(
                                product_id=sku_to_id[p1["sku"]],
                                related_product_id=sku_to_id[p2["sku"]],
                                relationship_type=random.choice(["cross-sell", "complementary"]),
                                reason=f"Customers who viewed {p1['name']} also viewed {p2['name']}",
                            )
                            db.add(rel)
                            rel_count += 1

        await db.commit()
        print(f"Inserted {rel_count} relationships")
        print(f"\nDone! Total: {len(db_products)} products, {rel_count} relationships")


async def clear():
    """Clear all products."""
    async with engine.begin() as conn:
        from sqlalchemy import text
        await conn.execute(text("DELETE FROM product_relationships"))
        await conn.execute(text("DELETE FROM cart_items"))
        await conn.execute(text("DELETE FROM carts"))
        await conn.execute(text("DELETE FROM payments"))
        await conn.execute(text("DELETE FROM approvals"))
        await conn.execute(text("DELETE FROM orders"))
        await conn.execute(text("DELETE FROM audit_logs"))
        await conn.execute(text("DELETE FROM agent_sessions"))
        await conn.execute(text("DELETE FROM products"))
        await conn.execute(text("DELETE FROM policies"))
        await conn.execute(text("DELETE FROM customers"))
        await conn.execute(text("DELETE FROM merchants"))
    print("All data cleared.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "seed"
    if cmd == "clear":
        asyncio.run(clear())
    elif cmd == "reset":
        asyncio.run(clear())
        asyncio.run(seed())
    else:
        asyncio.run(seed())

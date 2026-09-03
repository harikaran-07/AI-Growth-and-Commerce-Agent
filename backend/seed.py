"""
Seed script: 10,000+ real products across many categories for AI Growth and Commerce Agent.
Includes cost_price, sales, revenue, margin for each product.
"""
import uuid
import asyncio
import logging
import random
import hashlib

logger = logging.getLogger(__name__)


def _id():
    return str(uuid.uuid4())


def _hash_seed(name):
    return int(hashlib.md5(name.encode()).hexdigest()[:8], 16)


# ──────────────────────────────────────────────────────────
# Product templates: (name, description, category, subcategory, brand, price, stock)
# We'll derive cost_price, sales, revenue, margin from these
# ──────────────────────────────────────────────────────────

ELECTRONICS_PRODUCTS = [
    # Smartphones
    ("iPhone 15 Pro Max", "Apple iPhone 15 Pro Max 256GB", "Electronics", "Smartphones", "Apple", 159900, 30),
    ("Samsung Galaxy S24 Ultra", "Samsung Galaxy S24 Ultra 512GB", "Electronics", "Smartphones", "Samsung", 134999, 25),
    ("OnePlus 12", "OnePlus 12 5G 256GB", "Electronics", "Smartphones", "OnePlus", 64999, 40),
    ("Xiaomi 14", "Xiaomi 14 Leica Camera Phone", "Electronics", "Smartphones", "Xiaomi", 59999, 35),
    ("Google Pixel 8 Pro", "Google Pixel 8 Pro 128GB", "Electronics", "Smartphones", "Google", 89999, 20),
    ("Vivo X100 Pro", "Vivo X100 Pro 512GB", "Electronics", "Smartphones", "Vivo", 79999, 22),
    ("Realme GT 5 Pro", "Realme GT 5 Pro 256GB", "Electronics", "Smartphones", "Realme", 42999, 45),
    ("Nothing Phone 2", "Nothing Phone 2 Transparent Design", "Electronics", "Smartphones", "Nothing", 34999, 30),
    ("Samsung Galaxy A54", "Samsung Galaxy A54 5G 128GB", "Electronics", "Smartphones", "Samsung", 32999, 50),
    ("Redmi Note 13 Pro", "Redmi Note 13 Pro 5G 256GB", "Electronics", "Smartphones", "Xiaomi", 24999, 60),
    ("iPhone 14", "Apple iPhone 14 128GB", "Electronics", "Smartphones", "Apple", 69999, 35),
    ("Samsung Galaxy S23", "Samsung Galaxy S23 128GB", "Electronics", "Smartphones", "Samsung", 54999, 28),
    ("OnePlus Nord CE 3", "OnePlus Nord CE 3 5G 128GB", "Electronics", "Smartphones", "OnePlus", 24999, 40),
    ("iQOO 12", "iQOO 12 5G 256GB", "Electronics", "Smartphones", "iQOO", 52999, 18),
    ("Motorola Edge 40 Pro", "Motorola Edge 40 Pro 5G", "Electronics", "Smartphones", "Motorola", 45999, 20),
    ("Lava Blaze Pro 5G", "Lava Blaze Pro 5G Budget Phone", "Electronics", "Smartphones", "Lava", 12999, 70),
    ("Nokia G42 5G", "Nokia G42 5G Mid-Range Phone", "Electronics", "Smartphones", "Nokia", 17999, 35),
    ("Poco X6 Pro", "Poco X6 Pro 5G 256GB", "Electronics", "Smartphones", "Poco", 26999, 42),
    ("Honor 90", "Honor 90 5G Camera Phone", "Electronics", "Smartphones", "Honor", 37999, 25),
    ("Infinix Zero 30", "Infinix Zero 30 5G 256GB", "Electronics", "Smartphones", "Infinix", 22999, 48),

    # Laptops
    ("MacBook Air M3", "Apple MacBook Air 15-inch M3 16GB", "Electronics", "Laptops", "Apple", 164900, 15),
    ("Dell XPS 15", "Dell XPS 15 Intel i7 16GB 512GB SSD", "Electronics", "Laptops", "Dell", 134999, 12),
    ("HP Spectre x360", "HP Spectre x360 14 OLED Touch", "Electronics", "Laptops", "HP", 119999, 18),
    ("Lenovo ThinkPad X1 Carbon", "ThinkPad X1 Carbon Gen 11 i7", "Electronics", "Laptops", "Lenovo", 149999, 10),
    ("ASUS ROG Strix G16", "ASUS ROG Strix G16 RTX 4070", "Electronics", "Laptops", "ASUS", 109999, 20),
    ("Acer Nitro 5", "Acer Nitro 5 RTX 3060 16GB", "Electronics", "Laptops", "Acer", 79999, 25),
    ("Lenovo IdeaPad Slim 5", "Lenovo IdeaPad 14 AMD Ryzen 7", "Electronics", "Laptops", "Lenovo", 64999, 30),
    ("HP Pavilion 15", "HP Pavilion 15 AMD Ryzen 5", "Electronics", "Laptops", "HP", 54999, 35),
    ("ASUS Zenbook 14", "ASUS Zenbook 14 OLED i5", "Electronics", "Laptops", "ASUS", 74999, 22),
    ("MacBook Pro 14 M3 Pro", "Apple MacBook Pro 14-inch M3 Pro", "Electronics", "Laptops", "Apple", 199900, 8),
    ("Dell Inspiron 15", "Dell Inspiron 15 AMD Ryzen 5 16GB", "Electronics", "Laptops", "Dell", 49999, 40),
    ("HP 15s", "HP 15s AMD Ryzen 3 8GB", "Electronics", "Laptops", "HP", 39999, 45),
    ("Lenovo LOQ 15", "Lenovo LOQ 15 RTX 3050 Gaming", "Electronics", "Laptops", "Lenovo", 69999, 22),
    ("ASUS TUF Gaming A15", "ASUS TUF Gaming A15 Ryzen 7 RTX 4060", "Electronics", "Laptops", "ASUS", 89999, 16),
    ("Acer Aspire 5", "Acer Aspire 5 Intel i5 8GB", "Electronics", "Laptops", "Acer", 44999, 35),

    # Tablets
    ("iPad Pro 12.9 M2", "Apple iPad Pro 12.9-inch M2 256GB", "Electronics", "Tablets", "Apple", 112900, 15),
    ("Samsung Galaxy Tab S9", "Samsung Galaxy Tab S9 11-inch 128GB", "Electronics", "Tablets", "Samsung", 74999, 20),
    ("OnePlus Pad", "OnePlus Pad 256GB WiFi", "Electronics", "Tablets", "OnePlus", 37999, 25),
    ("Xiaomi Pad 6", "Xiaomi Pad 6 144Hz 128GB", "Electronics", "Tablets", "Xiaomi", 26999, 30),
    ("Lenovo Tab M10 Plus", "Lenovo Tab M10 Plus Gen 3 64GB", "Electronics", "Tablets", "Lenovo", 15999, 40),
    ("iPad Air M1", "Apple iPad Air M1 64GB WiFi", "Electronics", "Tablets", "Apple", 59900, 18),
    ("Realme Pad 2", "Realme Pad 2 11-inch 128GB", "Electronics", "Tablets", "Realme", 17999, 35),
    ("Honor Pad X9", "Honor Pad X9 11.5-inch 128GB", "Electronics", "Tablets", "Honor", 22999, 28),
    ("Samsung Galaxy Tab A9", "Samsung Galaxy Tab A9 8.7-inch 64GB", "Electronics", "Tablets", "Samsung", 14999, 45),
    ("Lenovo Tab P12 Pro", "Lenovo Tab P12 Pro AMOLED 256GB", "Electronics", "Tablets", "Lenovo", 69999, 12),

    # Monitors
    ("LG UltraFine 27UK850", "LG 27-inch 4K UHD Monitor HDR10", "Electronics", "Monitors", "LG", 42999, 20),
    ("Dell S2722QC", "Dell 27-inch 4K USB-C Monitor", "Electronics", "Monitors", "Dell", 34999, 25),
    ("Samsung Odyssey G5", "Samsung 27-inch 165Hz Curved Gaming", "Electronics", "Monitors", "Samsung", 24999, 30),
    ("BenQ EW3280U", "BenQ 32-inch 4K Entertainment Monitor", "Electronics", "Monitors", "BenQ", 39999, 15),
    ("ASUS ProArt PA278QV", "ASUS 27-inch WQHD ProArt Monitor", "Electronics", "Monitors", "ASUS", 29999, 18),
    ("HP E243m", "HP 24-inch FHD Monitor IPS", "Electronics", "Monitors", "HP", 14999, 40),
    ("Acer Nitro XV272U", "Acer 27-inch WQHD 170Hz Gaming", "Electronics", "Monitors", "Acer", 27999, 22),
    ("Lenovo L24q-30", "Lenovo 23.8-inch QHD IPS Monitor", "Electronics", "Monitors", "Lenovo", 16999, 35),
    ("Gigabyte M28U", "Gigabyte 28-inch 4K 144Hz Gaming", "Electronics", "Monitors", "Gigabyte", 36999, 16),
    ("Philips 27E1N5600", "Philips 27-inch QHD IPS Monitor", "Electronics", "Monitors", "Philips", 17999, 28),

    # Keyboards
    ("Logitech MX Keys S", "Logitech MX Keys S Wireless Keyboard", "Electronics", "Keyboards", "Logitech", 11995, 40),
    ("Keychron Q1 Pro", "Keychron Q1 Pro QMK Wireless 75%", "Electronics", "Keyboards", "Keychron", 18999, 20),
    ("Razer BlackWidow V4", "Razer BlackWidow V4 Mechanical RGB", "Electronics", "Keyboards", "Razer", 16999, 15),
    ("Corsair K100 RGB", "Corsair K100 RGB Mechanical Keyboard", "Electronics", "Keyboards", "Corsair", 19999, 12),
    ("HP K2500", "HP K2500 Wireless Keyboard Mouse Combo", "Electronics", "Keyboards", "HP", 1999, 50),
    ("Zebronics Zeb-MK2000", "Zebronics Multimedia USB Keyboard", "Electronics", "Keyboards", "Zebronics", 599, 80),
    ("Redgear Shadow Blade", "Redgear Mechanical Keyboard RGB", "Electronics", "Keyboards", "Redgear", 2499, 45),
    ("Logitech MK270", "Logitech MK270 Wireless Keyboard Mouse", "Electronics", "Keyboards", "Logitech", 2495, 60),
    ("Cosmic Byte CB-GK-18", "Cosmic Byte Firefly RGB Mechanical", "Electronics", "Keyboards", "Cosmic Byte", 1999, 35),
    ("Ant Esports MK3400W Pro", "Ant Esports Wireless Mechanical", "Electronics", "Keyboards", "Ant Esports", 3499, 25),

    # Mice
    ("Logitech MX Master 3S", "Logitech MX Master 3S Ergonomic Mouse", "Electronics", "Mice", "Logitech", 8995, 30),
    ("Razer DeathAdder V3", "Razer DeathAdder V3 Gaming Mouse", "Electronics", "Mice", "Razer", 6999, 25),
    ("Logitech G Pro X Superlight", "Logitech G Pro X Superlight 2 Wireless", "Electronics", "Mice", "Logitech", 14995, 15),
    ("SteelSeries Rival 5", "SteelSeries Rival 5 Gaming Mouse", "Electronics", "Mice", "SteelSeries", 5999, 20),
    ("HP Wireless Mouse 200", "HP Wireless Mouse 200 2.4GHz", "Electronics", "Mice", "HP", 699, 75),
    ("Redgear Cloak Gaming Mouse", "Redgear Cloak RGB Gaming Mouse Wired", "Electronics", "Mice", "Redgear", 549, 60),
    ("Zebronics Zeb-Transformer", "Zebronics Gaming Mouse RGB 7 Buttons", "Electronics", "Mice", "Zebronics", 899, 55),
    ("Cosmic Byte G21", "Cosmic Byte G21 Gaming Mouse Wireless", "Electronics", "Mice", "Cosmic Byte", 1299, 40),
    ("Lenovo Legion M600", "Lenovo Legion M600 Wireless Gaming", "Electronics", "Mice", "Lenovo", 4999, 22),
    ("BenQ Zowie EC2", "BenQ Zowie EC2 Ergonomic Gaming", "Electronics", "Mice", "BenQ", 5499, 18),

    # Headphones
    ("Sony WH-1000XM5", "Sony WH-1000XM5 Wireless NC Headphones", "Electronics", "Headphones", "Sony", 29990, 25),
    ("JBL Tune 770NC", "JBL Tune 770NC Wireless Over-Ear", "Electronics", "Headphones", "JBL", 5999, 40),
    ("boAt Rockerz 551", "boAt Rockerz 551 Bluetooth Headphones", "Electronics", "Headphones", "boAt", 1799, 60),
    ("Sennheiser HD 450BT", "Sennheiser HD 450BT ANC Wireless", "Electronics", "Headphones", "Sennheiser", 9990, 20),
    ("Audio-Technica ATH-M50x", "Audio-Technica ATH-M50x Studio Monitor", "Electronics", "Headphones", "Audio-Technica", 14999, 15),
    ("JBL Tune 510BT", "JBL Tune 510BT On-Ear Wireless", "Electronics", "Headphones", "JBL", 3999, 50),
    ("boAt Nirvanaa 751 ANC", "boAt Nirvanaa 751 ANC Hybrid Headphones", "Electronics", "Headphones", "boAt", 3999, 45),
    ("Zebronics Zeb-Thunder", "Zebronics Zeb-Thunder Gaming Headphones", "Electronics", "Headphones", "Zebronics", 799, 70),
    ("Marshall Major IV", "Marshall Major IV On-Ear Wireless", "Electronics", "Headphones", "Marshall", 14999, 12),
    ("Skullcandy Crusher ANC 2", "Skullcandy Crusher ANC 2 Wireless NC", "Electronics", "Headphones", "Skullcandy", 12999, 18),

    # Earphones
    ("Sony WF-1000XM5", "Sony WF-1000XM5 TWS Earbuds", "Electronics", "Earphones", "Sony", 27990, 20),
    ("boAt Airdopes 141", "boAt Airdopes 141 TWS Earbuds", "Electronics", "Earphones", "boAt", 1299, 80),
    ("JBL Tune Beam", "JBL Tune Beam TWS Earbuds ANC", "Electronics", "Earphones", "JBL", 7999, 30),
    ("Samsung Galaxy Buds2 Pro", "Samsung Galaxy Buds2 Pro TWS", "Electronics", "Earphones", "Samsung", 17999, 22),
    ("OnePlus Buds Pro 2", "OnePlus Buds Pro 2 TWS ANC", "Electronics", "Earphones", "OnePlus", 9999, 28),
    ("Realme Buds Air 5 Pro", "Realme Buds Air 5 Pro 50dB ANC", "Electronics", "Earphones", "Realme", 4999, 40),
    ("boAt Airdopes 411", "boAt Airdopes 411 ANC TWS", "Electronics", "Earphones", "boAt", 1999, 65),
    ("Noise Buds Solo", "Noise Buds Solo 360 ANC TWS", "Electronics", "Earphones", "Noise", 2499, 50),
    ("Apple AirPods Pro 2", "Apple AirPods Pro 2nd Gen USB-C", "Electronics", "Earphones", "Apple", 24900, 15),
    ("Jabra Elite 4", "Jabra Elite 4 TWS ANC Earbuds", "Electronics", "Earphones", "Jabra", 7999, 25),

    # Speakers
    ("JBL Charge 5", "JBL Charge 5 Portable BT Speaker", "Electronics", "Speakers", "JBL", 17999, 25),
    ("Sony SRS-XB100", "Sony SRS-XB100 Wireless Speaker", "Electronics", "Speakers", "Sony", 4990, 35),
    ("Marshall Emberton II", "Marshall Emberton II Portable Speaker", "Electronics", "Speakers", "Marshall", 16999, 15),
    ("boAt Stone 1200", "boAt Stone 1200 14W BT Speaker", "Electronics", "Speakers", "boAt", 3999, 50),
    ("JBL Go 3", "JBL Go 3 Portable BT Speaker", "Electronics", "Speakers", "JBL", 3999, 60),
    ("Ultimate Ears Boom 3", "UE Boom 3 360 Wireless Speaker", "Electronics", "Speakers", "Ultimate Ears", 15999, 18),
    ("Home Speaker 500", "Amazon Echo Studio Smart Speaker", "Electronics", "Speakers", "Amazon", 22999, 12),
    ("Sony HT-S400", "Sony HT-S400 2.1ch Soundbar", "Electronics", "Speakers", "Sony", 22990, 20),
    ("JBL Bar 2.0", "JBL Bar 2.0 All-in-One Soundbar", "Electronics", "Speakers", "JBL", 14999, 22),
    ("Redmi Soundbar 2.0", "Redmi Soundbar 2.0 with Subwoofer", "Electronics", "Speakers", "Xiaomi", 4999, 40),

    # Webcams
    ("Logitech C920s HD", "Logitech C920s HD Pro Webcam", "Electronics", "Webcams", "Logitech", 5995, 40),
    ("Razer Kiyo Pro", "Razer Kiyo Pro 1080p Webcam HDR", "Electronics", "Webcams", "Razer", 11999, 15),
    ("Poly Studio P5", "Poly Studio P5 USB Webcam", "Electronics", "Webcams", "Poly", 7999, 25),
    ("Logitech Brio 300", "Logitech Brio 300 1080p Webcam", "Electronics", "Webcams", "Logitech", 4995, 35),
    ("HP Wide Vision HD", "HP Wide Vision HD Webcam F2200", "Electronics", "Webcams", "HP", 2999, 45),
    ("Zebronics Zeb-Jaguar", "Zebronics USB HD Webcam 1080p", "Electronics", "Webcams", "Zebronics", 999, 60),
    ("Logitech Rally Camera", "Logitech Rally 4K PTZ Conference Camera", "Electronics", "Webcams", "Logitech", 129999, 5),
    ("Anker PowerConf S330", "Anker PowerConf S330 Webcam Speaker", "Electronics", "Webcams", "Anker", 8999, 20),
    ("Insta360 Link", "Insta360 Link AI Webcam 4K", "Electronics", "Webcams", "Insta360", 19999, 10),
    ("Elgato Facecam MK.2", "Elgato Facecam MK.2 1080p60", "Electronics", "Webcams", "Elgato", 14999, 12),

    # SSDs
    ("Samsung T7 1TB", "Samsung T7 Portable SSD 1TB USB 3.2", "Electronics", "SSDs", "Samsung", 10999, 30),
    ("WD Black SN850X 1TB", "WD Black SN850X NVMe SSD 1TB", "Electronics", "SSDs", "Western Digital", 9999, 25),
    ("Crucial P3 Plus 1TB", "Crucial P3 Plus NVMe SSD 1TB", "Electronics", "SSDs", "Crucial", 6499, 40),
    ("Kingston NV2 1TB", "Kingston NV2 NVMe SSD 1TB", "Electronics", "SSDs", "Kingston", 5499, 45),
    ("SanDisk Extreme Pro 1TB", "SanDisk Extreme Pro Portable SSD 1TB", "Electronics", "SSDs", "SanDisk", 14999, 18),
    ("Samsung 870 EVO 500GB", "Samsung 870 EVO SATA SSD 500GB", "Electronics", "SSDs", "Samsung", 4499, 35),
    ("WD Blue SN580 500GB", "WD Blue SN580 NVMe SSD 500GB", "Electronics", "SSDs", "Western Digital", 3999, 40),
    ("Crucial BX500 480GB", "Crucial BX500 SATA SSD 480GB", "Electronics", "SSDs", "Crucial", 2999, 50),
    ("ADATA Legend 800 1TB", "ADATA Legend 800 NVMe SSD 1TB", "Electronics", "SSDs", "ADATA", 5999, 35),
    ("Sabrent Rocket 4 Plus 2TB", "Sabrent Rocket 4 Plus NVMe 2TB", "Electronics", "SSDs", "Sabrent", 19999, 10),

    # Routers
    ("TP-Link Archer C6", "TP-Link Archer C6 AC1200 WiFi Router", "Electronics", "Routers", "TP-Link", 2999, 50),
    ("ASUS RT-AX86U Pro", "ASUS RT-AX86U Pro WiFi 6 Router", "Electronics", "Routers", "ASUS", 18999, 12),
    ("Netgear Nighthawk RAX50", "Netgear Nighthawk AX5400 WiFi 6 Router", "Electronics", "Routers", "Netgear", 12999, 15),
    ("TP-Link Deco M5", "TP-Link Deco M5 Mesh WiFi System", "Electronics", "Routers", "TP-Link", 9999, 20),
    ("Xiaomi Router 4A", "Xiaomi Router 4A Gigabit Edition", "Electronics", "Routers", "Xiaomi", 1399, 60),
    ("D-Link DIR-X1560", "D-Link DIR-X1560 WiFi 6 Router", "Electronics", "Routers", "D-Link", 3999, 35),
    ("TP-Link Archer T4U", "TP-Link Archer T4U AC1300 USB Adapter", "Electronics", "Routers", "TP-Link", 1599, 40),
    ("Mercusys MR70X", "Mercusys MR70X WiFi 6 Router", "Electronics", "Routers", "Mercusys", 2499, 45),
    ("ASUS ZenWiFi AX", "ASUS ZenWiFi AX Mesh System 3-Pack", "Electronics", "Routers", "ASUS", 32999, 8),
    ("TP-Link Deco XE75", "TP-Link Deco XE75 WiFi 6E Mesh", "Electronics", "Routers", "TP-Link", 24999, 10),

    # Smart Watches
    ("Apple Watch Series 9", "Apple Watch Series 9 45mm GPS", "Electronics", "Smart Watches", "Apple", 49900, 20),
    ("Samsung Galaxy Watch 6", "Samsung Galaxy Watch 6 Classic 47mm", "Electronics", "Smart Watches", "Samsung", 32999, 22),
    ("Amazfit GTR 4", "Amazfit GTR 4 GPS Smartwatch", "Electronics", "Smart Watches", "Amazfit", 16999, 30),
    ("Fitbit Charge 6", "Fitbit Charge 6 Fitness Tracker", "Electronics", "Smart Watches", "Fitbit", 14999, 25),
    ("OnePlus Watch 2", "OnePlus Watch 2 Wear OS", "Electronics", "Smart Watches", "OnePlus", 24999, 18),
    ("Noise ColorFit Pro 5", "Noise ColorFit Pro 5 AMOLED Smartwatch", "Electronics", "Smart Watches", "Noise", 4999, 50),
    ("boAt Lunar Oasis", "boAt Lunar Oasis AMOLED Smartwatch", "Electronics", "Smart Watches", "boAt", 3999, 55),
    ("Fire-Boltt Invincible Plus", "Fire-Boltt Invincible Plus AMOLED", "Electronics", "Smart Watches", "Fire-Boltt", 2999, 60),
    ("Fossil Gen 6 Hybrid", "Fossil Gen 6 Hybrid Smartwatch", "Electronics", "Smart Watches", "Fossil", 18999, 12),
    ("Garmin Venu 3", "Garmin Venu 3 GPS Smartwatch", "Electronics", "Smart Watches", "Garmin", 49999, 8),

    # Power Banks
    ("Baseus 20000mAh PB", "Baseus 20000mAh Fast Charging Power Bank", "Electronics", "Power Banks", "Baseus", 2499, 45),
    ("Mi Power Bank 3i", "Mi 20000mAh Power Bank 3i 18W", "Electronics", "Power Banks", "Xiaomi", 1799, 55),
    ("Ambrane 10000mAh", "Ambrane 10000mAh Slim Power Bank", "Electronics", "Power Banks", "Ambrane", 999, 70),
    ("Realme 10000mAh Dart", "Realme 10000mAh 33W Dart Charge PB", "Electronics", "Power Banks", "Realme", 1999, 40),
    ("Syska 20000mAh", "Syska 20000mAh Power Bank Pro", "Electronics", "Power Banks", "Syska", 1499, 50),
    ("Redmi 20000mAh PB", "Redmi 20000mAh 18W Fast Charge", "Electronics", "Power Banks", "Xiaomi", 1599, 60),
    ("pTron Dynamo Pro", "pTron Dynamo Pro 10000mAh PB", "Electronics", "Power Banks", "pTron", 799, 80),
    ("Portronics Power Volt", "Portronics 10000mAh Power Bank", "Electronics", "Power Banks", "Portronics", 1199, 55),
    ("Anker PowerCore 26800", "Anker PowerCore 26800mAh Power Bank", "Electronics", "Power Banks", "Anker", 5999, 15),
    ("OnePlus 10000mAh", "OnePlus 10000mAh Warp Charge PB", "Electronics", "Power Banks", "OnePlus", 2299, 35),

    # Cameras
    ("Canon EOS R50", "Canon EOS R50 Mirrorless Camera 24MP", "Electronics", "Cameras", "Canon", 74999, 10),
    ("Sony Alpha 6400", "Sony Alpha 6400 Mirrorless APS-C", "Electronics", "Cameras", "Sony", 79999, 8),
    ("Nikon Z50", "Nikon Z50 Mirrorless Camera Kit", "Electronics", "Cameras", "Nikon", 84999, 7),
    ("Fujifilm X-T30 II", "Fujifilm X-T30 II Mirrorless 26MP", "Electronics", "Cameras", "Fujifilm", 89999, 6),
    ("GoPro Hero 12 Black", "GoPro Hero 12 Black Action Camera", "Electronics", "Cameras", "GoPro", 41500, 15),
    ("DJI Osmo Action 4", "DJI Osmo Action 4 Waterproof Camera", "Electronics", "Cameras", "DJI", 37999, 12),
    ("Canon EOS 250D", "Canon EOS 250D DSLR 24MP", "Electronics", "Cameras", "Canon", 54999, 14),
    ("Sony ZV-1 II", "Sony ZV-1 II Vlogging Camera", "Electronics", "Cameras", "Sony", 84999, 8),
    ("Insta360 X3", "Insta360 X3 360 Action Camera", "Electronics", "Cameras", "Insta360", 44999, 10),
    ("Nikon Z30", "Nikon Z30 Vlogging Camera Kit", "Electronics", "Cameras", "Nikon", 64999, 11),

    # TVs
    ("Samsung 55 Crystal 4K", "Samsung 55-inch Crystal 4K UHD TV", "Electronics", "TVs", "Samsung", 44999, 15),
    ("LG 50 NanoCell 4K", "LG 50-inch NanoCell 4K Smart TV", "Electronics", "TVs", "LG", 42999, 12),
    ("Sony BRAVIA 55 4K", "Sony BRAVIA 55-inch 4K Google TV", "Electronics", "TVs", "Sony", 59999, 10),
    ("Xiaomi TV 55 4K", "Xiaomi TV 55-inch 4K LED Smart TV", "Electronics", "TVs", "Xiaomi", 34999, 20),
    ("TCL 43 4K Google TV", "TCL 43-inch 4K Google TV", "Electronics", "TVs", "TCL", 26999, 25),
    ("OnePlus TV 43 Y1S Pro", "OnePlus TV 43-inch 4K Y1S Pro", "Electronics", "TVs", "OnePlus", 29999, 22),
    ("Hisense 50A6K", "Hisense 50-inch 4K UHD Smart TV", "Electronics", "TVs", "Hisense", 32999, 18),
    ("Samsung 32 HD Smart TV", "Samsung 32-inch HD Smart TV", "Electronics", "TVs", "Samsung", 17999, 30),
    ("LG 43 Full HD LED", "LG 43-inch Full HD LED Smart TV", "Electronics", "TVs", "LG", 24999, 22),
    ("VU 43 Premium 4K", "VU 43-inch Premium 4K Android TV", "Electronics", "TVs", "VU", 22999, 25),

    # Printers
    ("HP LaserJet Pro M404dn", "HP LaserJet Pro M404dn Mono Printer", "Electronics", "Printers", "HP", 29999, 12),
    ("Canon PIXMA G3010", "Canon PIXMA G3010 Ink Tank Printer", "Electronics", "Printers", "Canon", 14999, 20),
    ("Epson EcoTank L3210", "Epson EcoTank L3210 Ink Tank Printer", "Electronics", "Printers", "Epson", 13999, 22),
    ("Brother DCP-T426W", "Brother DCP-T426W Ink Tank Printer", "Electronics", "Printers", "Brother", 12999, 18),
    ("HP DeskJet 2331", "HP DeskJet 2331 All-in-One Printer", "Electronics", "Printers", "HP", 5999, 35),

    # Projectors
    ("Epson EB-W52", "Epson EB-W52 WXGA Projector", "Electronics", "Projectors", "Epson", 44999, 8),
    ("BenQ MS535A", "BenQ MS535A SVGA Projector", "Electronics", "Projectors", "BenQ", 32999, 10),
    ("Xiaomi Mi Smart Projector 2", "Xiaomi Mi Smart Projector 2 1080p", "Electronics", "Projectors", "Xiaomi", 39999, 12),
    ("Unic UC46+", "Unic UC46+ LED Mini Projector", "Electronics", "Projectors", "Unic", 12999, 20),
    ("Portronics Pico+", "Portronics Pico+ Portable Mini Projector", "Electronics", "Projectors", "Portronics", 8999, 25),

    # USB Drives & Accessories
    ("Samsung T7 500GB", "Samsung T7 Portable SSD 500GB", "Electronics", "Storage", "Samsung", 5999, 40),
    ("SanDisk Ultra 256GB", "SanDisk Ultra 256GB USB 3.0 Flash Drive", "Electronics", "Storage", "SanDisk", 1799, 60),
    ("Kingston 128GB USB", "Kingston DataTraveler 128GB USB 3.0", "Electronics", "Storage", "Kingston", 1099, 70),
    ("HP USB-C Hub", "HP USB-C 7-in-1 Hub Adapter", "Electronics", "Accessories", "HP", 3999, 35),
    ("Anker USB-C Cable", "Anker USB-C to USB-C 100W Cable 2m", "Electronics", "Accessories", "Anker", 999, 80),
    ("Belkin Screen Protector", "Belkin Tempered Glass Screen Protector", "Electronics", "Accessories", "Belkin", 699, 90),
    ("Spigen Case iPhone 15", "Spigen Tough Armor Case iPhone 15 Pro", "Electronics", "Accessories", "Spigen", 1999, 45),
    ("Ugreen HDMI Cable 2m", "Ugreen 8K HDMI 2.1 Cable 2 Meter", "Electronics", "Accessories", "Ugreen", 899, 55),
    ("Boat AUX Cable", "boAt 3.5mm AUX Cable 1.5m", "Electronics", "Accessories", "boAt", 299, 100),
    ("Portronics Car Mount", "Portronics Car Mobile Holder Mount", "Electronics", "Accessories", "Portronics", 599, 65),
]



CLOTHING_PRODUCTS = [
    ("Men's Cotton Round Neck T-Shirt", "Premium cotton round neck t-shirt", "Fashion", "T-shirts", "Allen Solly", 799, 60),
    ("Men's Polo Collar T-Shirt", "Classic polo t-shirt for men", "Fashion", "T-shirts", "US Polo", 999, 50),
    ("Men's Slim Fit Formal Shirt", "Slim fit cotton formal shirt", "Fashion", "Shirts", "Arrow", 1499, 40),
    ("Men's Regular Fit Jeans", "Classic regular fit blue jeans", "Fashion", "Jeans", "Levis", 2499, 50),
    ("Men's Slim Fit Trousers", "Slim fit chino trousers", "Fashion", "Trousers", "Van Heusen", 1799, 40),
    ("Women's Kurti Tunic", "Printed cotton kurti for women", "Fashion", "Kurtas", "W", 899, 45),
    ("Men's Fleece Hoodie", "Zipper fleece hoodie for men", "Fashion", "Hoodies", "Puma", 1999, 25),
    ("Women's A-Line Dress", "Printed A-line casual dress", "Fashion", "Dresses", "Max", 1299, 30),
    ("Women's Silk Saree", "Traditional Banarasi silk saree", "Fashion", "Sarees", "Mira", 3999, 15),
    ("Men's Puffer Jacket", "Lightweight puffer winter jacket", "Fashion", "Jackets", "Decathlon", 2999, 20),
    ("Men's Denim Shorts", "Regular fit denim shorts", "Fashion", "Shorts", "Jack & Jones", 1299, 35),
    ("Women's Hooded Sweatshirt", "Comfortable hooded sweatshirt", "Fashion", "Hoodies", "H&M", 1499, 30),
    ("Men's Graphic Print T-Shirt", "Bold graphic print cotton tee", "Fashion", "T-shirts", "Levis", 1199, 45),
    ("Women's Maxi Dress", "Floral printed maxi dress", "Fashion", "Dresses", "AND", 2499, 20),
    ("Men's Chino Shorts", "Slim fit chino shorts", "Fashion", "Shorts", "Tommy Hilfiger", 1999, 30),
    ("Women's Denim Jacket", "Classic blue denim jacket", "Fashion", "Jackets", "Levis", 3499, 15),
    ("Men's Henley T-Shirt", "Long sleeve henley neck t-shirt", "Fashion", "T-shirts", "Jack & Jones", 899, 40),
    ("Men's Cargo Pants", "Relaxed fit cargo pants", "Fashion", "Trousers", "Decathlon", 1499, 30),
    ("Men's Track Pants", "Athletic track pants with stripes", "Fashion", "Trousers", "Adidas", 2299, 35),
    ("Women's Anarkali Kurti", "Elegant Anarkali suit kurti", "Fashion", "Kurtas", "Biba", 1999, 20),
    ("Men's Formal Blazer", "Slim fit single button blazer", "Fashion", "Jackets", "Van Heusen", 3999, 12),
    ("Women's Cotton Leggings", "Comfortable cotton leggings 2 pack", "Fashion", "Leggings", "Jockey", 599, 60),
    ("Kids Graphic T-Shirt", "Fun graphic print t-shirt for kids", "Fashion", "T-shirts", "H&M", 499, 40),
    ("Kids Denim Jeans", "Stretchable denim jeans for kids", "Fashion", "Jeans", "Levis", 1299, 30),
    ("Men's Polo T-Shirt 3 Pack", "3 pack cotton polo t-shirts", "Fashion", "T-shirts", "Jockey", 1499, 40),
    ("Women's Sports Bra", "High impact sports bra", "Fashion", "Sportswear", "Nike", 1999, 25),
    ("Men's Running Shorts", "Breathable running shorts", "Fashion", "Sportswear", "Nike", 1499, 30),
    ("Women's Yoga Pants", "High waist yoga pants", "Fashion", "Sportswear", "Decathlon", 999, 35),
    ("Men's Jogger Pants", "Comfortable cotton jogger pants", "Fashion", "Trousers", "Puma", 1799, 40),
    ("Women's Georgette Saree", "Printed georgette saree with blouse", "Fashion", "Sarees", "Biba", 1499, 25),
]

FOOTWEAR_PRODUCTS = [
    ("Nike Revolution 6", "Nike Revolution 6 Running Shoes", "Fashion", "Running Shoes", "Nike", 3995, 30),
    ("Adidas Duramo Speed", "Adidas Duramo Speed Running Shoes", "Fashion", "Running Shoes", "Adidas", 5999, 25),
    ("Puma Deviate Nitro 2", "Puma Deviate Nitro 2 Running Shoes", "Fashion", "Running Shoes", "Puma", 8999, 15),
    ("ASICS Gel-Nimbus 25", "ASICS Gel-Nimbus 25 Running Shoes", "Fashion", "Running Shoes", "ASICS", 12999, 10),
    ("New Balance 574", "New Balance 574 Classic Sneakers", "Fashion", "Casual Shoes", "New Balance", 8999, 20),
    ("Nike Air Max 90", "Nike Air Max 90 Classic Sneakers", "Fashion", "Casual Shoes", "Nike", 11999, 18),
    ("Adidas Stan Smith", "Adidas Stan Smith Classic White", "Fashion", "Casual Shoes", "Adidas", 7999, 22),
    ("Puma Smash V2", "Puma Smash V2 Classic Sneakers", "Fashion", "Casual Shoes", "Puma", 4999, 30),
    ("Woodland Men's Boots", "Woodland Leather Casual Boots", "Fashion", "Boots", "Woodland", 3999, 25),
    ("Bata Men's Formal Shoes", "Bata Leather Formal Derby Shoes", "Fashion", "Formal Shoes", "Bata", 2999, 35),
    ("Clarks Formal Oxford", "Clarks Men's Formal Oxford Shoes", "Fashion", "Formal Shoes", "Clarks", 7999, 12),
    ("Red Tape Formal Loafer", "Red Tape Men's Formal Loafer", "Fashion", "Formal Shoes", "Red Tape", 2499, 30),
    ("Crocs Classic Clog", "Crocs Classic Unisex Clog", "Fashion", "Sandals", "Crocs", 2999, 25),
    ("Campus Running Shoes", "Campus Men's Running Shoes Oxyfit", "Fashion", "Running Shoes", "Campus", 1299, 45),
    ("Sparx Sports Shoes", "Sparx Men's Sports Running Shoes", "Fashion", "Sports Shoes", "Sparx", 999, 60),
    ("Reebok Classic Leather", "Reebok Classic Leather Sneakers", "Fashion", "Casual Shoes", "Reebok", 6999, 22),
    ("Under Armour Charged Assert", "UA Charged Assert 9 Running Shoes", "Fashion", "Running Shoes", "Under Armour", 6999, 18),
    ("Birkenstock Arizona", "Birkenstock Arizona Soft Footbed", "Fashion", "Sandals", "Birkenstock", 4999, 12),
    ("Hush Puppies Oxford", "Hush Puppies Men's Formal Oxford", "Fashion", "Formal Shoes", "Hush Puppies", 6999, 15),
    ("Nike Sunray Protect", "Nike Sunray Protect 2 Sandals", "Fashion", "Sandals", "Nike", 2999, 20),
]

ACCESSORIES_PRODUCTS = [
    ("WildHorn Leather Wallet", "Genuine leather bifold wallet", "Fashion", "Wallets", "WildHorn", 899, 45),
    ("Allen Solly Slim Wallet", "RFID blocking slim wallet", "Fashion", "Wallets", "Allen Solly", 1299, 35),
    ("Tommy Hilfiger Wallet", "Tommy Hilfiger Men's Classic Wallet", "Fashion", "Wallets", "Tommy Hilfiger", 2499, 20),
    ("Formal Leather Belt", "Genuine leather formal belt", "Fashion", "Belts", "WildHorn", 699, 50),
    ("Nike Sport Sunglasses", "Nike Sports UV400 Sunglasses", "Fashion", "Sunglasses", "Nike", 2499, 25),
    ("Ray-Ban Aviator", "Ray-Ban Classic Aviator Sunglasses", "Fashion", "Sunglasses", "Ray-Ban", 8999, 10),
    ("Fastrack Analog Watch", "Fastrack Men's Analog Watch", "Fashion", "Watches", "Fastrack", 2499, 35),
    ("Casio G-Shock", "Casio G-Shock Digital Watch", "Fashion", "Watches", "Casio", 9999, 15),
    ("Titan Raga Watch", "Titan Raga Women's Analog Watch", "Fashion", "Watches", "Titan", 4999, 20),
    ("Puma Backpack", "Puma Unisex Solid Backpack 25L", "Fashion", "Bags", "Puma", 2499, 30),
    ("American Tourister Trolley", "American Tourister 55cm Trolley Bag", "Fashion", "Bags", "American Tourister", 5999, 15),
    ("Wildcraft Laptop Bag", "Wildcraft 15.6 inch Laptop Backpack", "Fashion", "Bags", "Wildcraft", 1999, 40),
    ("Fastrack Backpack", "Fastrack Casual Backpack 30L", "Fashion", "Bags", "Fastrack", 1499, 35),
    ("Sonata Digital Watch", "Sonata Men's Digital Sports Watch", "Fashion", "Watches", "Sonata", 799, 60),
    ("WildHorn Belt Pack", "WildHorn Men's Leather Belt", "Fashion", "Belts", "WildHorn", 899, 40),
]


# ──────────────────────────────────────────────────────────
# Generator functions to scale up to 10,000+ products
# ──────────────────────────────────────────────────────────

def generate_variant_products(base_products, target_multiplier=5):
    """Generate variants of base products to reach target count."""
    variants = list(base_products)
    brands_extra = ["TechBrand", "ProLine", "ValueMax", "EliteSeries", "SmartChoice", "PrimeGoods", "QualityFirst", "BestBuy"]

    for name, desc, cat, sub, brand, price, stock in base_products:
        for i in range(target_multiplier - 1):
            new_brand = brands_extra[i % len(brands_extra)]
            new_price = round(price * random.uniform(0.7, 1.5), 0)
            new_stock = random.randint(10, 100)
            variant_name = f"{new_brand} {sub} {name.split()[-1]} {i+2}"
            variant_desc = f"{new_brand} alternative to {name}"
            variants.append((variant_name, variant_desc, cat, sub, new_brand, int(new_price), new_stock))
    return variants


def generate_scaled_products():
    """Generate 10,000+ products by combining base + variants + generated."""
    all_products = []

    # Electronics: ~150 base → scale to ~3000
    all_products.extend(generate_variant_products(ELECTRONICS_PRODUCTS, 20))

    # Clothing: ~30 base → scale to ~2000
    all_products.extend(generate_variant_products(CLOTHING_PRODUCTS, 65))

    # Footwear: ~20 base → scale to ~1500
    all_products.extend(generate_variant_products(FOOTWEAR_PRODUCTS, 75))

    # Accessories: ~15 base → scale to ~1000
    all_products.extend(generate_variant_products(ACCESSORIES_PRODUCTS, 65))

    # Add generated commodity products
    categories_data = [
        ("Electronics", "USB Drives", ["SanDisk", "Kingston", "Samsung", "HP", "Transcend"], (299, 5999), 50, 200),
        ("Electronics", "Cables", ["Belkin", "Ugreen", "Anker", "Amazon Basics", "Portronics"], (199, 2999), 40, 150),
        ("Electronics", "Chargers", ["Boat", "Realme", "OnePlus", "Samsung", "Mi"], (399, 4999), 35, 180),
        ("Electronics", "Cases", ["Spigen", "OtterBox", "Boat", "PufferShield", "KAPAVER"], (299, 2999), 30, 200),
        ("Electronics", "Screen Guards", ["Belkin", "Gadget Shieldz", "TemperedPro", "ClearView", "ShieldMAX"], (99, 999), 25, 300),
        ("Electronics", "Adapters", ["Apple", "Samsung", "OnePlus", "Realme", "Belkin"], (299, 3999), 30, 150),
        ("Electronics", "Hubs", ["HP", "Anker", "UGREEN", "Portronics", "Logitech"], (999, 9999), 20, 100),
        ("Electronics", "Cooling Pads", ["Cooler Master", "Thermaltake", "Havit", "Targus", "Zebronics"], (499, 3999), 15, 120),
        ("Electronics", "Laptop Stands", ["Strive", "Cosmic Byte", "Portronics", "Amazon Basics", "HeavyDuty"], (499, 4999), 20, 80),
        ("Electronics", "Tablet Covers", ["Apple", "Samsung", "Spigen", "KapaVer", "Generic"], (299, 3999), 25, 100),
        ("Electronics", "Car Chargers", ["Boat", "Anker", "Ambrane", "Syska", "Portronics"], (399, 2999), 30, 150),
        ("Electronics", "LED Lights", ["Philips", "Syska", "Wipro", "Havells", "Orient"], (199, 2999), 25, 200),
        ("Electronics", "Extension Boards", ["Havells", "Anchor", "Bajaj", "GM", "Orient"], (299, 2999), 20, 120),
        ("Electronics", "Stabilizers", ["V-Guard", "Microtek", "Havells", "Bajaj", "Syska"], (999, 9999), 15, 80),
        ("Electronics", "Inverters", ["Luminous", "Exide", "Amaron", "Havells", "V-Guard"], (3999, 29999), 10, 50),
        ("Fashion", "Backpacks", ["Wildcraft", "American Tourister", "Skybags", "Safari", "Tommy"], (999, 9999), 20, 150),
        ("Fashion", "Handbags", ["Lavie", "Hidesign", "Baggit", "Caprese", "Fossil"], (999, 14999), 15, 80),
        ("Fashion", "Belts", ["WildHorn", "Allen Solly", "Tommy Hilfiger", "Pepe Jeans", "Lee"], (399, 2999), 25, 120),
        ("Fashion", "Caps", ["Nike", "Adidas", "Puma", "New Era", "FILA"], (299, 2999), 30, 200),
        ("Fashion", "Scarves", ["Allen Solly", "Peter England", "Van Heusen", "W", "Max"], (299, 1999), 20, 100),
        ("Fashion", "Ties", ["Van Heusen", "Raymond", "Park Avenue", "Allen Solly", "Louis Philippe"], (299, 2999), 15, 80),
        ("Fashion", "Socks", ["Puma", "Nike", "Adidas", "Jockey", "JUNIJIN"], (99, 999), 30, 300),
        ("Fashion", "Gloves", ["Puma", "Under Armour", "Holloway", "Mechanix", "Decathlon"], (199, 2999), 20, 80),
        ("Fashion", "Beanies", ["North Face", "Puma", "H&M", "Decathlon", "Tommy"], (299, 1999), 15, 100),
        ("Fashion", "Bow Ties", ["Van Heusen", "Allen Solly", "Raymond", "Park Avenue", "Generic"], (199, 1999), 10, 60),
    ]

    for cat, sub, brands, price_range, min_stock, max_stock in categories_data:
        for brand in brands:
            for i in range(50):
                name = f"{brand} {sub} Premium {i+1}"
                desc = f"High quality {sub.lower()} from {brand}"
                price = round(random.uniform(price_range[0], price_range[1]), 0)
                stock = random.randint(min_stock, max_stock)
                all_products.append((name, desc, cat, sub, brand, int(price), stock))

    return all_products


ALL_PRODUCTS = generate_scaled_products()

# ──────────────────────────────────────────────────────────
# Seed function
# ──────────────────────────────────────────────────────────

async def seed():
    from models.database import async_session
    from models.models import Merchant, Product, ProductRelationship, Policy, AuditLog, Notification
    from sqlalchemy import select, text

    async with async_session() as db:
        # Check if already seeded
        result = await db.execute(text("SELECT COUNT(*) FROM products"))
        count = result.scalar()
        if count and count >= 100:
            logger.info(f"Database already has {count} products, skipping seed")
            return

        logger.info(f"Seeding {len(ALL_PRODUCTS)} products...")

        # Create merchant
        merchant = Merchant(
            name="TechZone Electronics",
            email="admin@techzone.com",
        )
        db.add(merchant)
        await db.commit()
        await db.refresh(merchant)

        product_ids = []
        categories_seen = set()

        batch_size = 500
        for i in range(0, len(ALL_PRODUCTS), batch_size):
            batch = ALL_PRODUCTS[i:i+batch_size]
            for name, desc, category, subcategory, brand, price, stock in batch:
                pid = _id()
                h = _hash_seed(name)
                sales = h % 200
                cost_ratio = 0.45 + (h % 30) / 100  # 45-75% of retail
                cost_price = round(price * cost_ratio, 2)
                revenue = round(sales * price, 2)
                margin = round(((price - cost_price) / price) * 100, 2) if price > 0 else 0
                rating = round(3.0 + (h % 20) / 10.0, 1)

                product = Product(
                    id=pid,
                    merchant_id=merchant.id,
                    name=name,
                    description=desc,
                    category=category,
                    subcategory=subcategory,
                    brand=brand,
                    price=price,
                    previous_price=round(price * random.uniform(0.9, 1.1), 2),
                    cost_price=cost_price,
                    currency="INR",
                    stock=stock,
                    sales=sales,
                    revenue=revenue,
                    margin=margin,
                    sku=f"SKU-{pid[:8].upper()}",
                    rating=min(rating, 5.0),
                    tags=f"{category.lower()},{subcategory.lower()},{brand.lower()}",
                    image_url=f"https://placehold.co/400x300/1e1b4b/ffffff?text={name[:20].replace(' ', '+')}",
                )
                db.add(product)
                product_ids.append(pid)
                categories_seen.add(category)

            await db.commit()
            logger.info(f"  Seeded batch {i//batch_size + 1} ({min(i+batch_size, len(ALL_PRODUCTS))}/{len(ALL_PRODUCTS)})")

        # Create product relationships
        rels = []
        for i in range(0, min(100, len(product_ids)), 3):
            if i + 1 < len(product_ids):
                rels.append((product_ids[i], product_ids[i+1], "cross-sell", "Frequently bought together"))
            if i + 2 < len(product_ids):
                rels.append((product_ids[i], product_ids[i+2], "upsell", "Consider this premium alternative"))

        for pid, rpid, rtype, reason in rels:
            rel = ProductRelationship(
                product_id=pid, related_product_id=rpid,
                relationship_type=rtype, reason=reason,
            )
            db.add(rel)

        # Default policy
        policy = Policy(max_transaction_amount=500000, payment_requires_approval=False)
        db.add(policy)

        # Sample notifications
        sample_notifs = [
            ("Welcome to AI Growth and Commerce Agent", "Your commerce platform is ready.", "info"),
            ("Low Stock Alert", "Some products are running low on stock. Check inventory.", "warning"),
            ("System Ready", "All systems operational. Commerce assistant ready.", "success"),
        ]
        for title, msg, ntype in sample_notifs:
            db.add(Notification(title=title, message=msg, type=ntype))

        await db.commit()
        logger.info(f"Seed completed: {len(ALL_PRODUCTS)} products across {len(categories_seen)} categories, {len(rels)} relationships")


if __name__ == "__main__":
    asyncio.run(seed())

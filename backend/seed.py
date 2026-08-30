"""
Seed script: 500+ real products across 10 categories for MerchantFlow AI.
Run once to populate the database.
"""
import uuid
import asyncio
import logging

logger = logging.getLogger(__name__)


def _id():
    return str(uuid.uuid4())


# ──────────────────────────────────────────────────────────
# 100 ELECTRONICS products
# ──────────────────────────────────────────────────────────
ELECTRONICS = [
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

    ("iPad Pro 12.9 M2", "Apple iPad Pro 12.9-inch M2 256GB", "Electronics", "Tablets", "Apple", 112900, 15),
    ("Samsung Galaxy Tab S9", "Samsung Galaxy Tab S9 11-inch 128GB", "Electronics", "Tablets", "Samsung", 74999, 20),
    ("Lenovo Tab P12 Pro", "Lenovo Tab P12 Pro AMOLED 256GB", "Electronics", "Tablets", "Lenovo", 69999, 12),
    ("OnePlus Pad", "OnePlus Pad 256GB WiFi", "Electronics", "Tablets", "OnePlus", 37999, 25),
    ("Realme Pad 2", "Realme Pad 2 11-inch 128GB", "Electronics", "Tablets", "Realme", 17999, 35),
    ("iPad Air M1", "Apple iPad Air M1 64GB WiFi", "Electronics", "Tablets", "Apple", 59900, 18),
    ("Xiaomi Pad 6", "Xiaomi Pad 6 144Hz 128GB", "Electronics", "Tablets", "Xiaomi", 26999, 30),
    ("Lenovo Tab M10 Plus", "Lenovo Tab M10 Plus Gen 3 64GB", "Electronics", "Tablets", "Lenovo", 15999, 40),
    ("Samsung Galaxy Tab A9", "Samsung Galaxy Tab A9 8.7-inch 64GB", "Electronics", "Tablets", "Samsung", 14999, 45),
    ("Honor Pad X9", "Honor Pad X9 11.5-inch 128GB", "Electronics", "Tablets", "Honor", 22999, 28),

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

    ("Dell 240GB USB Drive", "Dell 240GB USB 3.0 Flash Drive", "Electronics", "USB Drives", "Dell", 1999, 50),
    ("SanDisk Ultra 128GB", "SanDisk Ultra 128GB USB 3.0 Flash Drive", "Electronics", "USB Drives", "SanDisk", 999, 70),
    ("Kingston DataTraveler 64GB", "Kingston DataTraveler 64GB USB 3.0", "Electronics", "USB Drives", "Kingston", 599, 80),
    ("Samsung BAR Plus 256GB", "Samsung BAR Plus 256GB USB 3.1", "Electronics", "USB Drives", "Samsung", 2999, 40),
    ("HP v236w 64GB", "HP v236w Metal USB Drive 64GB", "Electronics", "USB Drives", "HP", 549, 75),
    ("Transcend JetFlash 890 128GB", "Transcend JetFlash 890 128GB USB-C", "Electronics", "USB Drives", "Transcend", 1499, 45),
    ("Strontium AMMO 256GB", "Strontium AMMO 256GB USB 3.1 Flash", "Electronics", "USB Drives", "Strontium", 2499, 35),
    ("ADATA UV370 128GB", "ADATA UV370 128GB USB 3.1 Flash Drive", "Electronics", "USB Drives", "ADATA", 899, 60),
    ("Toshiba Hayabusa 64GB", "Toshiba Hayabusa 64GB USB 3.0", "Electronics", "USB Drives", "Toshiba", 699, 65),
    ("PNY Turbo Attache 4 128GB", "PNY Turbo Attache 4 128GB USB 3.0", "Electronics", "USB Drives", "PNY", 1099, 50),

    ("HP LaserJet Pro M404dn", "HP LaserJet Pro M404dn Mono Printer", "Electronics", "Printers", "HP", 29999, 12),
    ("Canon PIXMA G3010", "Canon PIXMA G3010 Ink Tank Printer", "Electronics", "Printers", "Canon", 14999, 20),
    ("Epson EcoTank L3210", "Epson EcoTank L3210 Ink Tank Printer", "Electronics", "Printers", "Epson", 13999, 22),
    ("Brother DCP-T426W", "Brother DCP-T426W Ink Tank Printer", "Electronics", "Printers", "Brother", 12999, 18),
    ("HP DeskJet 2331", "HP DeskJet 2331 All-in-One Printer", "Electronics", "Printers", "HP", 5999, 35),
    ("Canon imageCLASS MF246dn", "Canon MF246dn Laser MFP", "Electronics", "Printers", "Canon", 24999, 10),
    ("Epson L1210", "Epson L1210 Single Function Ink Tank", "Electronics", "Printers", "Epson", 10999, 25),
    ("Samsung Xpress M2026", "Samsung Xpress M2026 Mono Laser", "Electronics", "Printers", "Samsung", 15999, 15),
    ("HP Smart Tank 500", "HP Smart Tank 500 All-in-One", "Electronics", "Printers", "HP", 16999, 20),
    ("Canon PIXMA E4570", "Canon PIXMA E4570 Ink Tank AIO", "Electronics", "Printers", "Canon", 12499, 22),

    ("Epson EB-W52", "Epson EB-W52 WXGA Projector", "Electronics", "Projectors", "Epson", 44999, 8),
    ("BenQ MS535A", "BenQ MS535A SVGA Projector", "Electronics", "Projectors", "BenQ", 32999, 10),
    ("Xiaomi Mi Smart Projector 2", "Xiaomi Mi Smart Projector 2 1080p", "Electronics", "Projectors", "Xiaomi", 39999, 12),
    ("Epson EF-11", "Epson EF-11 Laser Projector", "Electronics", "Projectors", "Epson", 79999, 5),
    ("ViewSonic PA500S", "ViewSonic PA500S SVGA Projector", "Electronics", "Projectors", "ViewSonic", 29999, 10),
    ("BenQ TH585P", "BenQ TH585P 1080p Home Projector", "Electronics", "Projectors", "BenQ", 64999, 6),
    ("Unic UC46+", "Unic UC46+ LED Mini Projector", "Electronics", "Projectors", "Unic", 12999, 20),
    ("Portronics Pico+", "Portronics Pico+ Portable Mini Projector", "Electronics", "Projectors", "Portronics", 8999, 25),
    ("Xiaomi Mi Laser Projector", "Xiaomi Mi Laser Projector 150 inch", "Electronics", "Projectors", "Xiaomi", 59999, 7),
    ("Samsung The Freestyle", "Samsung The Freestyle Portable Projector", "Electronics", "Projectors", "Samsung", 59999, 8),

    ("Samsung 55\" Crystal 4K", "Samsung 55-inch Crystal 4K UHD TV", "Electronics", "TVs", "Samsung", 44999, 15),
    ("LG 50\" NanoCell 4K", "LG 50-inch NanoCell 4K Smart TV", "Electronics", "TVs", "LG", 42999, 12),
    ("Sony BRAVIA 55\" 4K", "Sony BRAVIA 55-inch 4K Google TV", "Electronics", "TVs", "Sony", 59999, 10),
    ("Xiaomi TV 55\" 4K", "Xiaomi TV 55-inch 4K LED Smart TV", "Electronics", "TVs", "Xiaomi", 34999, 20),
    ("TCL 43\" 4K Google TV", "TCL 43-inch 4K Google TV", "Electronics", "TVs", "TCL", 26999, 25),
    ("OnePlus TV 43\" Y1S Pro", "OnePlus TV 43-inch 4K Y1S Pro", "Electronics", "TVs", "OnePlus", 29999, 22),
    ("Hisense 50A6K", "Hisense 50-inch 4K UHD Smart TV", "Electronics", "TVs", "Hisense", 32999, 18),
    ("Samsung 32\" HD Smart TV", "Samsung 32-inch HD Smart TV", "Electronics", "TVs", "Samsung", 17999, 30),
    ("LG 43\" Full HD LED", "LG 43-inch Full HD LED Smart TV", "Electronics", "TVs", "LG", 24999, 22),
    ("VU 43\" Premium 4K", "VU 43-inch Premium 4K Android TV", "Electronics", "TVs", "VU", 22999, 25),
]

# ──────────────────────────────────────────────────────────
# 60 GROCERY products
# ──────────────────────────────────────────────────────────
GROCERY = [
    ("India Gate Basmati Rice 5kg", "Premium long grain basmati rice", "Grocery", "Rice", "India Gate", 649, 100),
    ("Daawat Rozana Basmati 5kg", "Everyday basmati rice for daily meals", "Grocery", "Rice", "Daawat", 499, 120),
    ("Tata Sampann Basmati 1kg", "Premium basmati rice for special dishes", "Grocery", "Rice", "Tata", 149, 150),
    ("Fortune Sunlite Refined 1L", "Sunflower refined oil 1 litre", "Grocery", "Cooking Oil", "Fortune", 179, 200),
    ("Saffola Gold 1L", "Saffola Gold refined cooking oil", "Grocery", "Cooking Oil", "Saffola", 219, 150),
    ("Fortune Sunburst 1L", "Fortune Sunburst sunflower oil 1L", "Grocery", "Cooking Oil", "Fortune", 189, 180),
    ("Dalda Vanaspati 1L", "Dalda hydrogenated vegetable oil 1L", "Grocery", "Cooking Oil", "Dalda", 139, 90),
    ("Toor Dal 1kg", "Premium toor dal (arhar dal) 1kg", "Grocery", "Pulses", "Tata Sampann", 159, 200),
    ("Chana Dal 1kg", "High quality chana dal 1kg", "Grocery", "Pulses", "Tata Sampann", 129, 180),
    ("Moong Dal 1kg", "Washed moong dal 1kg pack", "Grocery", "Pulses", "Tata Sampann", 139, 170),
    ("Masoor Dal 1kg", "Red masoor dal 1kg", "Grocery", "Pulses", "Tata Sampann", 119, 160),
    ("Turmeric Powder 500g", "Pure turmeric powder for cooking", "Grocery", "Spices", "Everest", 79, 250),
    ("Red Chilli Powder 500g", "Kashmiri red chilli powder", "Grocery", "Spices", "Everest", 99, 230),
    ("Garam Masala 100g", "Everest garam masala blend", "Grocery", "Spices", "Everest", 69, 280),
    ("Coriander Powder 100g", "Fresh ground coriander powder", "Grocery", "Spices", "MDH", 49, 300),
    ("Cumin Powder 100g", "Jeera powder for Indian cooking", "Grocery", "Spices", "MDH", 59, 260),
    ("Table Salt 1kg", "Tata Salt iodized table salt 1kg", "Grocery", "Salt", "Tata", 28, 500),
    ("Sugar 1kg", "Domestic refined sugar 1kg", "Grocery", "Sugar", "Madhur", 52, 400),
    ("Tata Tea Gold 500g", "Premium CTC tea blend 500g", "Grocery", "Tea", "Tata", 199, 300),
    ("Brooke Bond Red Label 250g", "Brooke Bond Red Label tea 250g", "Grocery", "Tea", "Brooke Bond", 79, 350),
    ("Nescafe Classic 100g", "Nescafe Classic instant coffee 100g", "Grocery", "Coffee", "Nescafe", 199, 250),
    ("Bru Instant Coffee 100g", "Bru Green Label instant coffee 100g", "Grocery", "Coffee", "Bru", 169, 280),
    ("Quaker Oats 1kg", "Quaker whole grain rolled oats 1kg", "Grocery", "Oats", "Quaker", 299, 200),
    ("Saffola Masala Oats 400g", "Saffola Masala Oats 4 pack", "Grocery", "Oats", "Saffola", 128, 180),
    ("Kellogg's Corn Flakes 475g", "Kellogg's Original Corn Flakes", "Grocery", "Cereals", "Kellogg's", 229, 150),
    ("Muesli 500g", "Freedom muesli with fruits and nuts", "Grocery", "Cereals", "Freedom", 299, 120),
    ("Parle-G Biscuit 80g", "Parle-G glucose biscuits 80g", "Grocery", "Biscuits", "Parle", 10, 1000),
    ("Marie Gold 250g", "Britannia Marie Gold biscuits 250g", "Grocery", "Biscuits", "Britannia", 50, 400),
    ("Maggi Noodles 70g", "Maggi 2-Minute Masala Noodles 70g", "Grocery", "Noodles", "Maggi", 14, 800),
    ("Yippee Noodles 60g", "Yippee Happy Belly Noodles 60g", "Grocery", "Noodles", "Yippee", 12, 700),
    ("Maggi Pasta 350g", "Maggi Pazzta Cheesy Tomato 350g", "Grocery", "Pasta", "Maggi", 65, 300),
    ("Knorr Pasta 350g", "KnorrItaliano Pasta Cheese Tomato", "Grocery", "Pasta", "Knorr", 75, 250),
    ("Maggi Tomato Ketchup 500g", "Maggi Rich Tomato Ketchup 500g", "Grocery", "Sauces", "Maggi", 99, 300),
    ("Kissan Mixed Fruit Jam 500g", "Kissan Mixed Fruit Jam 500g", "Grocery", "Sauces", "Kissan", 139, 200),
    ("Haldirams Aloo Bhujia 200g", "Haldirams Aloo Bhujia snack 200g", "Grocery", "Snacks", "Haldirams", 69, 350),
    ("Lays Classic Salted 52g", "Lays Classic Salted potato chips 52g", "Grocery", "Snacks", "Lays", 20, 600),
    ("Kurkure Masala Munch 90g", "Kurkure Masala Munch snack 90g", "Grocery", "Snacks", "Kurkure", 20, 500),
    ("Cadbury Dairy Milk 150g", "Cadbury Dairy Milk chocolate 150g", "Grocery", "Chocolates", "Cadbury", 99, 300),
    ("Amul Dark Chocolate 40g", "Amul Dark Chocolate 40g bar", "Grocery", "Chocolates", "Amul", 40, 250),
    ("KitKat 4 Finger 40g", "KitKat 4 Finger wafer chocolate 40g", "Grocery", "Chocolates", "Nestle", 40, 400),
    ("Frooti Mango 200ml", "Frooti Mango drink 200ml tetra pack", "Grocery", "Beverages", "Frooti", 10, 500),
    ("Real Mango Juice 1L", "Real Fruit Power Mango Juice 1L", "Grocery", "Juices", "Real", 99, 200),
    ("Tropicana Mixed Fruit 1L", "Tropicana Mixed Fruit juice 1L", "Grocery", "Juices", "Tropicana", 119, 180),
    ("Paper Boat Aamras 200ml", "Paper Boat Aamras mango drink 200ml", "Grocery", "Beverages", "Paper Boat", 20, 400),
    ("Haldiram Navratan Mix 200g", "Haldirams Navratan Mix snack 200g", "Grocery", "Snacks", "Haldirams", 79, 250),
    ("Bikano Dal Biji 200g", "Bikano Dal Biji namkeen 200g", "Grocery", "Snacks", "Bikano", 59, 200),
    ("MDH Chana Masala 100g", "MDH Chana Masala spice blend 100g", "Grocery", "Spices", "MDH", 79, 300),
    ("Aashirvaad Atta 5kg", "Aashirvaad Select Sharbati Atta 5kg", "Grocery", "Flour", "Aashirvaad", 349, 200),
    ("Pillsbury Atta 5kg", "Pillsbury Chakki Fresh Atta 5kg", "Grocery", "Flour", "Pillsbury", 299, 220),
    ("Patanjali Atta 5kg", "Patanjali Whole Wheat Atta 5kg", "Grocery", "Flour", "Patanjali", 259, 250),
    ("Tata Sampann Rava 500g", "Tata Sampann Sooji Rava 500g", "Grocery", "Flour", "Tata", 55, 300),
    ("Besan 500g", "Tata Sampann Besan 500g", "Grocery", "Flour", "Tata", 79, 280),
    ("Chocos 260g", "Kellogg's Chocos chocolate cereal", "Grocery", "Cereals", "Kellogg's", 179, 200),
    ("Horlicks 500g", "Horlicks Classic Malt 500g health drink", "Grocery", "Cereals", "Horlicks", 279, 180),
    ("Complan 500g", "Complan Royale Chocolate 500g", "Grocery", "Cereals", "Complan", 299, 150),
    ("Bournvita 500g", "Cadbury Bournvita 500g health drink", "Grocery", "Cereals", "Cadbury", 329, 160),
    ("Pedigree Dog Food 3kg", "Pedigree Adult Dry Dog Food 3kg", "Grocery", "Packaged Foods", "Pedigree", 499, 100),
    ("Maggi Hot & Sweet 200g", "Maggi Hot & Sweet Chilli Sauce 200g", "Grocery", "Sauces", "Maggi", 79, 250),
    ("Hellmanns Mayo 300g", "Hellmanns Real Mayonnaise 300g", "Grocery", "Sauces", "Hellmanns", 189, 150),
    ("Weikfield Corn Flour 100g", "Weikfield Corn Starch 100g", "Grocery", "Packaged Foods", "Weikfield", 45, 200),
    ("Amul Butter 100g", "Amul Pasteurised Butter 100g", "Grocery", "Packaged Foods", "Amul", 56, 300),
]

# ──────────────────────────────────────────────────────────
# 40 SUPERMARKET products
# ──────────────────────────────────────────────────────────
SUPERMARKET = [
    ("Surf Excel Matic 1L", "Surf Excel Matic Liquid Detergent 1L", "Supermarket", "Detergents", "Surf Excel", 199, 100),
    ("Tide Original 1kg", "Tide Original Powder Detergent 1kg", "Supermarket", "Detergents", "Tide", 159, 120),
    ("Ariel Matic 1L", "Ariel Matic Liquid Detergent 1L", "Supermarket", "Detergents", "Ariel", 219, 90),
    ("Harpic Power Plus 1L", "Harpic Power Plus Toilet Cleaner 1L", "Supermarket", "Cleaning Products", "Harpic", 99, 150),
    ("Lizol Floor Cleaner 975ml", "Lizol Citrus Floor Cleaner 975ml", "Supermarket", "Cleaning Products", "Lizol", 169, 130),
    ("Vim Dishwash Liquid 500ml", "Vim Dishwash Liquid Lemon 500ml", "Supermarket", "Dishwashing", "Vim", 99, 180),
    ("Pril Dishwasher 500ml", "Pril Dishwashing Liquid 500ml", "Supermarket", "Dishwashing", "Pril", 119, 140),
    ("Colin Glass Cleaner 500ml", "Colin Glass & Surface Cleaner 500ml", "Supermarket", "Cleaning Products", "Colin", 79, 160),
    ("Comfort Fabric Conditioner 1L", "Comfort After Wash 1L", "Supermarket", "Detergents", "Comfort", 199, 110),
    ("Klin Stain Remover 500ml", "Klin Stain Remover Liquid 500ml", "Supermarket", "Cleaning Products", "Klin", 129, 100),
    ("Kleenex Tissue Box 100s", "Kleenex Facial Tissue 100 pulls", "Supermarket", "Tissues", "Kleenex", 99, 150),
    ("Tempo Disposable Plates 20pcs", "Tempo Disposable Paper Plates 20pcs", "Supermarket", "Kitchen Supplies", "Tempo", 45, 200),
    ("Glen Forza Kitchen Rack", "Glen Forza Stainless Steel Kitchen Rack", "Supermarket", "Kitchen Supplies", "Glen", 1299, 25),
    ("Tupperware Container 1L", "Tupperware Plastic Container 1L", "Supermarket", "Storage Products", "Tupperware", 399, 40),
    ("Signoraware Container Set", "Signoraware Container Set of 3", "Supermarket", "Storage Products", "Signoraware", 299, 50),
    ("Prestige STriendly Jar", "Prestige Stainless Steel Jar 750ml", "Supermarket", "Kitchen Supplies", "Prestige", 349, 35),
    ("Sistema Lunch Box 1L", "Sistema Bento Lunch Box 1L", "Supermarket", "Kitchen Supplies", "Sistema", 499, 30),
    ("Eveready AA Batteries 10pc", "Eveready Red AA Batteries 10 pack", "Supermarket", "Batteries", "Eveready", 149, 200),
    ("Duracell AA Batteries 8pc", "Duracell Coppertop AA 8 pack", "Supermarket", "Batteries", "Duracell", 299, 120),
    ("Milton Water Bottle 750ml", "Milton Thermosteel Bottle 750ml", "Supermarket", "Water Bottles", "Milton", 599, 60),
    ("Cello Opalware Bowl Set", "Cello Opalware Dinner Set 18pc", "Supermarket", "Kitchen Supplies", "Cello", 1499, 30),
    ("Nayasa Smart Jar Set", "Nayasa Smart Storage Jar Set 6pc", "Supermarket", "Storage Products", "Nayasa", 599, 45),
    ("Agarwal Brand Store Container", "Agarwal Brand Spice Box Stainless Steel", "Supermarket", "Kitchen Supplies", "Agarwal", 449, 35),
    ("Scotch Brite Sponge 6pc", "Scotch Brite Heavy Duty Sponge 6 pack", "Supermarket", "Dishwashing", "Scotch Brite", 139, 150),
    ("Vim Bar 200g", "Vim Dishwash Bar 200g pack of 4", "Supermarket", "Dishwashing", "Vim", 88, 200),
    ("Odonil Air Freshener 75g", "Odonil Air Freshener Blocks 75g", "Supermarket", "Household Products", "Odonil", 65, 180),
    ("Hit Insect Spray 400ml", "Hit Insect Killer Spray 400ml", "Supermarket", "Household Products", "Hit", 149, 120),
    ("Good Knight Refill 2pk", "Good Knight Power Liquid Refill 2pk", "Supermarket", "Household Products", "Good Knight", 99, 150),
    ("Lysol Disinfectant 500ml", "Lysol Disinfectant Surface Cleaner 500ml", "Supermarket", "Cleaning Products", "Lysol", 179, 100),
    ("Dettol Liquid 200ml", "Dettol Antiseptic Liquid 200ml", "Supermarket", "Household Products", "Dettol", 89, 200),
    ("Domex Toilet Cleaner 500ml", "Domex Toilet Cleaner 500ml", "Supermarket", "Cleaning Products", "Domex", 79, 160),
    ("Bajaj Majesty OTG 36L", "Bajaj Majesty OTG 36L Oven Toaster", "Supermarket", "Kitchen Supplies", "Bajaj", 5999, 15),
    ("Prestige Induction Cooktop", "Prestige PIC 16.0+ Induction Cooktop", "Supermarket", "Kitchen Supplies", "Prestige", 2999, 25),
    ("Butterfly Stainless Steel Cooker", "Butterfly Deluxe Plus 5L Pressure Cooker", "Supermarket", "Kitchen Supplies", "Butterfly", 1799, 30),
    ("Hawkins Futura 3L Kadhai", "Hawkins Futura Non-Stick Kadhai 3L", "Supermarket", "Kitchen Supplies", "Hawkins", 1499, 20),
    ("Borosil Klip N Store 400ml", "Borosil Klip N Store Glass Container 400ml", "Supermarket", "Storage Products", "Borosil", 349, 40),
    ("Flipkart Smartpart Storage Bags", "Flipkart Smartpart Ziplock Bags 100pc", "Supermarket", "Storage Products", "Flipkart", 149, 80),
    ("Nilkamal Plastic Chair", "Nilkamal Freedom HD Plastic Chair", "Supermarket", "Household Products", "Nilkamal", 2299, 30),
    ("Cello Hexaware Casserole Set", "Cello Hexaware Casserole Set 3pc", "Supermarket", "Kitchen Supplies", "Cello", 1199, 25),
    ("Prestige Stainless Steel Tawa", "Prestige SS Flat Tawa 26cm", "Supermarket", "Kitchen Supplies", "Prestige", 899, 35),
]

# ──────────────────────────────────────────────────────────
# 50 CLOTHING products
# ──────────────────────────────────────────────────────────
CLOTHING = [
    ("Men's Cotton Round Neck T-Shirt", "Premium cotton round neck t-shirt", "Clothing", "T-shirts", "Allen Solly", 799, 60),
    ("Men's Polo Collar T-Shirt", "Classic polo t-shirt for men", "Clothing", "T-shirts", "US Polo", 999, 50),
    ("Men's Slim Fit Formal Shirt", "Slim fit cotton formal shirt", "Clothing", "Shirts", "Arrow", 1499, 40),
    ("Men's Casual Denim Shirt", "Washed denim casual shirt", "Clothing", "Shirts", "Levis", 1999, 35),
    ("Women's Kurti Tunic", "Printed cotton kurti for women", "Clothing", "Kurtas", "W", 899, 45),
    ("Men's Regular Fit Jeans", "Classic regular fit blue jeans", "Clothing", "Jeans", "Levis", 2499, 50),
    ("Men's Slim Fit Trousers", "Slim fit chino trousers", "Clothing", "Trousers", "Van Heusen", 1799, 40),
    ("Women's Printed Palazzo", "Floral printed palazzo pants", "Clothing", "Trousers", "W", 699, 55),
    ("Men's Denim Shorts", "Regular fit denim shorts", "Clothing", "Shorts", "Jack & Jones", 1299, 35),
    ("Women's Cotton Shorts", "Comfortable cotton casual shorts", "Clothing", "Shorts", "H&M", 599, 50),
    ("Men's Puffer Jacket", "Lightweight puffer winter jacket", "Clothing", "Jackets", "Decathlon", 2999, 20),
    ("Women's Hooded Sweatshirt", "Comfortable hooded sweatshirt", "Clothing", "Hoodies", "H&M", 1499, 30),
    ("Men's Fleece Hoodie", "Zipper fleece hoodie for men", "Clothing", "Hoodies", "Puma", 1999, 25),
    ("Women's A-Line Dress", "Printed A-line casual dress", "Clothing", "Dresses", "Max", 1299, 30),
    ("Women's Silk Saree", "Traditional Banarasi silk saree", "Clothing", "Sarees", "Mira", 3999, 15),
    ("Women's Cotton Leggings", "Comfortable cotton leggings 2 pack", "Clothing", "Leggings", "Jockey", 599, 60),
    ("Men's Classic White Shirt", "Crisp white cotton formal shirt", "Clothing", "Shirts", "Raymond", 1999, 35),
    ("Men's Jogger Pants", "Comfortable cotton jogger pants", "Clothing", "Trousers", "Puma", 1799, 40),
    ("Women's Georgette Saree", "Printed georgette saree with blouse", "Clothing", "Sarees", "Biba", 1499, 25),
    ("Men's Graphic Print T-Shirt", "Bold graphic print cotton tee", "Clothing", "T-shirts", "Levis", 1199, 45),
    ("Women's Maxi Dress", "Floral printed maxi dress", "Clothing", "Dresses", "AND", 2499, 20),
    ("Men's Chino Shorts", "Slim fit chino shorts", "Clothing", "Shorts", "Tommy Hilfiger", 1999, 30),
    ("Women's Denim Jacket", "Classic blue denim jacket", "Clothing", "Jackets", "Levis", 3499, 15),
    ("Men's Henley T-Shirt", "Long sleeve henley neck t-shirt", "Clothing", "T-shirts", "Jack & Jones", 899, 40),
    ("Women's Shrug Cardigan", "Lightweight open front shrug", "Clothing", "Jackets", "W", 799, 35),
    ("Men's Cargo Pants", "Relaxed fit cargo pants", "Clothing", "Trousers", "Decathlon", 1499, 30),
    ("Women's Plaid Shirt", "Casual plaid cotton shirt", "Clothing", "Shirts", "H&M", 1299, 25),
    ("Men's Track Pants", "Athletic track pants with stripes", "Clothing", "Trousers", "Adidas", 2299, 35),
    ("Women's Anarkali Kurti", "Elegant Anarkali suit kurti", "Clothing", "Kurtas", "Biba", 1999, 20),
    ("Men's V-Neck Sweater", "Lightweight v-neck sweater", "Clothing", "Hoodies", "Allen Solly", 1799, 18),
    ("Women's Churidar Set", "Cotton churidar with kurta", "Clothing", "Kurtas", "W", 1299, 25),
    ("Men's Formal Blazer", "Slim fit single button blazer", "Clothing", "Jackets", "Van Heusen", 3999, 12),
    ("Kids Graphic T-Shirt", "Fun graphic print t-shirt for kids", "Clothing", "T-shirts", "H&M", 499, 40),
    ("Kids Denim Jeans", "Stretchable denim jeans for kids", "Clothing", "Jeans", "Levis", 1299, 30),
    ("Women's Sports Bra", "High impact sports bra", "Clothing", "Sportswear", "Nike", 1999, 25),
    ("Men's Running Shorts", "Breathable running shorts", "Clothing", "Sportswear", "Nike", 1499, 30),
    ("Men's Compression Tights", "Athletic compression tights", "Clothing", "Sportswear", "Puma", 1299, 20),
    ("Women's Yoga Pants", "High waist yoga pants", "Clothing", "Sportswear", "Decathlon", 999, 35),
    ("Men's Polo T-Shirt 3 Pack", "3 pack cotton polo t-shirts", "Clothing", "T-shirts", "Jockey", 1499, 40),
    ("Women's Cotton Night Suit", "Comfortable cotton night suit set", "Clothing", "Innerwear", "Jockey", 899, 45),
    ("Men's Boxer Briefs 3pk", "Cotton boxer briefs 3 pack", "Clothing", "Innerwear", "Jockey", 699, 50),
    ("Women's Cotton Bra 3pk", "Non-wired cotton bras 3 pack", "Clothing", "Innerwear", "Jockey", 999, 40),
    ("Men's Ankle Socks 5pk", "Cotton ankle socks 5 pack", "Clothing", "Socks", "Puma", 499, 60),
    ("Women's Knee High Socks 3pk", "Cotton knee high socks 3 pack", "Clothing", "Socks", "H&M", 399, 50),
    ("Kids Winter Jacket", "Warm padded winter jacket for kids", "Clothing", "Jackets", "Decathlon", 1799, 20),
    ("Women's Silk Blend Kurta", "Elegant silk blend kurta", "Clothing", "Kurtas", "Fabindia", 2499, 15),
    ("Men's Linen Shirt", "Pure linen casual shirt", "Clothing", "Shirts", "Fabindia", 2499, 18),
    ("Women's Cotton Saree", "Handloom cotton saree", "Clothing", "Sarees", "Fabindia", 1999, 20),
    ("Men's Flex Shorts", "Stretchable active shorts", "Clothing", "Shorts", "Decathlon", 799, 40),
    ("Women's Knit Cardigan", "Cozy knit open cardigan", "Clothing", "Hoodies", "H&M", 1799, 22),
]

# ──────────────────────────────────────────────────────────
# 30 FOOTWEAR products
# ──────────────────────────────────────────────────────────
FOOTWEAR = [
    ("Nike Revolution 6", "Nike Revolution 6 Running Shoes", "Footwear", "Running Shoes", "Nike", 3995, 30),
    ("Adidas Duramo Speed", "Adidas Duramo Speed Running Shoes", "Footwear", "Running Shoes", "Adidas", 5999, 25),
    ("Puma Deviate Nitro 2", "Puma Deviate Nitro 2 Running Shoes", "Footwear", "Running Shoes", "Puma", 8999, 15),
    ("ASICS Gel-Nimbus 25", "ASICS Gel-Nimbus 25 Running Shoes", "Footwear", "Running Shoes", "ASICS", 12999, 10),
    ("New Balance 574", "New Balance 574 Classic Sneakers", "Footwear", "Casual Shoes", "New Balance", 8999, 20),
    ("Nike Air Max 90", "Nike Air Max 90 Classic Sneakers", "Footwear", "Casual Shoes", "Nike", 11999, 18),
    ("Adidas Stan Smith", "Adidas Stan Smith Classic White", "Footwear", "Casual Shoes", "Adidas", 7999, 22),
    ("Puma Smash V2", "Puma Smash V2 Classic Sneakers", "Footwear", "Casual Shoes", "Puma", 4999, 30),
    ("Woodland Men's Boots", "Woodland Leather Casual Boots", "Footwear", "Casual Shoes", "Woodland", 3999, 25),
    ("Bata Men's Formal Shoes", "Bata Leather Formal Derby Shoes", "Footwear", "Formal Shoes", "Bata", 2999, 35),
    ("Clarks Formal Oxford", "Clarks Men's Formal Oxford Shoes", "Footwear", "Formal Shoes", "Clarks", 7999, 12),
    ("Red Tape Formal Loafer", "Red Tape Men's Formal Loafer", "Footwear", "Formal Shoes", "Red Tape", 2499, 30),
    ("Liberty Action Shoes", "Liberty Men's Sports Running Shoes", "Footwear", "Sports Shoes", "Liberty", 1499, 40),
    ("Nivia Storm Football Shoe", "Nivia Storm Turf Football Shoe", "Footwear", "Sports Shoes", "Nivia", 799, 50),
    ("Campus Running Shoes", "Campus Men's Running Shoes Oxyfit", "Footwear", "Running Shoes", "Campus", 1299, 45),
    ("Paragon Floaters Men", "Paragon Floaters Casual Sandals", "Footwear", "Sandals", "Paragon", 499, 80),
    ("Crocs Classic Clog", "Crocs Classic Unisex Clog", "Footwear", "Sandals", "Crocs", 2999, 25),
    ("Bata Flippers", "Bata Men's Flippers Slippers", "Footwear", "Slippers", "Bata", 349, 70),
    ("Hawai Slippers", "Hawai Classic Rubber Slippers", "Footwear", "Slippers", "Hawai", 199, 100),
    ("Nike Sunray Protect", "Nike Sunray Protect 2 Sandals", "Footwear", "Sandals", "Nike", 2999, 20),
    ("Sparx Sports Shoes", "Sparx Men's Sports Running Shoes", "Footwear", "Sports Shoes", "Sparx", 999, 60),
    ("ASICS Gel-Kayano 30", "ASICS Gel-Kayano 30 Stability Shoes", "Footwear", "Running Shoes", "ASICS", 15999, 8),
    ("Reebok Classic Leather", "Reebok Classic Leather Sneakers", "Footwear", "Casual Shoes", "Reebok", 6999, 22),
    ("Under Armour Charged Assert", "UA Charged Assert 9 Running Shoes", "Footwear", "Running Shoes", "Under Armour", 6999, 18),
    ("Crocs literide 360", "Crocs Literide 360 Clog", "Footwear", "Sandals", "Crocs", 3999, 20),
    ("Hush Puppies Oxford", "Hush Puppies Men's Formal Oxford", "Footwear", "Formal Shoes", "Hush Puppies", 6999, 15),
    ("Bata Kids School Shoes", "Bata Kids Velcro School Shoes", "Footwear", "School Shoes", "Bata", 999, 40),
    ("Lancer Sports Shoes", "Lancer Men's Sports Running Shoes", "Footwear", "Sports Shoes", "Lancer", 699, 55),
    ("Birkenstock Arizona", "Birkenstock Arizona Soft Footbed", "Footwear", "Sandals", "Birkenstock", 4999, 12),
    ("Woodland Sandals", "Woodland Men's Leather Sandals", "Footwear", "Sandals", "Woodland", 1999, 25),
]

# ──────────────────────────────────────────────────────────
# 40 ACCESSORIES products
# ──────────────────────────────────────────────────────────
ACCESSORIES = [
    ("WildHorn Leather Wallet", "Genuine leather bifold wallet", "Accessories", "Wallets", "WildHorn", 899, 45),
    ("Allen Solly Slim Wallet", "RFID blocking slim wallet", "Accessories", "Wallets", "Allen Solly", 1299, 35),
    ("Tommy Hilfiger Wallet", "Tommy Hilfiger Men's Classic Wallet", "Accessories", "Wallets", "Tommy Hilfiger", 2499, 20),
    ("Formal Leather Belt", "Genuine leather formal belt", "Accessories", "Belts", "Allen Solly", 999, 40),
    ("Casual Woven Belt", "Casual fabric woven belt for men", "Accessories", "Belts", "H&M", 499, 50),
    ("Wildcraft Backpack 32L", "Wildcraft 32L Laptop Backpack", "Accessories", "Backpacks", "Wildcraft", 2499, 30),
    ("Skybags Laptop Backpack", "Skybags 27L Laptop Backpack", "Accessories", "Backpacks", "Skybags", 1999, 35),
    ("American Tourister Backpack", "American Tourister 32L Backpack", "Accessories", "Backpacks", "American Tourister", 2999, 25),
    ("Safari Pentagon Trolley Bag", "Safari 55cm Hardside Trolley Bag", "Accessories", "Travel Bags", "Safari", 3999, 20),
    ("Antler Suited Carry On", "Antler 55cm Polycarbonate Trolley", "Accessories", "Travel Bags", "Antler", 5999, 12),
    ("Lino Perros Handbag", "Women's Faux Leather Handbag", "Accessories", "Handbags", "Lino Perros", 1499, 30),
    ("Lavie Crossbody Bag", "Lavie Women's Crossbody Sling Bag", "Accessories", "Handbags", "Lavie", 1999, 25),
    ("Fastrack Sunglasses", "Fastrack UV400 Sunglasses", "Accessories", "Sunglasses", "Fastrack", 799, 45),
    ("Ray-Ban Aviator", "Ray-Ban Classic Aviator Sunglasses", "Accessories", "Sunglasses", "Ray-Ban", 8999, 10),
    ("Fossil Analog Watch", "Fossil Men's Analog Stainless Steel Watch", "Accessories", "Watches", "Fossil", 8999, 15),
    ("Casio G-Shock", "Casio G-Shock Digital Watch", "Accessories", "Watches", "Casio", 9999, 12),
    ("Titan Raga Watch", "Titan Raga Women's Analog Watch", "Accessories", "Watches", "Titan", 3999, 25),
    ("Capsule Travel Cap", "Adjustable cotton travel cap", "Accessories", "Caps", "Puma", 499, 50),
    ("Nike Running Cap", "Nike Dri-FIT Running Cap", "Accessories", "Caps", "Nike", 799, 35),
    ("Safari Laptop Bag", "Safari 15.6 inch Laptop Messenger", "Accessories", "Laptop Bags", "Safari", 1499, 30),
    ("HP Laptop Backpack", "HP Bumper 15.6 inch Backpack", "Accessories", "Laptop Bags", "HP", 1999, 25),
    ("Spigen iPhone 15 Case", "Spigen Liquid Air Case iPhone 15", "Accessories", "Phone Cases", "Spigen", 999, 50),
    ("Tempered Glass Screen Guard", "9H Tempered Glass Screen Guard", "Accessories", "Phone Cases", "Generic", 299, 100),
    ("Samsung S24 Ultra Case", "Samsung Official Clear Case S24 Ultra", "Accessories", "Phone Cases", "Samsung", 1499, 30),
    ("OnePlus 12 Case", "OnePlus Sandstone Case OnePlus 12", "Accessories", "Phone Cases", "OnePlus", 799, 40),
    ("Keychain LED Light", "Aluminum LED Light Keychain", "Accessories", "Keychains", "Generic", 199, 80),
    ("Leather Key Holder", "Genuine leather key holder pouch", "Accessories", "Keychains", "WildHorn", 399, 45),
    ("Apple AirTag 4 Pack", "Apple AirTag 4 Pack Tracker", "Accessories", "Keychains", "Apple", 9900, 15),
    ("Safari Card Holder", "Safari Slim Card Holder Wallet", "Accessories", "Wallets", "Safari", 699, 40),
    ("Wildcraft Gym Bag", "Wildcraft 20L Duffel Gym Bag", "Accessories", "Travel Bags", "Wildcraft", 1499, 25),
    ("Allen Solly Men's Sunglasses", "Polarized UV400 Sunglasses", "Accessories", "Sunglasses", "Allen Solly", 1299, 30),
    ("Casio Edifice Watch", "Casio Edifice Chronograph Watch", "Accessories", "Watches", "Casio", 12999, 8),
    ("Fastrack Analog Watch", "Fastrack Men's Casual Analog Watch", "Accessories", "Watches", "Fastrack", 2499, 25),
    ("Daniel Klein Watch", "Daniel Klein Men's Chrono Watch", "Accessories", "Watches", "Daniel Klein", 3499, 18),
    ("Lavie Women's Tote Bag", "Lavie Women's Nylon Tote Bag", "Accessories", "Handbags", "Lavie", 2499, 20),
    ("American Tourister Sling", "AT Cross Body Sling Bag", "Accessories", "Travel Bags", "American Tourister", 1299, 30),
    ("Premium Sunglasses Case", "Hard Shell Sunglasses Carrying Case", "Accessories", "Sunglasses", "Generic", 299, 60),
    ("Samsung Galaxy Watch Band", "Silicone Replacement Band 20mm", "Accessories", "Phone Cases", "Generic", 499, 45),
    ("Apple Watch Strap", "Silicone Sport Band 42/44mm", "Accessories", "Phone Cases", "Generic", 399, 50),
    ("Nomad Slim Wallet", "Nomad Rugged Slim Leather Wallet", "Accessories", "Wallets", "Nomad", 1999, 15),
]

# ──────────────────────────────────────────────────────────
# 40 HOME & KITCHEN products
# ──────────────────────────────────────────────────────────
HOME_KITCHEN = [
    ("Prestige Induction Base Cooker", "Prestige Popular Plus 5L Pressure Cooker", "Home & Kitchen", "Cookware", "Prestige", 1899, 30),
    ("Hawkins Contura Cooker", "Hawkins Contura Hard Anodized 3L", "Home & Kitchen", "Cookware", "Hawkins", 1699, 25),
    ("Butterfly Stainless Steel Set", "Butterfly SS 3 Piece Cookware Set", "Home & Kitchen", "Cookware", "Butterfly", 2999, 20),
    ("Prestige Non-Stick Tawa", "Prestige Omega Select 26cm Tawa", "Home & Kitchen", "Cookware", "Prestige", 799, 35),
    ("Prestige Mixer Grinder", "Prestige Iris 750W Mixer Grinder", "Home & Kitchen", "Mixers", "Prestige", 2999, 25),
    ("Bajaj Rex Mixer Grinder", "Bajaj Rex 500W Mixer Grinder", "Home & Kitchen", "Mixers", "Bajaj", 1999, 30),
    ("Philips Mixer Grinder", "Philips HL7756 750W Mixer Grinder", "Home & Kitchen", "Mixers", "Philips", 3999, 20),
    ("Preethi Blue Leaf Mixer", "Preethi Blue Leaf Platinum 750W", "Home & Kitchen", "Mixers", "Preethi", 3499, 22),
    ("Bajaj Induction Cooktop", "Bajaj ICX Induction Cooktop", "Home & Kitchen", "Induction Cooktops", "Bajaj", 2199, 30),
    ("Prestige Induction Cooktop", "Prestige PIC 20.0+ Induction", "Home & Kitchen", "Induction Cooktops", "Prestige", 2499, 28),
    ("Butterfly Induction Cooktop", "Butterfly Blitz 1600W Induction", "Home & Kitchen", "Induction Cooktops", "Butterfly", 2799, 25),
    ("Prestige Electric Kettle", "Prestige PKOSS 1.5L Electric Kettle", "Home & Kitchen", "Electric Kettles", "Prestige", 799, 40),
    ("Bajaj Electric Kettle", "Bajaj Grand 1.7L Electric Kettle", "Home & Kitchen", "Electric Kettles", "Bajaj", 699, 45),
    ("Havells Electric Kettle", "Havells Crown 1.7L Electric Kettle", "Home & Kitchen", "Electric Kettles", "Havells", 999, 35),
    ("Prestige SS Container Set", "Prestige Stainless Steel Container 3pc", "Home & Kitchen", "Storage Containers", "Prestige", 999, 30),
    ("Milton Thermosteel Bottle", "Milton Thermosteel 750ml Bottle", "Home & Kitchen", "Storage Containers", "Milton", 549, 50),
    ("Signoraware Container Set", "Signoraware 4pc Storage Container", "Home & Kitchen", "Storage Containers", "Signoraware", 399, 45),
    ("Wakefit Ortho Mattress", "Wakefit Orthopedic Memory Foam Queen", "Home & Kitchen", "Bedsheets", "Wakefit", 8999, 15),
    ("Solimo Bedsheet King Size", "Amazon Solimo Cotton Bedsheet King", "Home & Kitchen", "Bedsheets", "Solimo", 899, 40),
    ("Bombay Dyeing Bedsheet", "Bombay Dyeing Cotton Bedsheet Double", "Home & Kitchen", "Bedsheets", "Bombay Dyeing", 1499, 30),
    ("Wakefit Dreamlite Pillow", "Wakefit Microfiber Soft Pillow 2pc", "Home & Kitchen", "Pillows", "Wakefit", 699, 40),
    ("Kurl-On Dreamz Pillow", "Kurl-On Dreamz Fibre Pillow", "Home & Kitchen", "Pillows", "Kurl-On", 499, 50),
    ("Syska LED Table Lamp", "Syska SSK-RDL-9W LED Table Lamp", "Home & Kitchen", "Lamps", "Syska", 799, 35),
    ("Philips LED Desk Lamp", "Philips3000 LED Desk Lamp EyeComfort", "Home & Kitchen", "Lamps", "Philips", 2499, 20),
    ("IKEA TRÅDFRI Desk Lamp", "IKEA TRÅDFRI LED Work Lamp", "Home & Kitchen", "Lamps", "IKEA", 1999, 15),
    ("Prestige Electric Cooker", "Prestige PRWO 1.8-2 Electric Rice Cooker", "Home & Kitchen", "Kitchen Appliances", "Prestige", 2499, 25),
    ("Bajaj Majesty OTG 25L", "Bajaj Majesty OTG 25L Oven", "Home & Kitchen", "Kitchen Appliances", "Bajaj", 4499, 18),
    ("Philips Air Fryer", "Philips Airfryer HD9200 4.1L", "Home & Kitchen", "Kitchen Appliances", "Philips", 8999, 12),
    ("Prestige Air Fryer", "Prestige PAF 6.0 2.2L Air Fryer", "Home & Kitchen", "Kitchen Appliances", "Prestige", 6999, 15),
    ("Borosil Glass Set", "Borosil Klip N Store Glass Set 3pc", "Home & Kitchen", "Storage Containers", "Borosil", 1199, 30),
    ("IKEA KALLAX Shelf", "IKEA KALLAX Shelf Unit 4x2 White", "Home & Kitchen", "Furniture Accessories", "IKEA", 7999, 8),
    ("IKEA MICKE Desk", "IKEA MICKE Desk 105x45cm", "Home & Kitchen", "Furniture Accessories", "IKEA", 5999, 10),
    ("IKEA LACK Side Table", "IKEA LACK Side Table 55x55cm", "Home & Kitchen", "Furniture Accessories", "IKEA", 1299, 20),
    ("Cello Opalware Thali Set", "Cello Opalware Dinner Thali Set 4pc", "Home & Kitchen", "Cookware", "Cello", 1199, 25),
    ("Prestige Frying Pan", "Prestige Hard Anodized Frying Pan 24cm", "Home & Kitchen", "Cookware", "Prestige", 649, 35),
    ("Hawkins Futura Kadhai", "Hawkins Futura Hard Anodized Kadhai 3L", "Home & Kitchen", "Cookware", "Hawkins", 1299, 28),
    ("Butterfly Stainless Steel Tumbler", "Butterfly SS Tumbler Set 4pc", "Home & Kitchen", "Utensils", "Butterfly", 599, 40),
    ("Milton Insulated Casserole", "Milton Insulated Casserole 1L", "Home & Kitchen", "Utensils", "Milton", 499, 35),
    ("Prestige Spatula Set", "Prestige Nylon Spatula Set 3pc", "Home & Kitchen", "Utensils", "Prestige", 349, 45),
    ("IKEA KORKEN Jar Set", "IKEA KORKEN Glass Jar Set 3pc", "Home & Kitchen", "Storage Containers", "IKEA", 599, 30),
]

# ──────────────────────────────────────────────────────────
# 30 PERSONAL CARE products
# ──────────────────────────────────────────────────────────
PERSONAL_CARE = [
    ("Head & Shoulders Shampoo 400ml", "H&S Cool Menthol Shampoo 400ml", "Personal Care", "Shampoo", "Head & Shoulders", 289, 80),
    ("Dove Shampoo 340ml", "Dove Hair Fall Rescue Shampoo 340ml", "Personal Care", "Shampoo", "Dove", 299, 75),
    ("Pantene Shampoo 340ml", "Pantene Advanced Hair Fall Solution", "Personal Care", "Shampoo", "Pantene", 279, 80),
    (" Clinic Plus Shampoo 175ml", "Clinic Plus Strong & Long Shampoo", "Personal Care", "Shampoo", "Clinic Plus", 99, 100),
    ("Nivea Men Soap 150g", "Nivea Men Deep Impact Soap 150g", "Personal Care", "Soap", "Nivea", 129, 90),
    ("Dettol Soap 75g", "Dettol Original Soap 75g", "Personal Care", "Soap", "Dettol", 42, 150),
    ("Pears Pure Glycerine Soap 125g", "Pears Pure Glycerine Gentle Soap", "Personal Care", "Soap", "Pears", 75, 120),
    ("Lifebuoy Soap 150g", "Lifebuoy Total 10 Soap 150g", "Personal Care", "Soap", "Lifebuoy", 55, 130),
    ("Colgate MaxFresh 150g", "Colgate MaxFresh Toothpaste 150g", "Personal Care", "Toothpaste", "Colgate", 99, 100),
    ("Pepsodent Germ Check 150g", "Pepsodent Germ Check Plus Toothpaste", "Personal Care", "Toothpaste", "Pepsodent", 79, 110),
    ("Sensodyne Sensitive 75g", "Sensodyne Toothpaste for Sensitive", "Personal Care", "Toothpaste", "Sensodyne", 119, 90),
    ("Himalaya Face Wash 100ml", "Himalaya Neem Face Wash 100ml", "Personal Care", "Skincare", "Himalaya", 170, 80),
    ("Nivea Moisturizer 100ml", "Nivea Soft Light Moisturizer 100ml", "Personal Care", "Skincare", "Nivea", 199, 70),
    ("Garnier SkinBright Serum", "Garnier Bright Complete Vitamin C Serum", "Personal Care", "Skincare", "Garnier", 299, 50),
    ("Mamaearth Vitamin C Face Cream", "Mamaearth Vitamin C Face Cream 50ml", "Personal Care", "Skincare", "Mamaearth", 399, 40),
    ("Himalaya Herbals Hair Oil 200ml", "Himalaya Anti-Hair Fall Hair Oil", "Personal Care", "Haircare", "Himalaya", 199, 60),
    ("Parachute Coconut Oil 300ml", "Parachute 100% Pure Coconut Oil", "Personal Care", "Haircare", "Parachute", 169, 80),
    ("Bajaj Almond Drops 200ml", "Bajaj Almond Drops Hair Oil 200ml", "Personal Care", "Haircare", "Bajaj", 199, 70),
    ("Set Wet Hair Gel 100ml", "Set Wet Cool Gel 100ml", "Personal Care", "Haircare", "Set Wet", 99, 60),
    ("Gillette Mach3 Razor", "Gillette Mach3 Cartridge Razor", "Personal Care", "Grooming Products", "Gillette", 189, 50),
    ("Philips Trimmer 3000", "Philips Multigroom Series 3000", "Personal Care", "Grooming Products", "Philips", 1199, 30),
    ("Nivea Men Deodorant 150ml", "Nivea Men Power Deodorant 150ml", "Personal Care", "Deodorants", "Nivea", 249, 60),
    ("Wild Stone Deodorant 150ml", "Wild Stone Ultra Sensual Deo 150ml", "Personal Care", "Deodorants", "Wild Stone", 199, 70),
    ("Axe Deodorant 150ml", "Axe Dark Temptation Deo 150ml", "Personal Care", "Deodorants", "Axe", 229, 65),
    ("Dove Body Wash 250ml", "Dove Deeply Nourishing Body Wash", "Personal Care", "Personal Hygiene", "Dove", 249, 50),
    ("Nivea Body Lotion 200ml", "Nivea Body Milk Lotion 200ml", "Personal Care", "Personal Hygiene", "Nivea", 299, 45),
    ("Vaseline Body Lotion 400ml", "Vaseline Intensive Care Body Lotion", "Personal Care", "Personal Hygiene", "Vaseline", 299, 55),
    ("Himalaya Under Eye Cream", "Himalaya Under Eye Cream 10ml", "Personal Care", "Skincare", "Himalaya", 170, 40),
    ("Boroline Antiseptic 60g", "Boroline Antiseptic Ayurvedic Cream", "Personal Care", "Skincare", "Boroline", 39, 100),
    ("VLCC Face Wash 100ml", "VLCC Insta Glow Diamond Bleach", "Personal Care", "Skincare", "VLCC", 249, 35),
]

# ──────────────────────────────────────────────────────────
# 20 FITNESS products
# ──────────────────────────────────────────────────────────
FITNESS = [
    ("Boldfit Yoga Mat 6mm", "Boldfit 6mm Anti-Skid Yoga Mat", "Fitness", "Yoga Mats", "Boldfit", 699, 60),
    ("AmazonBasics Yoga Mat 8mm", "AmazonBasics 8mm Yoga Mat", "Fitness", "Yoga Mats", "AmazonBasics", 899, 45),
    ("Kobo Exercise Yoga Mat 10mm", "Kobo 10mm Premium Yoga Mat", "Fitness", "Yoga Mats", "Kobo", 1299, 35),
    ("Boldfit Resistance Band Set", "Boldfit Resistance Bands 5 Levels", "Fitness", "Resistance Bands", "Boldfit", 499, 70),
    ("Fitbox Resistance Loop Bands", "Fitbox Loop Bands Set of 5", "Fitness", "Resistance Bands", "Fitbox", 349, 80),
    ("Decathlon Dumbbells 2kg Pair", "Decathlon Neoprene Dumbbells 2kg", "Fitness", "Fitness Accessories", "Decathlon", 599, 50),
    ("Boldfit Kettlebell 6kg", "Boldfit Vinyl Coated Kettlebell 6kg", "Fitness", "Fitness Accessories", "Boldfit", 899, 40),
    ("Decathlon skipping Rope", "Decathlon Skipping Rope Adjustable", "Fitness", "Sports Accessories", "Decathlon", 199, 80),
    ("Nivia Football Size 5", "Nivia Storm Football Size 5", "Fitness", "Sports Accessories", "Nivia", 599, 50),
    ("Nivia Basketball Size 7", "Nivia Meteor Basketball Size 7", "Fitness", "Sports Accessories", "Nivia", 699, 45),
    ("Cosco Cricket Bat", "Cosco Kashmir Willow Cricket Bat", "Fitness", "Sports Accessories", "Cosco", 899, 30),
    ("SG Shield Cricket Bat", "SG Shield Plus Kashmir Willow", "Fitness", "Sports Accessories", "SG", 1499, 25),
    ("Yonex Mavis 350 Shuttlecock", "Yonex Mavis 350 Nylon Shuttle 6pc", "Fitness", "Sports Accessories", "Yonex", 649, 50),
    ("Nivia Tennis Ball 4 Pack", "Nivia Premier Tennis Ball Pack of 4", "Fitness", "Sports Accessories", "Nivia", 299, 60),
    ("Decathlon Gym Gloves", "Decathlon Weight Training Gloves", "Fitness", "Fitness Accessories", "Decathlon", 399, 40),
    ("Boldfit Ab Roller", "Boldfit Ab Roller Wheel Exercise", "Fitness", "Fitness Accessories", "Boldfit", 499, 35),
    ("Lifelong Foam Roller", "Lifelong LLHM114 Foam Roller 45cm", "Fitness", "Fitness Accessories", "Lifelong", 599, 30),
    ("AmazonBasics Water Bottle 1L", "AmazonBasics Tritan Water Bottle 1L", "Fitness", "Water Bottles", "AmazonBasics", 499, 50),
    ("Milton Thermosteel Sports Bottle", "Milton 750ml Sports Bottle Steel", "Fitness", "Water Bottles", "Milton", 449, 55),
    ("Nivia Sports Bag 40L", "Nivia Storm Duffle Bag 40L", "Fitness", "Sports Accessories", "Nivia", 799, 35),
]

# ──────────────────────────────────────────────────────────
# 20 OFFICE & SCHOOL products
# ──────────────────────────────────────────────────────────
OFFICE_SCHOOL = [
    ("Classmate Notebook 240pg", "Classmate Pulse Notebook A4 240 pages", "Office & School", "Notebooks", "Classmate", 89, 200),
    ("Classmate Pulse 172pg", "Classmate Pulse Notebook 172 pages", "Office & School", "Notebooks", "Classmate", 65, 250),
    ("Navneet Top Score Notebook", "Navneet Top Score A4 300 pages", "Office & School", "Notebooks", "Navneet", 129, 150),
    ("Reynolds Blue Pen 10pc", "Reynolds Trimax Fine Carbold Blue 10", "Office & School", "Pens", "Reynolds", 120, 200),
    ("Cello Butterflow Pen 10pc", "Cello Butterflow Ball Pen Blue 10pk", "Office & School", "Pens", "Cello", 100, 180),
    ("Flair Writo-meter Pen 5pc", "Flair Writo-meter Blue Pen 5pk", "Office & School", "Pens", "Flair", 80, 200),
    ("Nataraj Pencil Box 12pc", "Nataraj Drawing Pencils 12pk", "Office & School", "Pencils", "Nataraj", 99, 160),
    ("Doms Zoom Pencil 10pc", "Doms Zoom Triangle Pencils 10pk", "Office & School", "Pencils", "Doms", 55, 200),
    ("Apsara Platinum Pencil 10pc", "Apsara Platinum Extra Dark 10pk", "Office & School", "Pencils", "Apsara", 49, 220),
    ("Faber Castell Colour 12pc", "Faber Castell Classic Colour Pencils 12", "Office & School", "Stationery", "Faber Castell", 99, 150),
    ("Camlin Kokuyo Compass Box", "Camlin Kokuyo Compass Box Essential", "Office & School", "Stationery", "Camlin", 149, 120),
    ("Kores Glue Stick 15g", "Kores Glu Stik Washable 15g 10pk", "Office & School", "Stationery", "Kores", 199, 100),
    ("Casio FX-991EX Calculator", "Casio FX-991EX Scientific Calculator", "Office & School", "Calculators", "Casio", 1199, 80),
    ("Casio MJ-12D Calculator", "Casio MJ-12D Desktop Calculator", "Office & School", "Calculators", "Casio", 549, 100),
    ("HP 15s Laptop Backpack", "HP Bumper 15.6 inch School Backpack", "Office & School", "Backpacks", "HP", 1799, 30),
    ("Wildcraft School Backpack", "Wildcraft 28L School Backpack", "Office & School", "Backpacks", "Wildcraft", 1999, 25),
    ("Skybags Luminos Backpack", "Skybags 32L College Backpack", "Office & School", "Backpacks", "Skybags", 1699, 30),
    ("Classmate Octane Gel Pen 10pc", "Classmate Octane Gel Pen 0.5mm 10pk", "Office & School", "Pens", "Classmate", 130, 180),
    ("Staedtler Norris Pencil 12pc", "Staedtler Norris Eco Pencils 12pk", "Office & School", "Pencils", "Staedtler", 149, 120),
    ("Maped Folder Set 6pc", "Maped.file Folder Set A4 6 colors", "Office & School", "Stationery", "Maped", 199, 100),
]

# ──────────────────────────────────────────────────────────
# Combine all products
# ──────────────────────────────────────────────────────────
ALL_PRODUCTS = (
    ELECTRONICS + GROCERY + SUPERMARKET + CLOTHING +
    FOOTWEAR + ACCESSORIES + HOME_KITCHEN + PERSONAL_CARE +
    FITNESS + OFFICE_SCHOOL
)


async def seed():
    """Seed the database with products."""
    from models.database import async_session
    from models.models import Product, Policy, Merchant, ProductRelationship
    from sqlalchemy import select

    async with async_session() as db:
        # Check if products exist
        result = await db.execute(select(Product).limit(1))
        if result.scalar_one_or_none():
            logger.info("Database already seeded, skipping.")
            return

        # Create merchant
        merchant = Merchant(name="TechZone Electronics", description="Your one-stop multi-category shop")
        db.add(merchant)
        await db.commit()
        await db.refresh(merchant)

        product_ids = []
        categories_seen = set()

        for name, desc, category, subcategory, brand, price, stock in ALL_PRODUCTS:
            pid = _id()
            product = Product(
                id=pid,
                merchant_id=merchant.id,
                name=name,
                description=desc,
                category=category,
                subcategory=subcategory,
                brand=brand,
                price=price,
                currency="INR",
                stock=stock,
                sku=f"SKU-{pid[:8].upper()}",
                rating=round(3.5 + (hash(name) % 16) / 10.0, 1),
                tags=f"{category.lower()},{subcategory.lower()},{brand.lower()}",
            )
            db.add(product)
            product_ids.append(pid)
            categories_seen.add(category)

        # Create product relationships (cross-sell and upsell)
        rels = []
        # Electronics cross-sells
        for i in range(0, min(30, len(product_ids)), 3):
            if i + 1 < len(product_ids):
                rels.append((product_ids[i], product_ids[i+1], "cross-sell", "Frequently bought together"))
            if i + 2 < len(product_ids):
                rels.append((product_ids[i], product_ids[i+2], "upsell", "Consider this premium alternative"))

        for pid, rpid, rtype, reason in rels:
            rel = ProductRelationship(
                product_id=pid,
                related_product_id=rpid,
                relationship_type=rtype,
                reason=reason
            )
            db.add(rel)

        # Create default policy (higher limit for demo)
        policy = Policy(max_transaction_amount=50000, payment_requires_approval=True)
        db.add(policy)

        await db.commit()
        logger.info(f"Seeded {len(ALL_PRODUCTS)} products across {len(categories_seen)} categories, {len(rels)} relationships")

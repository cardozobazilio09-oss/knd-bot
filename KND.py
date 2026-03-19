import requests
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup
import json

BOT_TOKEN = "8278630418:AAG3g7XDj71c55MbXitY2W-sM4GXGZDmd4g"
CHAT_ID = "855908755"

def send_telegram(product, alert_type):
    message = f"""🚨 {alert_type}

🚗 {product['name']}
💰 Price: {product['price']}
📦 Quantity: {product['quantity']}
📊 Status: {'In Stock' if product['in_stock'] else 'Out of Stock'}

🔗 {product['link']}
"""

    try:
        if product["image"]:
            # 🔥 DOWNLOAD IMAGE FIRST
            img_response = requests.get(product["image"])

            if img_response.status_code == 200:
                image_file = BytesIO(img_response.content)

                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

                data = {
                    "chat_id": CHAT_ID,
                    "caption": message
                }

                files = {
                    "photo": ("image.jpg", image_file)
                }

                response = requests.post(url, data=data, files=files)
                print("Photo sent:", response.text)

            else:
                raise Exception("Image download failed")

        else:
            raise Exception("No image")

    except Exception as e:
        print("Image failed:", e)

        # 🔥 FALLBACK TO TEXT
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        data = {
            "chat_id": CHAT_ID,
            "text": message
        }

        response = requests.post(url, data=data)
        print("Text sent:", response.text)

URL = "https://www.karzanddolls.com/details/mini+gt+/mini-gt/MTY1"

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# ✅ LOAD OLD DATA
try:
    with open("data.json", "r") as f:
        old_data = json.load(f)
except:
    old_data = {}

while True:
    print("Checking...")

    driver.get(URL)
    time.sleep(6)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    cards = soup.select("a[href*='/product/']")

    new_data = {}

    for card in cards:
        try:
            parent = card.parent

            # ✅ LINK
            from urllib.parse import quote

            link = card.get("href")

            if not link.startswith("http"):
                link = "https://www.karzanddolls.com" + link

            # 🔥 FIX SPECIAL CHARACTERS
                link = quote(link, safe=":/?=&")

            # ✅ NAME
            name = link.split("/product/mini-gt/")[1].split("/")[0].replace("-", " ").upper()

            # ✅ PRICE
            text = parent.get_text("\n")
            lines = [l.strip() for l in text.split("\n") if l.strip()]

            price = None
            for line in lines:
                if "rs." in line.lower() or "₹" in line:
                    price = line
                    break

            # ✅ QUANTITY
            qty_element = parent.select_one(".add-top-size li[data-qty]")

            quantity = None
            stock = False

            if qty_element:
                qty_str = qty_element.get("data-qty")
                if qty_str:
                    quantity = int(qty_str)
                    stock = quantity > 0

            # ✅ IMAGE FIX (lazy loading handled)
            img_tag = parent.select_one("img")

            image = None
            if img_tag:
                image = img_tag.get("src") or img_tag.get("data-src")

            if image and image.startswith("/"):
                image = "https://www.karzanddolls.com" + image

            # ✅ PRODUCT OBJECT
            product = {
                "name": name,
                "price": price,
                "quantity": quantity,
                "in_stock": stock,
                "link": link,
                "image": image
            }
            send_telegram(product, "TEST")

            new_data[name] = product

            # 🆕 NEW PRODUCT
            if name not in old_data:
                send_telegram(product, "NEW LISTING")

            # 🔥 RESTOCK
            elif old_data[name]["in_stock"] == False and stock == True:
                send_telegram(product, "RESTOCK")

        except Exception as e:
            print("Error:", e)
            continue

    old_data = new_data

    # ✅ SAVE DATA
    with open("data.json", "w") as f:
        json.dump(old_data, f)

    time.sleep(15)
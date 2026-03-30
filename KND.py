import requests
import time
from bs4 import BeautifulSoup
import json
from io import BytesIO
from datetime import datetime
import pytz

BOT_TOKEN = "8278630418:AAG3g7XDj71c55MbXitY2W-sM4GXGZDmd4g"
CHAT_ID = "855908755"

URLS = [
    "https://www.karzanddolls.com/details/mini+gt+/mini-gt/MTY1",
    "https://www.karzanddolls.com/details/hot+wheels/mainlines/MTEw",
    "https://www.karzanddolls.com/details/hot+wheels/car-culture/MTEx"
]


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
            img_response = requests.get(product["image"])
            if img_response.status_code == 200:
                image_file = BytesIO(img_response.content)

                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
                data = {"chat_id": CHAT_ID, "caption": message}
                files = {"photo": ("image.jpg", image_file)}

                requests.post(url, data=data, files=files)
            else:
                raise Exception("Image failed")
        else:
            raise Exception("No image")

    except:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": message}
        requests.post(url, data=data)


# LOAD OLD DATA
try:
    with open("data.json", "r") as f:
        old_data = json.load(f)
except:
    old_data = {}

first_run = True

while True:
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    current_hour = now.hour

    if 9 <= current_hour < 22:
        print("Checking all URLs...")

        new_data = {}

        for URL in URLS:
            print("Checking:", URL)

            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(URL, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            cards = soup.select("a[href*='/product/']")

            for card in cards:
                try:
                    parent = card.parent

                    link = card.get("href")
                    if not link.startswith("http"):
                        link = "https://www.karzanddolls.com" + link

                    name = link.split("/product/mini-gt/")[1].split("/")[0].replace("-", " ").upper()

                    text = parent.get_text("\n")
                    lines = [l.strip() for l in text.split("\n") if l.strip()]

                    price = None
                    for line in lines:
                        if "rs." in line.lower() or "₹" in line:
                            price = line
                            break

                    qty_element = parent.select_one(".add-top-size li[data-qty]")

                    quantity = None
                    stock = False

                    if qty_element:
                        qty_str = qty_element.get("data-qty")
                        if qty_str:
                            quantity = int(qty_str)
                            stock = quantity > 0

                    img_tag = parent.select_one("img")

                    image = None
                    if img_tag:
                        image = img_tag.get("src") or img_tag.get("data-src")

                    if image and image.startswith("/"):
                        image = "https://www.karzanddolls.com" + image

                    # 🔥 UNIQUE KEY (important for multiple links)
                    key = name + "_" + link

                    product = {
                        "name": name,
                        "price": price,
                        "quantity": quantity,
                        "in_stock": stock,
                        "link": link,
                        "image": image
                    }

                    new_data[key] = product

                    if first_run:
                        pass

                    elif key not in old_data:
                        send_telegram(product, "NEW LISTING")

                    elif old_data[key]["in_stock"] == False and stock == True:
                        send_telegram(product, "RESTOCK")

                except:
                    continue

        old_data = new_data

        with open("data.json", "w") as f:
            json.dump(old_data, f)

        if first_run:
            first_run = False

        time.sleep(10)

    else:
        print("Sleeping... outside active hours")
        time.sleep(60)

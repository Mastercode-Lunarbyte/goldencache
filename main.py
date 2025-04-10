#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
from flask import Flask, request
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import chromedriver_autoinstaller


app = Flask(__name__)

# دریافت توکن تلگرام از متغیر محیطی
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

def get_product_details(product_name):
        chromedriver_autoinstaller.install()  # نصب خودکار نسخه‌ی مناسب در شروع
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    service = Service(executable_path="/usr/bin/chromedriver")  # مسیر استاندارد در کانتینر
    driver = webdriver.Chrome(service=service, options=options)

    all_products = []
    try:
        driver.get("https://emalls.ir/")
        search_box = driver.find_element(By.ID, "ContentPlaceHolder1_SearchInBottom_txtSearch")
        search_box.clear()
        search_box.send_keys(product_name)
        search_box.send_keys(Keys.RETURN)

        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "product-block"))
        )

        time.sleep(2)

        product_blocks = driver.find_elements(By.CLASS_NAME, "product-block")
        for block in product_blocks:
            try:
                product_title = block.find_element(By.CLASS_NAME, "prd-name").text.strip()
                price_text = block.find_element(By.CLASS_NAME, "prd-price").text.strip().replace(",", "").replace("٬", "")
                price = int(price_text)
                seller = block.find_element(By.CLASS_NAME, "btn-buyshop").text.strip()
                data_attr = block.find_element(By.CLASS_NAME, "btn-buyshop").get_attribute("data-esrever")
                seller_link = "https://emalls.ir/" + data_attr[::-1] if data_attr else None

                all_products.append({
                    "title": product_title,
                    "price": price,
                    "seller": seller,
                    "link": seller_link
                })
            except:
                continue
    except:
        return "❌ خطا در دریافت اطلاعات."
    finally:
        driver.quit()

    if not all_products:
        return "❌ هیچ محصولی یافت نشد."

    sorted_products = sorted(all_products, key=lambda x: x["price"])
    best = sorted_products[0]
    return f"📷 {best['title']}\n🛍️ {best['seller']}\n💰 {best['price']} تومان\n🔗 {best['link']}"

@app.route("/", methods=["POST"])
def telegram_webhook():
    data = request.json
    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    if text:
        reply = get_product_details(text)
    else:
        reply = "🔎 لطفاً نام محصول را ارسال کنید."

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": reply})

    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


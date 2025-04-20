import os
import time
import requests
import chromedriver_autoinstaller
from flask import Flask, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_USERNAME = "@goldencache"
ADMIN_IDS = []

def is_user_in_channel(user_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getChatMember"
    params = {"chat_id": CHANNEL_USERNAME, "user_id": user_id}
    response = requests.get(url, params=params).json()
    return response.get("result", {}).get("status") in ["member", "creator", "administrator"]

def format_price(price):
    return f"{price:,}".replace(",", "٬")

def get_product_details(product_name, count=3):
    
    # بررسی خاص برای عبارت "موتور گازی"
    cleaned_name = product_name.replace("‌", "").replace(" ", "").strip().lower()
    if cleaned_name == "موتورگازی":
        
        return "ℹ️ لطفاً این محصول را بدون فاصله یعنی «موتورگازی» سرچ کنین 🙏"

    chromedriver_autoinstaller.install()
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    results = []
    try:
        driver.get("https://emalls.ir/")
        search_box = driver.find_element(By.ID, "ContentPlaceHolder1_SearchInBottom_txtSearch")
        search_box.send_keys(product_name, Keys.RETURN)

        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "product-block"))
        )
        time.sleep(2)

        product_blocks = driver.find_elements(By.CLASS_NAME, "product-block")
        for block in product_blocks:
            try:
                title = block.find_element(By.CLASS_NAME, "prd-name").text.strip()
                price_text = block.find_element(By.CLASS_NAME, "prd-price").text.strip().replace(",", "").replace("٬", "")
                price = int(price_text)
                seller = block.find_element(By.CLASS_NAME, "btn-buyshop").text.strip()
                data_attr = block.find_element(By.CLASS_NAME, "btn-buyshop").get_attribute("data-esrever")
                link = "https://emalls.ir/" + data_attr[::-1] if data_attr else "بدون لینک"

                results.append({
                    "title": title,
                    "price": price,
                    "seller": seller,
                    "link": link
                })
            except:
                continue
    except Exception as e:
        return f"❌ خطا در دریافت اطلاعات:\n{e}"
    finally:
        driver.quit()

    if not results:
        return "❌ هیچ محصولی یافت نشد."

    results = sorted(results, key=lambda x: x["price"])[:count]
    message = f"📦 نتایج برای: *{product_name}*\n\n"
    for i, p in enumerate(results, 1):
        message += f"{i}. 📌 *{p['title']}*\n"
        message += f"   🛒 {p['seller']}\n"
        message += f"   💰 {format_price(p['price'])} تومان\n"
        message += f"   🔗 [لینک خرید]({p['link']})\n\n"
    return message

@app.route("/", methods=["POST"])
def telegram_webhook():
    data = request.json
    message = data.get("message")
    if not message:
        return "no message"

    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    text = message.get("text", "")

    if text.lower() in ["/start", "start", "سلام", "سلام ربات"]:
        welcome = "👋 سلام! خوش اومدی 🌟\nاین ربات بهت کمک می‌کنه **بهترین قیمت** محصولات رو توی فروشگاه‌های آنلاین ایران پیدا کنی.\nفقط کافیه اسم محصول رو بنویسی! 📦💬"
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={
            "chat_id": chat_id, "text": welcome
        })
        return "ok"

    if not is_user_in_channel(user_id) and user_id not in ADMIN_IDS:
        join_msg = f"❗ برای استفاده از ربات لطفاً ابتدا در کانال ما عضو شوید:\n👉 https://t.me/goldencache"
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={
            "chat_id": chat_id, "text": join_msg
        })
        return "ok"

    if text:
        waiting = "⏳ در حال جستجوی محصول مورد نظر شما هستم..."
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={
            "chat_id": chat_id, "text": waiting
        })

        reply = get_product_details(text)
    else:
        reply = "🔎 لطفاً نام محصول را وارد کنید."

    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={
        "chat_id": chat_id,
        "text": reply,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    })
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

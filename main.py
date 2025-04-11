import os
from flask import Flask, request
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import chromedriver_autoinstaller
import json

app = Flask(__name__)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = "@Golden_cache"  # نام گروه تلگرام شما
GROUP_INVITE_LINK = "https://t.me/+WpqVX41kCIw2MWE0"  # لینک دعوت به گروه

# ذخیره اطلاعات کاربران
users_file = "users.json"

# خواندن کاربران از فایل
def load_users():
    if os.path.exists(users_file):
        with open(users_file, 'r') as f:
            return json.load(f)
    return {}

# ذخیره کاربران به فایل
def save_users(users):
    with open(users_file, 'w') as f:
        json.dump(users, f)

users = load_users()

def get_product_details(product_name):
    chromedriver_autoinstaller.install()  # نصب خودکار در آغاز
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=options)

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

def is_member(chat_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getChatMember"
    response = requests.get(url, params={"chat_id": GROUP_ID, "user_id": chat_id})
    data = response.json()
    
    # بررسی عضویت در گروه
    if 'result' in data and 'status' in data['result']:
        status = data['result']['status']
        if status in ["member", "administrator", "creator"]:
            return True
    return False

@app.route("/", methods=["POST"])
def telegram_webhook():
    data = request.json
    chat_id = data["message"]["chat"]["id"]
    username = data["message"]["chat"].get("username", "نامشخص")
    
    # ذخیره اطلاعات کاربر
    if chat_id not in users:
        users[chat_id] = {"username": username}
        save_users(users)

    # بررسی عضویت در گروه
    if not is_member(chat_id):
        reply = (
            f"❌ برای استفاده از ربات باید عضو کانال تلگرام ما باشید.\n"
            f"لطفاً به گروه بپیوندید: {GROUP_INVITE_LINK}"
        )
    else:
        text = data["message"].get("text", "")
        if text.lower() == "/start":
            send_welcome_message(chat_id)
            reply = "🔎 لطفاً نام محصول را ارسال کنید."
        elif text:
            reply = get_product_details(text)
        else:
            reply = "🔎 لطفاً نام محصول را ارسال کنید."

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": reply})

    return "ok"

def send_welcome_message(chat_id):
    message = (
        "👋 سلام! خوش آمدید به ربات مقایسه قیمت محصولات.\n"
        "در این ربات شما می‌توانید با وارد کردن نام محصول، بهترین قیمت آن را پیدا کنید.\n"
        "برای شروع، کافی است نام محصول مورد نظر خود را وارد کنید."
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": message})

@app.route("/", methods=["POST"])
def telegram_webhook():
    data = request.json
    chat_id = data["message"]["chat"]["id"]
    username = data["message"]["chat"].get("username", "نامشخص")
    
    # ذخیره اطلاعات کاربر
    if chat_id not in users:
        users[chat_id] = {"username": username}
        save_users(users)

    # بررسی عضویت در گروه
    if not is_member(chat_id):
        reply = (
            f"❌ برای استفاده از ربات باید عضو گروه تلگرام ما باشید.\n"
            f"لطفاً به گروه بپیوندید: {GROUP_INVITE_LINK}"
        )
    else:
        text = data["message"].get("text", "")
        if text.lower() == "/start":
            send_welcome_message(chat_id)
            reply = "🔎 لطفاً نام محصول را ارسال کنید."
        elif text:
            reply = get_product_details(text)
        else:
            reply = "🔎 لطفاً نام محصول را ارسال کنید."

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": reply})

    return "ok"

@app.route("/stats", methods=["GET"])
def stats():
    total_users = len(users)
    return f"تعداد کل کاربران: {total_users}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

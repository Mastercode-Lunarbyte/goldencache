import time
import requests
from flask import Flask, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller

app = Flask(__name__)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

def get_product_details(product_name):
    chromedriver_autoinstaller.install()
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=options)
    all_products = []

    try:
        driver.get("https://emalls.ir/")
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_SearchInBottom_txtSearch"))
        )
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
                title = block.find_element(By.CLASS_NAME, "prd-name").text.strip()
                price_text = block.find_element(By.CLASS_NAME, "prd-price").text.strip().replace(",", "").replace("٬", "")
                price = int(price_text)
                seller = block.find_element(By.CLASS_NAME, "btn-buyshop").text.strip()
                data_attr = block.find_element(By.CLASS_NAME, "btn-buyshop").get_attribute("data-esrever")
                link = "https://emalls.ir/" + data_attr[::-1] if data_attr else None

                all_products.append({
                    "title": title,
                    "price": price,
                    "seller": seller,
                    "link": link
                })
            except:
                continue
    except Exception as e:
        return f"❌ خطا در پردازش جستجو: {e}"
    finally:
        driver.quit()

    if not all_products:
        return "❌ هیچ محصولی یافت نشد."

    sorted_products = sorted(all_products, key=lambda x: x["price"])
    top_products = sorted_products[:3]

    reply = ""
    for i, p in enumerate(top_products, 1):
        reply += (
            f"🔹 *نتیجه {i}*\n"
            f"📦 {p['title']}\n"
            f"🛍️ {p['seller']}\n"
            f"💰 {p['price']:,} تومان\n"
            f"[🔗 لینک محصول]({p['link']})\n\n"
        )

    return reply.strip()

@app.route('/', methods=['POST'])
def telegram_webhook():
    data = request.get_json()
    chat_id = data['message']['chat']['id']
    text = data['message'].get('text', '')

    if text:
        reply = get_product_details(text)
        inline_keyboard = {
            "inline_keyboard": [
                [{"text": "🔍 جستجوی جدید", "switch_inline_query_current_chat": ""}],
                [{"text": "📢 عضویت در کانال", "url": "https://t.me/goldencache"}]
            ]
        }
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={
            "chat_id": chat_id,
            "text": reply,
            "reply_markup": inline_keyboard,
            "parse_mode": "Markdown"
        })
    else:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={
            "chat_id": chat_id,
            "text": "🔎 لطفاً نام محصولی را وارد کنید."
        })

    return '', 200

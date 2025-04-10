# انتخاب پایه image
FROM python:3.9-slim

# نصب Chromium و وابستگی‌های مورد نیاز
RUN apt-get update && apt-get install -y \
    chromium-driver \
    chromium \
    libgdk-pixbuf2.0-0 \
    libx11-xcb1 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libnspr4 \
    libnss3 \
    xdg-utils \
    wget \
    --no-install-recommends

# تنظیم دایرکتوری کاری
WORKDIR /app

# کپی کردن فایل‌ها
COPY . .

# نصب وابستگی‌ها
RUN pip install --no-cache-dir -r requirements.txt

# تنظیم متغیر محیطی برای پورتی که اپلیکیشن گوش می‌دهد
ENV PORT 5000

# اجرای اپلیکیشن با gunicorn
CMD ["gunicorn", "-b", ":$PORT", "main:app"]

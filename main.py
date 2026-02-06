import time
import requests
import smtplib
import os
import yfinance
from bs4 import BeautifulSoup
from email.mime.text import MIMEText

# ===== メール設定（環境変数から取得）=====
GMAIL = os.environ["GMAIL"]
APP_PASS = os.environ["APP_PASS"]
TO_MAIL = os.environ["TO_MAIL"]
RESEND_API_KEY = os.environ["RESEND_API_KEY"]

# ===== Web設定 =====
URL = "https://jp.investing.com/currencies/usd-jpy-technical"
HEADERS = {"User-Agent": "Mozilla/5.0"}

wanted_signals = ["強い買い", "買い", "中立", "売り", "強い売り"]

# ===== 環境設定 =====
CHECK_INTERVAL = os.environ["CHECK_INTERVAL"]
last_summary = None


# ===== 現在価格取得 =====
def get_price():
  ticker = yfinance.Ticker("JPY=X")
  data = ticker.history(period="1d", interval="1m")
  price = f"{data['Close'].iloc[-1]:.2f}"
  return price

# ===== サマリ取得 =====
def get_summary():
    results = {}

    r = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(r.text, "lxml")
    buttons = soup.find_all("button", attrs={"data-test": True})

    for btn in buttons:
        spans = btn.find_all("span")

        if len(spans) >= 2:
            timeframe = spans[0].get_text(strip=True)
            signal = spans[1].get_text(strip=True)
            results[timeframe] = signal

    filtered_results = {k: v for k, v in results.items() if v in wanted_signals}
    return filtered_results

# ===== メール送信 =====
def send_mail(text):
    requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": "onboarding@resend.dev",
            "to": [TO_MAIL],
            "subject": "USDJPYテクニカル変化",
            "text": text,
        },
    )

# ===== メール整形 =====
def format_summary_email(price, last, current):
    lines = []
    lines.append(f"現在価格 : {price}")
    for k, new in current.items():
        old = last.get(k, "新規")
        if old != new:
            lines.append(f"{k}: {old} → {new}")
        else:
            lines.append(f"{k}: {new}")
    return "\n".join(lines)


# ===== 実行 =====
print("監視開始")

while True:
    try:
        price = get_price()
        print("現在価格:", price)
        current = get_summary()
        print("現在:", current)

        if last_summary and current != last_summary:
            email_body = format_summary_email(price, last_summary, current)
            send_mail(email_body)

        last_summary = current

    except Exception as e:
        print("エラー:", e)

    time.sleep(CHECK_INTERVAL)




import ccxt
import pandas as pd
import numpy as np
import time
import requests
import datetime
import threading
from flask import Flask

# --- TELEGRAM SOZLAMALARI ---
BOT_TOKEN = "8561975465:AAGut6mQUfLfTcIOz90eesdhLdQ5iN52pRc"  
CHAT_ID = "6931604709"                        

binance = ccxt.binance()

# Tangalar ro'yxati (Barcha kerakli tangalar)
targets = [
    'BTC/USDT',
    'ETH/USDT',
    'SOL/USDT',
    'XRP/USDT',
    'ADA/USDT',
    'DOGE/USDT',
    'AVAX/USDT',
    'LINK/USDT'
]

TIMEFRAME = '1h'

# Flask veb-server (Render bepul ishlashi uchun shart)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot muvaffaqiyatli ishlayapti!"

def run_web():
    app.run(host='0.0.0.0', port=10000)


def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def send_telegram_message(message):
    """Telegramga xabar yuborish"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Xatolik (Telegram): {e}")

def get_market_analysis_text():
    """Bozorni tahlil qilib, matn qaytaruvchi funksiya"""
    report = f"📊 *Binance Bozor Tahlili* \n🕒 `{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n\n"
    log_data = []

    for symbol in targets:
        try:
            bars = binance.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=100)
            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            current_price = df['close'].iloc[-1]
            df['MA20'] = df['close'].rolling(window=20).mean()
            df['RSI'] = calculate_rsi(df['close'], period=14)
            
            bb_std = df['close'].rolling(window=20).std()
            bb_upper = df['MA20'] + (bb_std * 2)
            bb_lower = df['MA20'] - (bb_std * 2)
            
            ma_20 = df['MA20'].iloc[-1]
            current_rsi = df['RSI'].iloc[-1]
            bb_upper_val = bb_upper.iloc[-1]
            bb_lower_val = bb_lower.iloc[-1]
            
            report += f"🔹 *{symbol}*\n"
            report += f"  • Narx: `{current_price:.2f} USDT`\n"
            report += f"  • RSI: `{current_rsi:.2f}`\n"
            
            signal = "⚪ Aniq yo'nalish yo'q"
            if current_price <= bb_lower_val and current_rsi < 35:
                signal = "🟢 Katta imkoniyat (Oversold)"
                report += f"  • Signal: {signal}\n\n"
            elif current_price >= bb_upper_val and current_rsi > 65:
                signal = "🔴 Ehtiyot bo'ling (Overbought)"
                report += f"  • Signal: {signal}\n\n"
            elif current_price > ma_20 and current_rsi < 60:
                signal = "🔵 Barqaror o'sish (HOLD)"
                report += f"  • Signal: {signal}\n\n"
            else:
                report += f"  • Signal: {signal}\n\n"

            log_data.append(f"{datetime.datetime.now()},{symbol},{current_price},{current_rsi},{signal}")
            
        except Exception as e:
            print(f"Xatolik {symbol}: {e}")

    # Tarixni faylga yozish
    with open("trade_history.csv", "a", encoding="utf-8") as f:
        for line in log_data:
            f.write(line + "\n")

    return report

def background_scheduler():
    """Avtomatik ravishda vaqt oralig'ida xabar yuborib turuvchi funksiya"""
    while True:
        print("Avtomatik tahlil bajarilmoqda...")
        report = get_market_analysis_text()
        send_telegram_message(report)
        time.sleep(360) # 360 soniya (6 daqiqa)

def check_telegram_commands():
    """Telegramdan kelgan buyruqlarni tekshirib turish (/status)"""
    offset = 0
    print("Telegram buyruqlarini tinglash boshlandi...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url).json()
            
            if "result" in response:
                for result in response["result"]:
                    offset = result["update_id"] + 1
                    if "message" in result and "text" in result["message"]:
                        text = result["message"]["text"]
                        chat_id = result["message"]["chat"]["id"]
                        
                        if text == "/status" or text == "/start":
                            reply = "Salom! Siz so'ragan joriy bozor tahlili:\n\n" + get_market_analysis_text()
                            ans_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                            requests.post(ans_url, json={"chat_id": chat_id, "text": reply, "parse_mode": "Markdown"})
        except Exception as e:
            print(f"Buyruqni o'qishda xatolik: {e}")
        time.sleep(2)

if __name__ == "__main__":
    print("Mukammal Kripto Tahlilchi Bot ishga tushdi...")
    
    # 1. Render uchun veb-serverni ishga tushiramiz
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()
    
    # 2. Avtomatik xabar yuborishni ishga tushiramiz
    t = threading.Thread(target=background_scheduler)
    t.daemon = True
    t.start()
    
    # 3. Telegram buyruqlarini tinglaymiz
    check_telegram_commands()

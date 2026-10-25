import time
import requests
import datetime
import threading
import os
from flask import Flask

# --- TELEGRAM SOZLAMALARI ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8561975465:AAGut6mQUfLfTcIOz90eesdhLdQ5iN52pRc")
CHAT_ID = os.environ.get("CHAT_ID", "6931604709")

# CoinGecko uchun tanga ID'lari
coins = {
    'BTC/USDT': 'bitcoin',
    'ETH/USDT': 'ethereum',
    'SOL/USDT': 'solana',
    'XRP/USDT': 'ripple',
    'ADA/USDT': 'cardano',
    'DOGE/USDT': 'dogecoin',
    'AVAX/USDT': 'avalanche-2',
    'LINK/USDT': 'chainlink'
}

# Flask veb-server (Render uchun)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot muvaffaqiyatli ishlayapti va tahlilga tayyor!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def send_telegram_message(message, chat_id=CHAT_ID):
    """Telegramga xabar yuborish"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Xatolik (Telegram): {e}")

def get_market_analysis_text():
    """CoinGecko orqali bozor narxlarini olish va tahlil qilish"""
    report = f"📊 *Kripto Bozor Tahlili* \n🕒 `{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n\n"
    
    try:
        # Barcha tangalar narxini bitta so'rovda olamiz
        ids = ",".join(coins.values())
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"
        response = requests.get(url, timeout=10).json()
        
        for symbol, coin_id in coins.items():
            if coin_id in response:
                price = response[coin_id]['usd']
                change_24h = response[coin_id].get('usd_24h_change', 0)
                
                report += f"🔹 *{symbol}*\n"
                report += f"  • Narx: `{price:,.2f} USDT`\n"
                report += f"  • 24h O'zgarish: `{change_24h:+.2f}%`\n"
                
                signal = "⚪ Barqaror"
                if change_24h > 3:
                    signal = "🟢 Faol o'sishda (Bullish)"
                elif change_24h < -3:
                    signal = "🔴 Pasayishda (Bearish)"
                
                report += f"  • Holat: {signal}\n\n"
            else:
                report += f"🔹 *{symbol}* - Ma'lumot topilmadi\n\n"
                
    except Exception as e:
        print(f"Xatolik (API): {e}")
        report += "❌ Bozor ma'lumotlarini olishda vaqtinchalik xatolik yuz berdi."

    return report

def check_telegram_commands():
    """Telegramdan kelgan buyruqlarni tekshirib turish (/status)"""
    offset = 0
    print("Telegram buyruqlarini tinglash boshlandi...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url, timeout=35).json()
            
            if "result" in response:
                for result in response["result"]:
                    offset = result["update_id"] + 1
                    if "message" in result and "text" in result["message"]:
                        text = result["message"]["text"]
                        chat_id = result["message"]["chat"]["id"]
                        
                        if "/status" in text or "/start" in text:
                            print(f"Buyruq keldi: {text}")
                            reply = "⏳ Ma'lumotlar yuklanmoqda...\n\n" + get_market_analysis_text()
                            send_telegram_message(reply, chat_id)
        except Exception as e:
            print(f"Buyruqni o'qishda xatolik: {e}")
        time.sleep(2)

if __name__ == "__main__":
    print("Kripto Tahlilchi Bot ishga tushdi...")
    
    # 1. Veb-serverni ishga tushiramiz
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()
    
    # 2. Telegram buyruqlarini tinglashni ishga tushiramiz
    t = threading.Thread(target=check_telegram_commands)
    t.daemon = True
    t.start()
    
    while True:
        time.sleep(1)

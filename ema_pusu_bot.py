
# CoinKillers EMA Pusu Botu v1.2
# Sadece 15m grafikte EMA(5) - EMA(137) kesişimlerini kontrol eder.
# Aynı yönlü sinyali tekrar etmez, sadece yön değişiminde yeni sinyal yollar.

import ccxt
import requests
import time
import datetime
import numpy as np

# === AYARLAR ===
coins = ['BTC/USDT', 'ETH/USDT', 'BCH/USDT', 'XRP/USDT', 'LTC/USDT',
         'SOL/USDT', 'BNB/USDT', 'DOGE/USDT', 'ADA/USDT', 'TRX/USDT']

timeframes = ['15m']
ema_fast = 5
ema_slow = 137

telegram_token = '7757452796:AAG76ri7VWT3H-OU6iQiyHdIh2MEMJ5JODw'
telegram_chat_id = '1507759766'

binance_api_key = 'X6HbKkdgQd6xI4Ad70tA60DaF4NKnyZwBhdFn9peno8tfa5UL4xr3iSKKsoP98cr'
binance_secret = 'VHEmngz1WRcGJlwqBoThsGDA0WW6rnrdVnFwud5fXDekhZSzEuffAAWLASqnqwuQ'

# Binance Futures Bağlantısı
exchange = ccxt.binance({
    'apiKey': binance_api_key,
    'secret': binance_secret,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

# Coin bazlı son sinyal takibi
last_signals = {coin: None for coin in coins}

# === FONKSİYONLAR ===
def send_telegram(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {'chat_id': telegram_chat_id, 'text': message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram hatası:", e)

def calculate_ema(values, period):
    weights = np.exp(np.linspace(-1., 0., period))
    weights /= weights.sum()
    a = np.convolve(values, weights, mode='full')[:len(values)]
    a[:period] = a[period]
    return a

def check_cross(coin, tf):
    try:
        ohlcv = exchange.fetch_ohlcv(coin, tf, limit=150)
        closes = [c[4] for c in ohlcv]
        ema_fast_series = calculate_ema(closes, ema_fast)
        ema_slow_series = calculate_ema(closes, ema_slow)

        last_ema_fast = ema_fast_series[-1]
        last_ema_slow = ema_slow_series[-1]
        prev_ema_fast = ema_fast_series[-2]
        prev_ema_slow = ema_slow_series[-2]

        if prev_ema_fast < prev_ema_slow and last_ema_fast > last_ema_slow:
            if last_signals[coin] != 'long':
                msg = f"\n🕒 {tf} | {coin}\n🟢 EMA({ema_fast}) yukarı kesti! LONG Sinyali (Kesişim gerçekleşti)\nEMA({ema_fast}): {last_ema_fast:.2f}\nEMA({ema_slow}): {last_ema_slow:.2f}"
                send_telegram(msg)
                last_signals[coin] = 'long'

        elif prev_ema_fast > prev_ema_slow and last_ema_fast < last_ema_slow:
            if last_signals[coin] != 'short':
                msg = f"\n🕒 {tf} | {coin}\n🔴 EMA({ema_fast}) aşağı kesti! SHORT Sinyali (Kesişim gerçekleşti)\nEMA({ema_fast}): {last_ema_fast:.2f}\nEMA({ema_slow}): {last_ema_slow:.2f}"
                send_telegram(msg)
                last_signals[coin] = 'short'

    except Exception as e:
        print(f"Hata ({coin} - {tf}):", str(e))

# === ANA DÖNGÜ ===
print("CoinKillers EMA Pusu Botu (15M Kesişim Takibi) başlatıldı!")
while True:
    for coin in coins:
        for tf in timeframes:
            check_cross(coin, tf)
            time.sleep(1)  # Binance rate limit'e takılmamak için
    print(f"Taranma tamamlandı: {datetime.datetime.now()}")
    time.sleep(900)  # 15 dakikada bir tekrar tarar

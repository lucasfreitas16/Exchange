import requests
import pandas as pd
from datetime import datetime
import time
import os

# === CONFIGURAÇÕES ===
TAXA_TOTAL = 0.002  # 0.2% (compra + venda + saque)
MARGEM_MINIMA = 30  # lucro mínimo para enviar alerta
LOG_FILE = "log_arbitragem.csv"

# === TELEGRAM ===
TOKEN = "7927424941:AAFOEIfPMM6wu8WZ-m5kwLVFnXgFjZAbOZ4"
CHAT_ID = "6462067199"

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"⚠️ Erro ao enviar mensagem no Telegram: {e}")

# === APIs de preços ===
def get_dolar_cotacao():
    try:
        r = requests.get("https://economia.awesomeapi.com.br/last/USD-BRL", timeout=10)
        r.raise_for_status()
        return float(r.json()['USDBRL']['bid'])
    except Exception as e:
        print(f"❌ Erro ao buscar dólar: {e}")
        return 5.00

def get_binance_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usdt", timeout=10)
        r.raise_for_status()
        return float(r.json()['bitcoin']['usdt'])
    except Exception as e:
        print(f"❌ Erro ao buscar preço no CoinGecko: {e}")
        return None

def get_mb_price():
    try:
        r = requests.get("https://www.mercadobitcoin.net/api/BTC/ticker/", timeout=10)
        r.raise_for_status()
        return float(r.json()['ticker']['buy'])
    except Exception as e:
        print(f"❌ Erro ao buscar preço no Mercado Bitcoin: {e}")
        return None

# === Lógica principal ===
def simular_arbitragem():
    preco_binance_usdt = get_binance_price()
    preco_mb_brl = get_mb_price()
    USDT_BRL = get_dolar_cotacao()

    if preco_binance_usdt is None or preco_mb_brl is None:
        print("❌ Erro ao buscar preços. (alguma das fontes retornou None)")
        return

    preco_binance_brl = preco_binance_usdt * USDT_BRL
    spread = preco_mb_brl - preco_binance_brl
    lucro_liquido = spread - (preco_binance_brl * TAXA_TOTAL)

    data_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{data_hora}]")
    print(f"Câmbio USDT→BRL: R${USDT_BRL:.2f}")
    print(f"Binance (USDT): {preco_binance_usdt:.2f} → R${preco_binance_brl:.2f}")
    print(f"Mercado Bitcoin (BRL): R${preco_mb_brl:.2f}")
    print(f"Spread: R${spread:.2f} | Lucro líquido: R${lucro_liquido:.2f}")

    if lucro_liquido >= MARGEM_MINIMA:
        mensagem = (
            "🚨 *ARBITRAGEM DETECTADA!*\n"
            f"🕒 {data_hora}\n\n"
            f"💰 Lucro líquido: *R${lucro_liquido:.2f}*\n"
            f"🔽 Compra Binance: R${preco_binance_brl:.2f}\n"
            f"🔼 Venda MB: R${preco_mb_brl:.2f}\n"
            f"📊 Spread: R${spread:.2f}\n"
            f"💱 USDT→BRL: R${USDT_BRL:.2f}"
        )
        enviar_telegram(mensagem)

    # Salvar log
    registro = {
        "data": datetime.now(),
        "binance_usdt": preco_binance_usdt,
        "usdt_brl": USDT_BRL,
        "binance_brl": preco_binance_brl,
        "mb_brl": preco_mb_brl,
        "spread": spread,
        "lucro_liquido": lucro_liquido
    }
    df = pd.DataFrame([registro])
    df.to_csv(LOG_FILE, mode='a', index=False, header=not os.path.exists(LOG_FILE))

# === Loop principal ===
if __name__ == "__main__":
    print("📡 Bot de Arbitragem INICIADO com alerta via Telegram.")
    while True:
        simular_arbitragem()
        time.sleep(60)  # checa a cada 60s

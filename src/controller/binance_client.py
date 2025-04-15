import hashlib
import hmac
import logging

import requests

from config import (
    API_KEY,
    API_SECRET,
    BASE_URL,
    LONG_SMA_PERIOD,
    SHORT_SMA_PERIOD,
)
from src.controller.log import log_action, log_error


def get_server_time():
    return requests.get(f"{BASE_URL}/v3/time").json()["serverTime"]


def sign_request(params_dict):
    params = {k: str(v) for k, v in params_dict.items()}
    query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    signature = hmac.new(
        API_SECRET.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return query_string, signature


def get_klines(symbol, interval, limit=500):
    url = f"{BASE_URL}/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    response = requests.get(url, params=params)
    return response.json()


def calculate_smas(data):
    closes = [float(candle[4]) for candle in data]
    if len(closes) < max(SHORT_SMA_PERIOD, LONG_SMA_PERIOD):
        raise ValueError("Dados insuficientes para calcular as médias")
    sma_short = sum(closes[-SHORT_SMA_PERIOD:]) / SHORT_SMA_PERIOD
    sma_long = sum(closes[-LONG_SMA_PERIOD:]) / LONG_SMA_PERIOD
    return sma_short, sma_long


def get_symbol_info(symbol):
    url = f"{BASE_URL}/v3/exchangeInfo"
    params = {"symbol": symbol}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        for s in data["symbols"]:
            if s["symbol"] == symbol:
                return s
    return None


def get_price_filter(symbol):
    symbol_info = get_symbol_info(symbol)
    if symbol_info:
        for filter in symbol_info["filters"]:
            if filter["filterType"] == "PRICE_FILTER":
                return filter
    return None


def get_lot_size_filter(symbol):
    symbol_info = get_symbol_info(symbol)
    if symbol_info:
        for filter in symbol_info["filters"]:
            if filter["filterType"] == "LOT_SIZE":
                return filter
    return None


def round_price_to_tick_size(price, symbol):
    price_filter = get_price_filter(symbol)
    if price_filter:
        tick_size = float(price_filter["tickSize"])
        rounded_price = round(price / tick_size) * tick_size
        # Formatando para o número correto de casas decimais
        tick_decimals = len(str(tick_size).split(".")[-1])
        return float(f"{rounded_price:.{tick_decimals}f}")
    return price


def round_quantity_to_step_size(quantity, symbol):
    lot_size = get_lot_size_filter(symbol)
    if lot_size:
        step_size = float(lot_size["stepSize"])
        min_qty = float(lot_size["minQty"])
        # Garantir que a quantidade não seja menor que o mínimo
        quantity = max(quantity, min_qty)
        rounded_quantity = int(quantity / step_size) * step_size
        return rounded_quantity
    return int(quantity)


def execute_order(
    side,
    quantity,
    price,
    COIN,
    PAIR,
    use_all_balance=False,
):
    print(f"Executando ordem de {side}, quantidade: {quantity:.0f}, preco: {price:.8f}")
    log_action(
        f"EXECUTANDO ORDEM {side}", f"Quantidade: {quantity:.0f}, Preço: {price:.8f}"
    )
    # Se for vender usando todo o saldo disponível
    if side.upper() == "SELL" and use_all_balance:
        # Consulta o saldo atual da moeda
        current_balance = check_balance(COIN)
        if current_balance > 0:
            quantity = current_balance
            print(f"Usando saldo total disponível: {quantity} {COIN}")
        else:
            error_msg = f"Saldo insuficiente de {COIN} para vender"
            print(error_msg)
            log_error(error_msg)
            return False
    # Arredonda a quantidade para o step size correto
    quantity = round_quantity_to_step_size(quantity, PAIR)
    if (quantity * price) < 1.0:
        error_msg = "Valor muito pequeno pra ordem, minimum $1"
        print(error_msg)
        log_error(error_msg)
        return False
    params = {
        "symbol": PAIR,
        "side": side.upper(),
        "type": "MARKET",
        "timestamp": get_server_time(),
    }
    params["quantity"] = f"{quantity:.0f}"
    query_string, signature = sign_request(params)
    url = f"{BASE_URL}/v3/order"
    final_url = f"{url}?{query_string}&signature={signature}"
    headers = {"X-MBX-APIKEY": API_KEY}
    response = requests.post(final_url, headers=headers)
    if response.status_code == 200:
        success_msg = f"Caralho! Ordem executada: {side} {quantity:.0f} {PAIR}"
        print(success_msg)
        log_action("ORDEM EXECUTADA", response.json())
        logging.info(f"Ordem executada: {quantity:.0f} {COIN} @ {price:.8f}")
        return True
    else:
        error_msg = f"Puta que pariu, deu erro: {response.text}"
        print(error_msg)
        try:
            error_data = response.json()
            error_code = error_data.get("code", "Unknown")
            log_error(error_msg, error_code)
        except:
            log_error(error_msg)
        return False


def place_limit_order(side, quantity, price, COIN, PAIR, use_all_balance=False):
    # Se for vender usando todo o saldo disponível
    if side.upper() == "SELL" and use_all_balance:
        current_balance = check_balance(COIN)
        if current_balance > 0:
            quantity = current_balance
            print(f"Ordem limite: usando saldo total disponível: {quantity} {COIN}")
        else:
            error_msg = f"Saldo insuficiente de {COIN} para ordem limite de venda"
            print(error_msg)
            log_error(error_msg)
            return False
    # Arredondar preço e quantidade para os valores permitidos
    price = round_price_to_tick_size(price, PAIR)
    quantity = round_quantity_to_step_size(quantity, PAIR)
    print(
        f"Colocando ordem limite de {side}, quantidade: {quantity:.0f}, preco: {price:.8f}"
    )
    log_action(
        f"COLOCANDO ORDEM LIMITE {side}",
        f"Quantidade: {quantity:.0f}, Preço: {price:.8f}",
    )
    params = {
        "symbol": PAIR,
        "side": side.upper(),
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": f"{quantity:.0f}",
        "price": f"{price:.8f}",
        "timestamp": get_server_time(),
    }
    query_string, signature = sign_request(params)
    url = f"{BASE_URL}/v3/order"
    final_url = f"{url}?{query_string}&signature={signature}"
    headers = {"X-MBX-APIKEY": API_KEY}
    response = requests.post(final_url, headers=headers)
    if response.status_code == 200:
        success_msg = (
            f"Ordem limite colocada: {side} {quantity:.0f} {PAIR} @ {price:.8f}"
        )
        print(success_msg)
        log_action("ORDEM LIMITE COLOCADA", response.json())
        logging.info(
            f"Ordem limite colocada: {side} {quantity:.0f} {COIN} @ {price:.8f}"
        )
        return True
    else:
        error_msg = f"Erro ao colocar ordem limite: {response.text}"
        print(error_msg)
        try:
            error_data = response.json()
            error_code = error_data.get("code", "Unknown")
            log_error(error_msg, error_code)
        except:
            log_error(error_msg)
        return False


def check_balance(asset="USDT"):
    try:
        timestamp = get_server_time()
        url = f"{BASE_URL}/v3/account"
        query_string = f"timestamp={timestamp}"
        signature = hmac.new(
            API_SECRET.encode(), query_string.encode(), hashlib.sha256
        ).hexdigest()
        params = {"timestamp": timestamp, "signature": signature}
        headers = {"X-MBX-APIKEY": API_KEY}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            balances = data["balances"]
            for b in balances:
                if b["asset"] == asset:
                    return float(b["free"])
            return 0.0
        else:
            error_msg = f"Erro ao verificar saldo: {response.text}"
            print(error_msg)
            try:
                error_data = response.json()
                error_code = error_data.get("code", "Unknown")
                log_error(error_msg, error_code)
            except:
                log_error(error_msg)
            return 0.0
    except Exception as e:
        error_msg = f"Erro ao verificar saldo: {str(e)}"
        print(error_msg)
        log_error(error_msg)
        return 0.0


def calculate_rsi(data, period=14):
    closes = [float(candle[4]) for candle in data]
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gain = [delta if delta > 0 else 0 for delta in deltas]
    loss = [-delta if delta < 0 else 0 for delta in deltas]
    avg_gain = sum(gain[:period]) / period
    avg_loss = sum(loss[:period]) / period
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gain[i]) / period
        avg_loss = (avg_loss * (period - 1) + loss[i]) / period
    rs = avg_gain / avg_loss if avg_loss != 0 else 0
    rsi = 100 - (100 / (1 + rs))
    return rsi

import logging
from datetime import datetime

# Inicializa o logging
logging.basicConfig(
    filename="trades.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def log_trade(action, quantity, price, usdt_balance, COIN_balance, coin):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"{timestamp} - {action}: {quantity:.0f} {coin} @ ${price:.8f} | USDT: ${usdt_balance:.2f} | {coin}: {COIN_balance:.0f}"
    logging.info(log_message)
    print(log_message)


def log_error(error_message, error_code=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"{timestamp} - ERRO: {error_message}"
    if error_code:
        log_message += f" | CÓDIGO: {error_code}"
    logging.error(log_message)
    print(log_message)


def log_action(action, details=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"{timestamp} - AÇÃO: {action}"
    if details:
        log_message += f" | DETALHES: {details}"
    logging.info(log_message)
    print(log_message)

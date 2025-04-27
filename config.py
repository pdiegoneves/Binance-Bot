import os

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")


# Configurações globais da estratégia
SHORT_SMA_PERIOD = 9
LONG_SMA_PERIOD = 21
TAXA = 0.001  # 0.1% por operação
LUCRO_MINIMO = 0.01  # 1% de lucro mínimo real
BASE_URL = "https://api.binance.com/api"
PERCENTUAL_A_AVALIAR = 30


PAIRS = [
    {
        "coin": "PEPE",
        "pair": "PEPEUSDT",
        "interval": "1m",
        "value": 1.155,
    },
    {
        "coin": "BONK",
        "pair": "BONKUSDT",
        "interval": "1m",
        "value": 1.15,
    },
    {
        "coin": "TST",
        "pair": "TSTUSDT",
        "interval": "1m",
        "value": 1.15,
    },
    {
        "coin": "SHIB",
        "pair": "SHIBUSDT",
        "interval": "1m",
        "value": 1.15,
    },
    {
        "coin": "ACT",
        "pair": "ACTUSDT",
        "interval": "1m",
        "value": 1.15,
    },
    {
        "coin": "1000CHEEMS",
        "pair": "1000CHEEMSUSDT",
        "interval": "1m",
        "value": 1.15,
    },
    {
        "coin": "1000SATS",
        "pair": "1000SATSUSDT",
        "interval": "1m",
        "value": 1.15,
    },
    {
        "coin": "MUBARAK",
        "pair": "MUBARAKUSDT",
        "interval": "1m",
        "value": 1.15,
    },
    {
        "coin": "BANANAS31",
        "pair": "BANANAS31USDT",
        "interval": "1m",
        "value": 1.15,
    },
]

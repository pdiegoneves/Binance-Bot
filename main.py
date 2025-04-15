import logging
import time

from config import (
    LONG_SMA_PERIOD,
    LUCRO_MINIMO,
    PAIRS,
    PERCENTUAL_A_AVALIAR,
    SHORT_SMA_PERIOD,
    TAXA,
)
from src.controller.binance_client import (
    calculate_rsi,
    calculate_smas,
    check_balance,
    execute_order,
    get_klines,
    get_lot_size_filter,
    get_price_filter,
    get_symbol_info,
    round_price_to_tick_size,
    round_quantity_to_step_size,
)
from src.controller.log import log_action, log_trade

# Configurações da estratégia
# COIN = sys.argv[1]
# PAIR = f"{COIN}USDT"


def main():
    for pair in PAIRS:
        PAIR = (pair["pair"],)
        COIN = (pair["coin"],)
        QUANTIDADE_ENTRADA_USDT = pair["value"]
        CANDLE_TIME = pair["interval"]

        log_action(
            "BOT INICIADO",
            f"Par: {PAIR}, SMA Curta: {SHORT_SMA_PERIOD}, SMA Longa: {LONG_SMA_PERIOD}, Entrada USDT: {QUANTIDADE_ENTRADA_USDT}",
        )
        # Verificar informações do símbolo no início para diagnóstico
        symbol_info = get_symbol_info(PAIR)
        price_filter = get_price_filter(PAIR)
        lot_size = get_lot_size_filter(PAIR)
        if symbol_info and price_filter and lot_size:
            log_action(
                "INFORMAÇÕES DO PAR",
                f"Tick Size: {price_filter['tickSize']}, Step Size: {lot_size['stepSize']}",
            )

        try:
            data = get_klines(PAIR, CANDLE_TIME)
            current_price = float(data[-1][4])
            available_usdt = check_balance("USDT")
            available_COIN = check_balance(COIN)
            sma_short, sma_long = calculate_smas(data)
            rsi = calculate_rsi(data)
            print("\n==============================================")
            print(f"Preço atual: {current_price:.8f}")
            print(f"USDT disponível: {available_usdt:.2f}")
            print(f"{COIN} disponível: {available_COIN:.0f}")
            print(f"RSI: {rsi:.2f}")
            print(f"SMA Curta: {sma_short:.8f}")
            print(f"SMA Longa: {sma_long:.8f}")

            # Calcular a quantidade de moeda que podemos comprar com o USDT definido
            coin_quantity = QUANTIDADE_ENTRADA_USDT / current_price
            coin_quantity = round_quantity_to_step_size(coin_quantity, PAIR)

            # Verificar sinais de compra
            if (
                rsi < PERCENTUAL_A_AVALIAR
                and sma_short > sma_long
                and available_usdt >= QUANTIDADE_ENTRADA_USDT
            ):
                print("🚀 SINAL DE COMPRA DETECTADO! 🚀")
                log_action(
                    "SINAL DE COMPRA",
                    f"RSI: {rsi:.2f}, SMA Curta: {sma_short:.8f}, SMA Longa: {sma_long:.8f}",
                )
                # Usar a quantidade calculada a partir do valor em USDT
                if execute_order("BUY", coin_quantity, current_price, COIN, PAIR):
                    entry_price = current_price
                    # Atualizar saldos após a compra
                    available_COIN = check_balance(COIN)
                    available_usdt = check_balance("USDT")
                    log_trade(
                        "COMPRA",
                        coin_quantity,
                        current_price,
                        available_usdt,
                        available_COIN,
                        coin=COIN,
                    )
                    take_profit_price = round_price_to_tick_size(
                        entry_price * (1 + LUCRO_MINIMO + TAXA), PAIR
                    )
                    print(f"Preço TP: {take_profit_price:.8f}")
                    # Colocar ordem de take profit usando todo o saldo
                    if execute_order(
                        "SELL",
                        available_COIN,
                        take_profit_price,
                        COIN=COIN,
                        PAIR=PAIR,
                        use_all_balance=True,
                    ):
                        print(
                            f"Ordem TP colocada para todo saldo: {available_COIN:.0f} @ {take_profit_price:.8f}"
                        )
                        log_action(
                            "TP APÓS COMPRA",
                            f"Preço: {take_profit_price:.8f}, Quantidade: TODO SALDO",
                        )

            # Log do saldo a cada ciclo
            logging.info(
                f"Saldo atual: USDT: ${available_usdt:.2f} | {COIN}: {available_COIN:.0f}"
            )
            time.sleep(1)
        except Exception as e:
            error_message = f"⚠️ Erro crítico: {e}"
            print(error_message)
            logging.error(error_message)
            time.sleep(30)


if __name__ == "__main__":
    try:
        while True:
            main()
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nPrograma interrompido pelo usuário.")

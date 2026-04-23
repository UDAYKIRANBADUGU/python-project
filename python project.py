import os
import argparse
import logging
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv

load_dotenv()

# Logger setup
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger():
    logger = logging.getLogger("trading_bot")
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(f"{LOG_DIR}/app.log")
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )
    file_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(file_handler)

    return logger

logger = setup_logger()

# Binance Client
class BinanceClient:
    def __init__(self):
        self.client = Client(
            os.getenv("BINANCE_API_KEY"),
            os.getenv("BINANCE_API_SECRET")
        )
        self.client.FUTURES_URL = os.getenv("BASE_URL")

    def get_client(self):
        return self.client

# Order Validators
def validate_order(symbol, side, order_type, quantity, price):
    side = side.upper()
    order_type = order_type.upper()

    if side not in ["BUY", "SELL"]:
        raise ValueError("Side must be BUY or SELL")

    if order_type not in ["MARKET", "LIMIT"]:
        raise ValueError("Order type must be MARKET or LIMIT")

    if quantity <= 0:
        raise ValueError("Quantity must be positive")

    if order_type == "LIMIT" and price is None:
        raise ValueError("Price is required for LIMIT orders")

    return symbol.upper(), side, order_type

# Order placement
def place_order(client, symbol, side, order_type, quantity, price=None):
    try:
        logger.info(f"Placing order: {symbol} {side} {order_type} qty={quantity} price={price}")

        if order_type == "MARKET":
            response = client.futures_create_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=quantity
            )
        else:
            response = client.futures_create_order(
                symbol=symbol,
                side=side,
                type="LIMIT",
                quantity=quantity,
                price=price,
                timeInForce="GTC"
            )

        logger.info(f"Response: {response}")
        return response
    
    except BinanceAPIException as e:
        logger.error(f"API Error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        raise

# Main
def main():
    parser = argparse.ArgumentParser(description="Binance Futures Testnet Trading Bot")

    parser.add_argument("--symbol", required=True)
    parser.add_argument("--side", required=True)
    parser.add_argument("--type", required=True)
    parser.add_argument("--quantity", type=float, required=True)
    parser.add_argument("--price", type=float)

    args = parser.parse_args()

    try:
        symbol, side, order_type = validate_order(
            args.symbol, args.side, args.type, args.quantity, args.price
        )

        print("\n📌 Order Summary")
        print(f"Symbol: {symbol}")
        print(f"Side: {side}")
        print(f"Type: {order_type}")
        print(f"Quantity: {args.quantity}")
        print(f"Price: {args.price}\n")

        client = BinanceClient().get_client()

        response = place_order(
            client,
            symbol,
            side,
            order_type,
            args.quantity,
            args.price
        )

        print("✅ Order Successful")
        print(f"Order ID: {response.get('orderId')}")
        print(f"Status: {response.get('status')}")
        print(f"Executed Qty: {response.get('executedQty')}")
        print(f"Avg Price: {response.get('avgPrice', 'N/A')}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
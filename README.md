# Binance Order-Book

Minimal Python project allowing one to run a Binance order-book locally. This project simply follows the Binance API recommendations that you can find [here](https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams#how-to-manage-a-local-order-book-correctly).

The primary goal of this project is to collect order-book data that could be used for financial modelling projects. The data is collected while the program is running, and is written as JSON on interrupt (Ctrl-C).

*Note that the highest frequency at which Binance allows us to update the status is 100ms, which might not be suitable for HFT.*

**Usage Examples:**
***
For simply displaying the order book in your terminal (as in the screenshot):
```
python main.py --interval=1s --symbols=SOLUSDT --display=yes --writedata=no --depth=8
```
***
For collecting order-book data every 100 milliseconds for 3 different symbols:
```
python3 main.py --interval=100ms --writedata=yes --symbols=ETHUSDT,BTCUSDT,SOLUSDT 
```
import sys
from binanceob import BinanceOrderbook
from multiprocessing import Process

if __name__ == '__main__': 
    symbols = ['ETHUSDT', 'BTCUSDT', 'SOLUSDT']
    interval = '100ms'

    processes = []
    for symbol in symbols:
        process = Process(target=BinanceOrderbook(symbol=symbol, display_depth=8, interval=interval).start)
        processes.append(process)
        process.start()

    try: [process.join() for process in processes]
    except KeyboardInterrupt: print('STOPPED')
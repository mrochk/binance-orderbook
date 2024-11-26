from binance import Client, ThreadedWebsocketManager
from binance.exceptions import BinanceAPIException
from time import sleep
import json
import os

from ..orderbook import Orderbook
from ..event import Event
from ..util import *

class BinanceOrderbook(object):
    symbol        : str
    interval      : str
    display_depth : int
    buffer        : list[dict]
    orderbook     : Orderbook
    twm           : ThreadedWebsocketManager
    data          : dict

    def __init__(self, symbol='BTCUSDT', display_depth=10, interval='1s'):
        self.symbol = symbol if symbol is not None else BASE_SYMBOL
        self.interval = interval
        self.display_depth = display_depth
        self.buffer = list()
        self.orderbook = None
        self.twm = ThreadedWebsocketManager() 
        self.data = {'symbol': self.symbol, 'ob': []}

    def start(self):
        def callback(msg): 
            """wrapper around `__callback` to include `u`"""
            nonlocal u 
            self.__callback(u, msg)

        u = None

        self.twm.start()

        # start websocket stream
        try: socket_name = self.__open_depth_stream(callback, self.interval)
        except Exception as e: 
            print_error(f'when trying to start depth stream: {e}')
            self.__exit_error()

        # get orderbook snapshot to sync
        try: snapshot = self.__get_snapshot()
        except BinanceAPIException as e: 
            print_error(f'while getting snapshot: {e}')
            self.__exit_error()

        last_update_id = snapshot['lastUpdateId']
        self.orderbook = Orderbook(snapshot)
        self.__wait_first_event(last_update_id)
        self.__prune_buffer(last_update_id)

        try: self.__loop()
        except KeyboardInterrupt: self.__end(socket_name)

    def __end(self, socket_name):
        print(f'\nshutting down...')
        self.__stop_stream(socket_name); self.__stop_twm()
        print('orderbook stopped successfully')

        try: os.mkdir('data') 
        except: pass

        out = f'data/{self.symbol}.json'
        with open(out, 'w') as f: f.write(self.to_json())
        print(f'wrote data in {out} successfully')

    def __callback(self, u, msg):
        # sanity check
        if u is not None: assert msg['U'] == u+1
        u = msg['u']
        # append message
        self.buffer.append(msg)
        # log
        n_asks, n_bids = len(msg['a']), len(msg['b'])
        print(f'<{self.symbol}> event received ({n_bids} bids, {n_asks} asks)')

    def to_json(self): return json.dumps(self.data)

    def __wait_first_event(self, luid):
        while True:
            for event in self.buffer:
                if self.__is_first_event(luid, event): return
            sleep(2)

    def __loop(self):
        while True:
            if not self.buffer: continue
            msg = self.buffer.pop(0)
            event = Event(msg)
            self.orderbook.update(event)
            #print()
            #self.orderbook.display(self.display_depth) 
            self.data['ob'].append(self.orderbook.as_dict())

    def __get_snapshot(self, limit=1000):
        return Client().get_order_book(symbol=self.symbol, limit=limit)

    def __open_depth_stream(self, callback, interval='1s'):
        assert interval == '1s' or interval == '100ms', \
            'interval must be equal to \'1s\' or \'100ms\''

        interval = None if interval == '1s' else 100

        print(f'attempting to start wss depth stream for symbol <{self.symbol}>...')
        socket_name = self.twm.start_depth_socket(callback, self.symbol, interval=interval)
        sleep(1)
        print(f'depth stream ({socket_name}) started successfully for symbol <{self.symbol}>')
        return socket_name

    @staticmethod
    def __is_first_event(last_update_id, event):
        U, u = event['U'], event['u']
        return U <= last_update_id+1 and last_update_id+1 <= u

    def __prune_buffer(self, last_update_id):
        before = len(self.buffer)
        while not self.__is_first_event(last_update_id, self.buffer[0]): self.buffer.pop(0)
        print(f'<prune buffer> removed {before - len(self.buffer)} events')
        sleep(1)

    def __stop_stream(self, stream_name):
        try:
            self.twm.stop_socket(stream_name)
            sleep(0.5)
            print(f'stream <{stream_name}> stopped successfully')
        except: print_error('when trying to stop wss stream')

    def __stop_twm(self):
        try:  self.twm.stop(); sleep(0.1); print(f'twm stopped successfully')
        except: print_error('when trying to stop twm')

    def __exit_error(self): self.twm.stop(); exit(1)
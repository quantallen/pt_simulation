import asyncio
import json
import time
import logging
import sys
import socket
#import websockets
from math import floor
from module.pricer import Pricer
from module.predictor import Predictor
from datetime import timedelta, datetime
from module.log_format import SaveLog

logger = logging.getLogger(__name__)

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class Spreader:
    testnet_endpoint = f'wss://testws.btse.io/ws/spot'
    production_endpoint = f'wss://aws-ws.btse.com/ws/spot'
    staging_endpoint = f'wss://ws.oa.btse.io/ws/spot'

    orderbook = {}
    orderbook_5min = {}
    trades = {}
    
    def __init__(self, BTSE, config,Ref,Target,start,end):
        logging.getLogger('').handlers = []
        self.btse = BTSE
        self.config = config
        self.log = SaveLog("Allen","PairTrading",f"PairTrading{Ref}{Target}_add_pos0_{int(self.config.TEST_SECOND/60)}min_{self.config.OPEN_THRESHOLD}_{self.config.STOP_LOSS_THRESHOLD}",f"./{start}_{end}_{Ref}{Target}_Trading_log/")
        self.predictor = Predictor(
            window_size=self.config.MA_WINDOW_SIZE,
            ref_symbol=config.REFERENCE_SYMBOL,
            target_symbol=config.TARGET_SYMBOL,
            slippage= self.config.SLIPPAGE,
            log = self.log
        )
        self.pricer = Pricer(
            BTSE,
            config.REFERENCE_SYMBOL,
            config.TARGET_SYMBOL,
            self.log
        )
        self.spread_prices = None
        self.remember_quotos = None


    
    def local_simulate(self, timestamp, symbol, asks, bids):
        
        if symbol not in self.orderbook_5min or timestamp - self.orderbook_5min[symbol]['timestamp'] >= timedelta(seconds=self.config.TEST_SECOND):
            # self.orderbook_5min[symbol] = {
            #     'buyQuote': [{'price': [bids[0][0],bids[1][0],bids[2][0]], 'size':[bids[0][1],bids[1][1],bids[2][1]]}],
            #     'sellQuote': [{'price': [asks[0][0],asks[1][0],asks[2][0]], 'size':[asks[0][1],asks[1][1],asks[2][1]]}],
            #     'timestamp': timestamp
            # }
            
            self.orderbook_5min[symbol] = {
                'buyQuote': [{'price': [bids], 'size':[bids]}],
                'sellQuote': [{'price': [asks], 'size':[asks]}],
                'timestamp': timestamp
            }
            self.predictor.update_spreads(self.orderbook_5min)
        self.orderbook[symbol] = {
                    'buyQuote': [{'price': [bids], 'size':[bids]}],
                    'sellQuote': [{'price': [asks], 'size':[asks]}],
                    'timestamp': timestamp
                }
        #print(self.orderbook[symbol]['buyQuote'][0]['price'],self.orderbook[symbol]['buyQuote'][0]['size'])
        #print(self.orderbook[symbol]['sellQuote'][0]['price'],self.orderbook[symbol]['sellQuote'][0]['size'])

        self.spread_prices = self.predictor.get_target_spread_price(
                orderbook=self.orderbook,
                orderbook_5min= self.orderbook_5min,
                open_threshold=self.config.OPEN_THRESHOLD,
                stop_loss_threshold=self.config.STOP_LOSS_THRESHOLD,
            )
        
        # unlike live trading, we can not submit order to cross market,
        # only orders that match current iteration's symbol are valid.
        valid_orders = []
        # print(self.pricer.active_orders)
        if self.pricer.active_orders:
            for id in self.pricer.active_orders:
                if self.pricer.active_orders[id].symbol == symbol:
                    valid_orders.append(self.pricer.active_orders[id])

        return {
            'orders': valid_orders,
        
        }
        
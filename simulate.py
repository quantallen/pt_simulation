import sys
import os
import os,sys
import pandas as pd 
import datetime
from datetime import timedelta, datetime
from dateutil import parser
import math

#設定當前工作目錄，放再import其他路徑模組之前
os.chdir(sys.path[0])
#sys.path.append('./simulator')
sys.path.append('./module')

def main(Ref,Target,open_threshold,stop_loss_threshold,test_second):
    from module.spreader import Spreader
    from config import Pair_Trading_Config
    config = Pair_Trading_Config(Ref,Target,open_threshold,stop_loss_threshold,test_second)
    path = f"/home/allen.kuo/0404_1114_{Ref}{Target}_orderbook/"
    isExist = os.path.exists(path)

    if not isExist:    
        # Create a new directory because it does not exist 
        os.makedirs(path)
        print("The new directory is created!")
    spreader = Spreader(None, config,Ref,Target)

    BNB_list,BTC_list = [],[]
    start, end , period = '2022-04-04','2022-11-14',5
    sets_count = math.floor((pd.to_datetime(end)+ pd.Timedelta("1d") -pd.to_datetime(start))/pd.Timedelta(str(period)+"d"))
    start_day = pd.to_datetime(start)
    for set in range(sets_count):
            day_range = tuple(pd.date_range(start=start_day,periods=period).strftime("%Y%m%d"))
            day_begin = day_range[0][-4:]
            day_end = day_range[-1][-4:]
            start_day = start_day + pd.Timedelta(str(period)+"d")
            BNB_list.append(f'/data/order/{day_begin}_{day_end}_{Ref}_USDT_order.pkl')
            BTC_list.append(f'/data/order/{day_begin}_{day_end}_{Target}_USDT_order.pkl')
    # for i in range(3,9):
    #     BNB_list.append(f'/data/order/{i}_{Target}_USDT_PERP_order.pkl')
    BNB = pd.read_pickle(BNB_list[0])
    for E in BNB_list[1:] :
        df = pd.read_pickle(E)
        print(df)
        df = df.sort_values(by="binance_orderbook.collectedtimestamp")
        BNB = pd.concat([BNB, df], ignore_index=True)
    BNB = BNB.sort_values(by="binance_orderbook.collectedtimestamp")
    BNB = BNB.loc[:, ~BNB.columns.str.contains('^Unnamed')]
    BNB = BNB.reset_index(drop=True)
    print(BNB)
    BTC = pd.read_pickle(BTC_list[0])
    for B in BTC_list[1:] :
        df = pd.read_pickle(B)
        df = df.sort_values(by="binance_orderbook.collectedtimestamp")
        BTC = pd.concat([BTC, df], ignore_index=True)
    BTC = BTC.sort_values(by="binance_orderbook.collectedtimestamp")
    BTC = BTC.loc[:, ~BTC.columns.str.contains('^Unnamed')]
    BTC = BTC.reset_index(drop=True)
    print(BTC)

    i = j = 0
    B_time,B_symbol,B_asks,B_bids,E_time,E_symbol,E_asks,E_bids = BTC['binance_orderbook.collectedtimestamp'],BTC['binance_orderbook.symbol'],BTC['binance_orderbook.asks'],BTC['binance_orderbook.bids'],BNB['binance_orderbook.collectedtimestamp'],BNB['binance_orderbook.symbol'],BNB['binance_orderbook.asks'],BNB['binance_orderbook.bids']
    while i < len(B_time) and j < len(E_time):
        if parser.parse(B_time[i]) - parser.parse(E_time[j]) >= timedelta(milliseconds= 25) :
            #print(parser.parse(B_time[i]) - parser.parse(E_time[j]))
            j += 1
            continue
        elif parser.parse(E_time[j]) - parser.parse(B_time[i]) >= timedelta(milliseconds= 25) :
            #print(parser.parse(E_time[j]) - parser.parse(B_time[i]))
            i += 1
            continue
        else :
            #print(parser.parse(B_time[i]), parser.parse(E_time[j]) )
            spreader.local_simulate(parser.parse(B_time[i]),B_symbol[i],eval(B_asks[i]),eval(B_bids[i]))
            spreader.local_simulate(parser.parse(E_time[j]),E_symbol[j],eval(E_asks[j]),eval(E_bids[j]))
            i += 1
            j += 1


if __name__ == '__main__':

    main(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])

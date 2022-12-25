import sys
import os
import os, sys
import pandas as pd
from datetime import timedelta, datetime
from dateutil import parser
import math
from module.spreader import Spreader
from datetime import date as dt_date

from config import Pair_Trading_Config

# 設定當前工作目錄，放再import其他路徑模組之前
os.chdir(sys.path[0])
# sys.path.append('./simulator')
sys.path.append("./module")


def date_range(x, y, inclusive=False):
    x, y = datetime.strptime(x, "%Y-%m-%d"), datetime.strptime(y, "%Y-%m-%d")
    inclusive_nr = 1 if inclusive else 0

    if isinstance(x, dt_date) and isinstance(y, dt_date):

        for i in range(x.toordinal(), y.toordinal() + inclusive_nr):
            yield dt_date.fromordinal(i)

    else:
        raise TypeError("Parameters x and y should be dates.")


def main(Ref, Target, open_threshold, stop_loss_threshold, test_second):
    start, end = "2022-01-01", "2022-12-13"
    mydates = [str(d) for d in date_range(start, end, inclusive=True)]
    config = Pair_Trading_Config(
        Ref, Target, open_threshold, stop_loss_threshold, test_second
    )
    path = f"./{start}_{end}_{Ref}{Target}_Trading_log/"
    isExist = os.path.exists(path)
    if not isExist:
        # Create a new directory because it does not exist
        os.makedirs(path)
        print("The new directory is created!")
    spreader = Spreader(None, config, Ref, Target, start, end)
    Ref_path = f"./{Ref}_process_trades/"
    dirs = os.listdir(Ref_path)
    # Ref_dataframe = pd.read_csv(Ref_path + dirs[0])
    Ref_dataframe = pd.read_csv(Ref_path + f"{Ref}_{mydates[0]}.csv")
    Ref_dataframe.rename(columns={"Unnamed: 0": "timestamp"}, inplace=True)
    # for file in dirs:
    for d in mydates[1:]:
        # df = pd.read_csv(Ref_path + "/" + file)
        df = pd.read_csv(Ref_path + f"{Ref}_{d}.csv")
        df.rename(columns={"Unnamed: 0": "timestamp"}, inplace=True)
        Ref_dataframe = pd.concat([Ref_dataframe, df], ignore_index=True)
    Ref_list, Target_list = [], []
    print(Ref_dataframe)
    Target_path = f"./{Target}_process_trades/"
    dirs = os.listdir(Target_path)
    print(dirs)
    # Target_dataframe = pd.read_csv(Target_path + dirs[0])
    Target_dataframe = pd.read_csv(Target_path + f"{Target}_{mydates[0]}.csv")
    Target_dataframe.rename(columns={"Unnamed: 0": "timestamp"}, inplace=True)
    # for file in dirs:
    for d in mydates[1:]:
        df = pd.read_csv(Target_path + f"{Target}_{d}.csv")
        df.rename(columns={"Unnamed: 0": "timestamp"}, inplace=True)
        Target_dataframe = pd.concat([Target_dataframe, df], ignore_index=True)
    Ref_list, Target_list = [], []
    print(Target_dataframe)
    R_time, R_price, T_time, T_price = (
        Ref_dataframe["timestamp"],
        Ref_dataframe["price"],
        Target_dataframe["timestamp"],
        Target_dataframe["price"],
    )
    i, j = 0, 0
    while i < len(R_time) and j < len(T_time):
        r_t = datetime.strptime(R_time[i], "%Y-%m-%d %H:%M:%S")
        t_t = datetime.strptime(T_time[i], "%Y-%m-%d %H:%M:%S")
        spreader.local_simulate(r_t, Ref, R_price[i], R_price[i])
        spreader.local_simulate(t_t, Target, T_price[j], T_price[j])
        i += 1
        j += 1


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])

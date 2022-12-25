from datetime import datetime, timedelta
from datetime import date as dt_date
import pandas as pd
from zipfile import ZipFile
import os


def date_range(x, y, inclusive=False):
    x, y = datetime.strptime(x, "%Y-%m-%d"), datetime.strptime(y, "%Y-%m-%d")
    inclusive_nr = 1 if inclusive else 0

    if isinstance(x, dt_date) and isinstance(y, dt_date):

        for i in range(x.toordinal(), y.toordinal() + inclusive_nr):
            yield dt_date.fromordinal(i)

    else:
        raise TypeError("Parameters x and y should be dates.")


def extract_file(zip_file_path, crypto):
    zf = ZipFile(zip_file_path, "r")
    path = f"./{crypto}_trades/"
    isExist = os.path.exists(path)
    if not isExist:
        # Create a new directory because it does not exist
        os.makedirs(path)
        print("The new directory is created!")
    zf.extractall(path)


def processing_data(file_path, crypto, date):
    path = f"./{crypto}_process_trades/"
    isExist = os.path.exists(path)
    if not isExist:
        # Create a new directory because it does not exist
        os.makedirs(path)
        print("The new directory is created!")
    filename = "./BTCUSDT_trades/BTCUSDT-trades-2020-01-01.csv"
    print(type(datetime.strptime(date, "%Y-%m-%d")))
    # if datetime.strptime(date, "%Y-%m-%d").date() < dt_date.fromisoformat("2021-07-13"):
    trades_columns = ["id", "price", "qty", "quote_qty", "time", "is_buyer_maker"]
    df_ = pd.read_csv(file_path, header=None, names=trades_columns)
    if (df_.iloc[0].tolist()) == trades_columns:
        df_ = pd.read_csv(file_path)

    # start_str = filename.split(".")[0][-10:]
    start_date = datetime.strptime(date, "%Y-%m-%d")
    end_date = start_date + timedelta(days=1)

    for idx, time in enumerate(df_["time"]):
        df_["time"].loc[idx] = datetime.utcfromtimestamp(int(time / 1000))
    del df_["id"]
    del df_["quote_qty"]
    del df_["is_buyer_maker"]
    aggregation_functions = {"price": "mean", "qty": "mean"}
    df_ = df_.groupby(df_["time"]).aggregate(aggregation_functions)
    dates = pd.date_range(start=start_date, end=end_date, freq="s")
    df_ = df_.reindex(dates[:-1])
    df_ = df_.fillna(method="ffill")
    df_ = df_.fillna(method="bfill")
    df_.to_csv(path + f"{crypto}_{date}.csv")
    return df_


if __name__ == "__main__":
    crypto_list = ["BTCUSDT"]  # ["BTCUSDT", "AVAXUSDT"]
    start_date = "2022-11-01"
    end_date = "2022-12-13"
    mydates = [str(d) for d in date_range(start_date, end_date, inclusive=True)]
    print(mydates)
    for crypto in crypto_list:
        for dates in mydates:
            stored_data_path = f"/mnt/d/Allen/binance-public-data-master/python/data/futures/um/daily/trades/{crypto}/2020-01-01_2022-12-13/{crypto}-trades-{dates}.zip"
            extract_file(stored_data_path, crypto)
            processing_path = f"./{crypto}_trades/{crypto}-trades-{dates}.csv"
            processing_data(processing_path, crypto, dates)
    # extract_file()
    # processing_data()

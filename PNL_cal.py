from datetime import datetime
import pandas as pd
import time
import os
import glob
import numpy as np
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib as mpl
from matplotlib.ticker import MultipleLocator, FuncFormatter
import matplotlib.pyplot as plt
import sys

draw_pic = True
record_return = False


class Strategy:
    def __init__(self, id, min, open_sigma, stop_loss_sigma, REF, TARGET):
        self.id = id
        self.min = min
        self.day = dict()
        self.open_sigma = open_sigma
        self.stop_loss_sigma = stop_loss_sigma
        self.ref_symbol = REF
        self.target_symbol = TARGET
        self.array = []
        self.ref = {
            "buy_ps": 0,
            "sell_ps": 0,
            "buy_avg": 0,
            "sell_avg": 0,
            "buy_size": 0,
            "sell_size": 0,
            "realize_pnl": 0,
            "unrealize_pnl": 0,
        }
        self.target = {
            "buy_ps": 0,
            "sell_ps": 0,
            "buy_avg": 0,
            "sell_avg": 0,
            "buy_size": 0,
            "sell_size": 0,
            "realize_pnl": 0,
            "unrealize_pnl": 0,
        }

        self.buy_ps = 0
        self.sell_ps = 0
        self.buy_avg = 0
        self.sell_avg = 0
        self.buy_size = 0
        self.sell_size = 0
        self.realize_pnl = 0
        self.unrealize_pnl = 0

        self.count = 0
        self.pos_count = 0
        self.pos_list = [0, 0, 0, 0, 0]
        self.pnl_list = [0, 0, 0, 0, 0]
        self.winloss_list = [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0]]
        self.unit_profit = 0
        self.winner = 0
        self.loser = 0
        self.dif_time = []
        self.opentime = None
        self.closetime = None

    def calculate_PnL1(self, symbol, side, price, size):
        if symbol == self.ref_symbol:
            if side == "BUY":
                if self.ref["sell_size"] == 0:
                    self.ref["buy_ps"] += price * size
                    self.ref["buy_size"] += size
                    self.ref["buy_avg"] = self.ref["buy_ps"] / self.ref["buy_size"]
                    self.ref["unrealize_pnl"] = (
                        price - self.ref["buy_avg"]
                    ) * self.ref["buy_size"]
                else:
                    if size < self.ref["sell_size"]:
                        self.ref["realize_pnl"] += size * (self.ref["sell_avg"] - price)
                        self.ref["sell_size"] -= size
                        self.ref["sell_ps"] -= self.ref["sell_avg"] * size
                        self.ref["unrealize_pnl"] = (
                            self.ref["sell_avg"] - price
                        ) * self.ref["sell_size"]
                    elif size == self.ref["sell_size"]:
                        self.ref["realize_pnl"] += self.ref["sell_size"] * (
                            self.ref["sell_avg"] - price
                        )
                        self.ref["sell_size"] = self.ref["sell_ps"] = self.ref[
                            "sell_avg"
                        ] = 0
                        self.ref["unrealize_pnl"] = 0
                    else:
                        self.ref["realize_pnl"] += self.ref["sell_size"] * (
                            self.ref["sell_avg"] - price
                        )
                        self.ref["buy_size"] = size - self.ref["sell_size"]
                        self.ref["buy_ps"] += price * self.ref["buy_size"]
                        self.ref["buy_avg"] = self.ref["buy_ps"] / self.ref["buy_size"]
                        self.ref["sell_size"] = self.ref["sell_ps"] = self.ref[
                            "sell_avg"
                        ] = 0
                        self.ref["unrealize_pnl"] = (
                            price - self.ref["buy_avg"]
                        ) * self.ref["buy_size"]
            else:
                if self.ref["buy_size"] == 0:
                    self.ref["sell_ps"] += price * size
                    self.ref["sell_size"] += size
                    self.ref["sell_avg"] = self.ref["sell_ps"] / self.ref["sell_size"]
                    self.ref["unrealize_pnl"] = (
                        self.ref["sell_avg"] - price
                    ) * self.ref["sell_size"]
                else:
                    if size < self.ref["buy_size"]:
                        self.ref["realize_pnl"] += size * (price - self.ref["buy_avg"])
                        self.ref["buy_size"] -= size
                        self.ref["buy_ps"] -= self.ref["buy_avg"] * size
                        self.ref["unrealize_pnl"] = (
                            price - self.ref["buy_avg"]
                        ) * self.ref["buy_size"]
                    elif size == self.ref["buy_size"]:
                        self.ref["realize_pnl"] += self.ref["buy_size"] * (
                            price - self.ref["buy_avg"]
                        )
                        self.ref["buy_size"] = self.ref["buy_ps"] = self.ref[
                            "buy_avg"
                        ] = 0
                        self.ref["unrealize_pnl"] = 0
                    else:
                        self.ref["realize_pnl"] += self.ref["buy_size"] * (
                            price - self.ref["buy_avg"]
                        )
                        self.ref["sell_size"] = size - self.ref["buy_size"]
                        self.ref["sell_ps"] += price * self.ref["sell_size"]
                        self.ref["sell_avg"] = (
                            self.ref["sell_ps"] / self.ref["sell_size"]
                        )
                        self.ref["buy_size"] = self.ref["buy_ps"] = self.ref[
                            "buy_avg"
                        ] = 0
                        self.ref["unrealize_pnl"] = (
                            self.ref["sell_avg"] - price
                        ) * self.ref["sell_size"]
        if symbol == self.target_symbol:
            if side == "BUY":
                if self.target["sell_size"] == 0:
                    self.target["buy_ps"] += price * size
                    self.target["buy_size"] += size
                    self.target["buy_avg"] = (
                        self.target["buy_ps"] / self.target["buy_size"]
                    )
                    self.target["unrealize_pnl"] = (
                        price - self.target["buy_avg"]
                    ) * self.target["buy_size"]
                else:
                    if size < self.target["sell_size"]:
                        self.target["realize_pnl"] += size * (
                            self.target["sell_avg"] - price
                        )
                        self.target["sell_size"] -= size
                        self.target["sell_ps"] -= self.target["sell_avg"] * size
                        self.target["unrealize_pnl"] = (
                            self.target["sell_avg"] - price
                        ) * self.target["sell_size"]
                    elif size == self.target["sell_size"]:
                        self.target["realize_pnl"] += self.target["sell_size"] * (
                            self.target["sell_avg"] - price
                        )
                        self.target["sell_size"] = self.target["sell_ps"] = self.target[
                            "sell_avg"
                        ] = 0
                        self.target["unrealize_pnl"] = 0
                    else:
                        self.target["realize_pnl"] += self.target["sell_size"] * (
                            self.target["sell_avg"] - price
                        )
                        self.target["buy_size"] = size - self.target["sell_size"]
                        self.target["buy_ps"] += price * self.target["buy_size"]
                        self.target["buy_avg"] = (
                            self.target["buy_ps"] / self.target["buy_size"]
                        )
                        self.target["sell_size"] = self.target["sell_ps"] = self.target[
                            "sell_avg"
                        ] = 0
                        self.target["unrealize_pnl"] = (
                            price - self.target["buy_avg"]
                        ) * self.target["buy_size"]
            else:
                if self.target["buy_size"] == 0:
                    self.target["sell_ps"] += price * size
                    self.target["sell_size"] += size
                    self.target["sell_avg"] = (
                        self.target["sell_ps"] / self.target["sell_size"]
                    )
                    self.target["unrealize_pnl"] = (
                        self.target["sell_avg"] - price
                    ) * self.target["sell_size"]
                else:
                    if size < self.target["buy_size"]:
                        self.target["realize_pnl"] += size * (
                            price - self.target["buy_avg"]
                        )
                        self.target["buy_size"] -= size
                        self.target["buy_ps"] -= self.target["buy_avg"] * size
                        self.target["unrealize_pnl"] = (
                            price - self.target["buy_avg"]
                        ) * self.target["buy_size"]
                    elif size == self.target["buy_size"]:
                        self.target["realize_pnl"] += self.target["buy_size"] * (
                            price - self.target["buy_avg"]
                        )
                        self.target["buy_size"] = self.target["buy_ps"] = self.target[
                            "buy_avg"
                        ] = 0
                        self.target["unrealize_pnl"] = 0
                    else:
                        self.target["realize_pnl"] += self.target["buy_size"] * (
                            price - self.target["buy_avg"]
                        )
                        self.target["sell_size"] = size - self.target["buy_size"]
                        self.target["sell_ps"] += price * self.target["sell_size"]
                        self.target["sell_avg"] = (
                            self.target["sell_ps"] / self.target["sell_size"]
                        )
                        self.target["buy_size"] = self.target["buy_ps"] = self.target[
                            "buy_avg"
                        ] = 0
                        self.target["unrealize_pnl"] = (
                            self.target["sell_avg"] - price
                        ) * self.target["sell_size"]

    def read_new_log(self, file_str):
        f = open(file_str)
        for i, line in enumerate(f.readlines()):
            dic = json.loads(line)
            self.calculate_PnL1(
                dic["msg"]["symbol"],
                str(dic["msg"]["side"]),
                float(dic["msg"]["price"]),
                float(dic["msg"]["size"]),
            )
            if (
                self.ref["buy_size"] == 0
                and self.ref["sell_size"] == 0
                and self.target["buy_size"] == 0
                and self.target["sell_size"] == 0
            ):

                # if (i+1) % 4 == 0:
                self.count += 1
                self.pos_list[self.pos_count - 1] += 1
                print(self.ref["realize_pnl"] + self.target["realize_pnl"])
                self.array.append(
                    (self.ref["realize_pnl"] + self.target["realize_pnl"]) / 2000
                )
                d = dic["msg"]["time"]
                date_time_obj = datetime.strptime(d, "%Y-%m-%d %H:%M:%S")
                self.closetime = date_time_obj
                if date_time_obj.strftime("%Y%m%d") not in self.day:
                    self.day[date_time_obj.strftime("%Y%m%d")] = (
                        self.ref["realize_pnl"] + self.target["realize_pnl"]
                    )
                else:
                    self.day[date_time_obj.strftime("%Y%m%d")] += (
                        self.ref["realize_pnl"] + self.target["realize_pnl"]
                    )
                self.pnl_list[self.pos_count - 1] += (
                    self.ref["realize_pnl"] + self.target["realize_pnl"]
                )
                if self.ref["realize_pnl"] + self.target["realize_pnl"] > 0:
                    self.winloss_list[self.pos_count - 1][0] += 1
                    self.winner += 1
                if self.ref["realize_pnl"] + self.target["realize_pnl"] < 0:
                    self.winloss_list[self.pos_count - 1][1] += 1
                    self.loser += 1
                self.unit_profit += self.ref["realize_pnl"] + self.target["realize_pnl"]
                self.ref["realize_pnl"] = self.target["realize_pnl"] = 0
                self.pos_count = 0
                # self.dif_time.append(self.closetime - self.opentime)
            # elif (i + 1) % 2 == 0:
            #     d = dic["msg"]["time"]
            #     date_time_obj = datetime.strptime(d, "%Y-%m-%d %H:%M:%S")
            #     self.opentime = date_time_obj
            #     self.pos_count += 1

    # def read_log(self, file_str):
    #     f = open(file_str)
    #     for i,line in enumerate(f.readlines()):
    #         dic = json.loads(line)
    #         #print(dic)
    #         self.calculate_PnL1(dic['msg']['symbol'] ,str(dic['msg']['side']),float(dic['msg']['price']), float(dic['msg']['size']))
    #         if self.target["buy_size"] == 0 and self.target["sell_size"] == 0 :
    #             self.count += 1
    #             self.pos_list[self.pos_count-1] += 1
    #             print(self.ref["realize_pnl"]+self.target["realize_pnl"])
    #             self.array.append((self.ref["realize_pnl"]+self.target["realize_pnl"])/2000)
    #             if self.ref["realize_pnl"]+self.target["realize_pnl"] > 0 :
    #                 self.winner += 1

    #             if self.ref["realize_pnl"]+self.target["realize_pnl"] < 0 :
    #                 self.loser += 1

    #             self.pnl_list[self.pos_count-1] += self.ref["realize_pnl"]+self.target["realize_pnl"]
    #             if self.ref["realize_pnl"]+self.target["realize_pnl"] > 0 :
    #                 self.winloss_list[self.pos_count-1][0] += 1
    #             if self.ref["realize_pnl"]+self.target["realize_pnl"] < 0 :
    #                 self.winloss_list[self.pos_count-1][1] += 1
    #             self.unit_profit += self.ref["realize_pnl"]+self.target["realize_pnl"]
    #             self.ref["realize_pnl"] = self.target["realize_pnl"] = 0

    #             self.pos_count = 0
    #         else :
    #             self.pos_count += 1
    #     f.close()
    def connect_to_local(self, fileExt):
        self.read_new_log(fileExt)

    def return_dataframe(self):
        return [
            self.min,
            self.open_sigma,
            self.stop_loss_sigma,
            sum(self.pos_list),
            sum(self.pnl_list),
            sum(self.pnl_list) / sum(self.pos_list),
            sum(self.pnl_list) / 60,
            "",
            self.winner,
            self.loser,
            np.mean(self.array) / np.std(self.array) * np.sqrt(365),
        ]

    def time_hold(self):
        for t in self.dif_time:
            totsec = t.total_seconds()
            h = totsec // 3600
            m = (totsec % 3600) // 60
            print("%d:%d" % (h, m))

    def return_daily_return(self):
        df = [[k, v] for k, v in self.day.items()]
        return df

    def return_dataframe_addpos(self):
        print(self.pos_list)
        print(self.pnl_list)
        print(sum(self.pnl_list))
        print(self.winner, self.loser)
        print(self.winloss_list)
        print("profit per day", sum(self.pnl_list) / 60)
        print("profit per trade:", sum(self.pnl_list) / sum(self.pos_list))
        return [
            self.min,
            self.open_sigma,
            sum(self.pos_list),
            sum(self.pnl_list),
            sum(self.pnl_list) / sum(self.pos_list),
            sum(self.pnl_list) / 60,
            "",
            self.winner,
            self.loser,
            self.pos_list[0],
            self.pnl_list[0],
            str(self.winloss_list[0][0]) + "/" + str(self.winloss_list[0][1]),
            self.pos_list[1] * 2,
            self.pnl_list[1],
            str(self.winloss_list[1][0]) + "/" + str(self.winloss_list[1][1]),
            self.pos_list[2] * 3,
            self.pnl_list[2],
            str(self.winloss_list[2][0]) + "/" + str(self.winloss_list[2][1]),
            self.pos_list[3] * 4,
            self.pnl_list[3],
            str(self.winloss_list[3][0]) + "/" + str(self.winloss_list[3][1]),
            self.pos_list[4] * 5,
            self.pnl_list[4],
            str(self.winloss_list[4][0]) + "/" + str(self.winloss_list[4][1]),
        ]

    def plot_performance_with_dd(self):
        capital = 2000
        profit_file = f"./PIC_BT/"
        if not os.path.exists(profit_file):
            os.makedirs(profit_file)
        picture_title = f"Pairs trading with CryptoCurrency_{REF}_{TARGET}_2"
        d_r = self.return_daily_return()
        dates = [k for k, _ in self.day.items()]
        ans = [v for _, v in self.day.items()]
        total_with_capital = [v / capital for _, v in self.day.items()]
        total = np.cumsum(ans)
        reverse_total = [i for i in total[::-1]]
        mdd = calculate_mdd(reverse_total)
        win_rate = self.winner / (self.winner + self.loser)
        dd = list()
        tt = total[0]
        r = pd.DataFrame(total_with_capital)
        r_neg = [i for i in total_with_capital if i < 0]
        r_neg = pd.DataFrame(r_neg)
        sharp_ratio = r.mean() / r.std() * np.sqrt(len(dates))
        sortino_ratio = r.mean() / r_neg.std() * np.sqrt(len(dates))
        for i in range(len(ans)):
            if i > 0 and total[i] > total[i - 1]:
                tt = total[i]
            dd.append(total[i] - tt)
        print(dd)
        # xs = [datetime.datetime.strptime(d, '%Y-%m-%d').date() for d in dates]
        highest_x = []
        highest_dt = []
        for i in range(len(total)):
            if total[i] == max(total[: i + 1]) and total[i] > 0:
                highest_x.append(total[i])
                highest_dt.append(i)
        mpl.style.use("seaborn")
        color_list = list(map(color_change, [r > 0 for r in total_with_capital]))
        f, axarr = plt.subplots(
            3, sharex=True, figsize=(20, 12), gridspec_kw={"height_ratios": [3, 1, 1]}
        )
        axarr[0].plot(np.arange(len(dates)), total, color="b", zorder=1)
        axarr[0].scatter(
            highest_dt, highest_x, color="lime", marker="o", s=40, zorder=2
        )
        axarr[0].set_title(picture_title, fontsize=20)
        axarr[1].bar(np.arange(len(dates)), dd, color="red")
        axarr[2].bar(np.arange(len(dates)), total_with_capital, color=color_list)
        date_tickers = dates

        def format_date(x, pos=None):
            if x < 0 or x > len(date_tickers) - 1:
                return ""
            return date_tickers[int(x)]

        axarr[0].xaxis.set_major_locator(MultipleLocator(80))
        axarr[0].xaxis.set_major_formatter(FuncFormatter(format_date))
        axarr[0].grid(True)
        shift = (max(total) - min(total)) / 20
        text_loc = max(total) - shift
        axarr[0].text(
            np.arange(len(dates))[5],
            text_loc,
            "Total open number : %d" % (self.winner + self.loser),
            fontsize=15,
        )
        axarr[0].text(
            np.arange(len(dates))[5],
            text_loc - shift,
            "Total profit : %.2f" % total[-1],
            fontsize=15,
        )
        axarr[0].text(
            np.arange(len(dates))[5],
            text_loc - shift * 2,
            "Win rate : %.2f " % (win_rate),
            fontsize=15,
        )
        axarr[0].text(
            np.arange(len(dates))[5],
            text_loc - shift * 4,
            "sharpe ratio : %.4f" % (sharp_ratio),
            fontsize=15,
        )
        axarr[0].text(
            np.arange(len(dates))[5],
            text_loc - shift * 5,
            "sortino ratio : %.4f" % (sortino_ratio),
            fontsize=15,
        )
        axarr[0].text(
            np.arange(len(dates))[5],
            text_loc - shift * 3,
            "Max drawdown : %.4f" % (mdd / capital),
            fontsize=15,
        )
        plt.tight_layout()
        plt.savefig(profit_file + picture_title)
        plt.show()
        plt.close()


def color_change(n):
    if n:
        return "g"
    else:
        return "r"


def calculate_mdd(cum_reward):
    mdd = 0
    low = -cum_reward[0]
    for r in cum_reward[1:]:
        mdd = max(mdd, low + r)
        low = max(low, -r)
    return mdd


def apply_to_excel(REF, TARGET, FILENAME, START_DATE, END_DATE):
    # scope = [
    #     "https://spreadsheets.google.com/feeds",
    #     "https://www.googleapis.com/auth/drive",
    # ]
    # credentials = ServiceAccountCredentials.from_json_keyfile_name(
    #     f"{os.path.abspath(os.getcwd())}/gridsearch.json", scope
    # )
    # client = gspread.authorize(credentials)
    # sheet = client.open_by_key("1i8ON5lICvbISdQmAVo4K7vjmTMagKJVxxwgA4Mv9rpo")
    # worksheet = sheet.worksheets()
    # check_list = [t.title for t in worksheet]
    # if f"{START_DATE}-{END_DATE} {FILENAME} pair_trading_simulation" in check_list:
    #     w_id = sheet.worksheet(
    #         f"{START_DATE}-{END_DATE} {FILENAME} pair_trading_simulation"
    #     ).id
    #     reqs = [{"deleteSheet": {"sheetId": w_id}}]
    #     sheet.batch_update({"requests": reqs})
    # sheet.add_worksheet(
    #     title=f"{START_DATE}-{END_DATE} {FILENAME} pair_trading_simulation",
    #     rows=500,
    #     cols=30,
    # )
    # worksheet = sheet.worksheet(
    #     f"{START_DATE}-{END_DATE} {FILENAME} pair_trading_simulation"
    # )
    # dataTitle = [
    #     "MIN",
    #     "open_sigma",
    #     "stop loss sigma",
    #     "total trade",
    #     "total profit",
    #     "profit per trade",
    #     "profit per day",
    #     "",
    #     "win",
    #     "loss",
    #     "Annual Sharpe",
    # ]
    # worksheet.append_row(dataTitle, table_range="A1")
    files = sorted(
        glob.glob(f"./{START_DATE}_{END_DATE}_{FILENAME}_Trading_log/*_add_pos0_*.log"),
        key=os.path.getctime,
    )
    # files = sorted(glob.glob(f'./{START_DATE}_{END_DATE}_{FILENAME}_orderbook/*_add_pos0_20min_1.5_20.0_Allen_20220817.log'),key = os.path.getctime)
    print(files)
    for data in files:
        file_name = data.split("/")[2].split("_")
        print(file_name)
        s = Strategy("Allen", file_name[-5], file_name[-4], file_name[-3], REF, TARGET)
        s.connect_to_local(data)
        _append_list = s.return_dataframe()
        # worksheet.append_row(_append_list, table_range="A1")
        if draw_pic:
            s.plot_performance_with_dd()
    if record_return:
        # worksheet.append_row(["date", "return(%)", "capital"], table_range="A1")
        list_of_df = s.return_daily_return()
        print(list_of_df)
        for df in list_of_df:
            df[1] = df[1] / 20
            df.append(2000)
            # worksheet.append_row(df, table_range="A1")
        s.time_hold()


if __name__ == "__main__":
    REF, TARGET, START_DATE, END_DATE = (
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        sys.argv[4],
    )
    # REF ,TARGET = 'BTC_USDT','AVAX_USDT'
    FILENAME = REF + TARGET
    print(FILENAME)
    apply_to_excel(REF, TARGET, FILENAME, START_DATE, END_DATE)

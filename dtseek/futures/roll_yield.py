# -*- coding:utf-8 -*-
# /usr/bin/env python
"""
Author: Tong Du
date: 2020/09/07 16:58
contact: dtshare@126.com
desc: 获取各合约展期收益率, 日线数据从 daily_bar 函数获取
"""
import datetime
import re
import warnings

import matplotlib.dates as mdate
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters

from dtseek.futures import cons
from dtseek.futures.daily_bar import get_futures_daily
from dtseek.futures.symbol_var import symbol_market, symbol_varieties

register_matplotlib_converters()
calendar = cons.get_calendar()


def _plot_bar(temp_df) -> None:
    fig = plt.figure(1, dpi=300)
    ax = fig.add_subplot(111)
    ax.bar(range(len(temp_df.index)), temp_df, color="green")
    ax.set_xticks(range(len(temp_df.index)))
    ax.set_xticklabels(temp_df.index, fontsize=4)
    plt.show()


def _plot_bar_2(temp_df) -> None:
    fig = plt.figure(1, dpi=300)
    ax = fig.add_subplot(111)
    ax.bar(range(len(temp_df.symbol)), temp_df.close, color="green")
    ax.set_xticks(range(len(temp_df.symbol)))
    ax.set_xticklabels(temp_df.symbol, fontsize=6)
    plt.show()


def _plot(plot_df):
    fig = plt.figure(1, dpi=300)
    ax = fig.add_subplot(111)
    ax.xaxis.set_major_formatter(mdate.DateFormatter("%Y-%m-%d"))  # 设置时间标签显示格式
    plt.xticks(pd.to_datetime(plot_df.index), rotation=90)
    plt.plot(plot_df, label="roll_yield")
    ax.legend()
    plt.show()


def get_roll_yield_bar(
    type_method="symbol", var="RB", date=None, start_day=None, end_day=None, plot=False
):
    """
    获取展期收益率
    :param type_method: 'symbol'：获取指定交易日指定品种所有交割月合约的收盘价, 'var'：获取某天所有品种两个主力合约的展期收益率（展期收益率横截面）, 'date'：获取某品种每天的两个主力合约的展期收益率（展期收益率时间序列）
    :param var: 合约品种如 RB、AL 等
    :param date: 指定交易日 format： YYYYMMDD
    :param start_day: 开始日期 format：YYYYMMDD
    :param end_day: 结束日期 format：YYYYMMDD
    :param plot: True or False作图
    :return: pandas.DataFrame
    展期收益率数据(DataFrame)
        ry      展期收益率
        index   日期或品种
    """

    date = cons.convert_date(date) if date is not None else datetime.date.today()
    start_day = (
        cons.convert_date(start_day) if start_day is not None else datetime.date.today()
    )
    end_day = (
        cons.convert_date(end_day)
        if end_day is not None
        else cons.convert_date(cons.get_latest_data_date(datetime.datetime.now()))
    )

    if type_method == "symbol":
        df = get_futures_daily(start_day=date, end_day=date, market=symbol_market(var))
        df = df[df["variety"] == var]
        if plot:
            _plot_bar_2(df[["symbol", "close"]])
        return df

    if type_method == "var":
        df = pd.DataFrame()
        for market in ["dce", "cffex", "shfe", "czce"]:
            df = df.append(
                get_futures_daily(start_day=date, end_day=date, market=market)
            )
        var_list = list(set(df["variety"]))
        df_l = pd.DataFrame()
        for var in var_list:
            ry = get_roll_yield(date, var, df=df)
            if ry:
                df_l = df_l.append(
                    pd.DataFrame(
                        [ry], index=[var], columns=["roll_yield", "near_by", "deferred"]
                    )
                )
        df_l["date"] = date
        df_l = df_l.sort_values("roll_yield")
        if plot:
            _plot_bar(df_l["roll_yield"])
        return df_l

    if type_method == "date":
        df_l = pd.DataFrame()
        while start_day <= end_day:
            try:
                ry = get_roll_yield(start_day, var)
                if ry:
                    df_l = df_l.append(
                        pd.DataFrame(
                            [ry],
                            index=[start_day],
                            columns=["roll_yield", "near_by", "deferred"],
                        )
                    )
            except:
                pass
            start_day += datetime.timedelta(days=1)
        if plot:
            _plot(df_l["roll_yield"])
        return df_l


def get_roll_yield(date=None, var="CU", symbol1=None, symbol2=None, df=None):
    """
    指定交易日指定品种（主力和次主力）或任意两个合约的展期收益率
    Parameters
    ------
    date: string 某一天日期 format： YYYYMMDD
    var: string 合约品种如RB、AL等
    symbol1: string 合约 1如 rb1810
    symbol2: string 合约 2 如 rb1812
    df: DataFrame或None 从dailyBar得到合约价格，如果为空就在函数内部抓dailyBar，直接喂给数据可以让计算加快
    Return
    -------
        tuple
        roll_yield
        near_by
        deferred
    """
    # date = "20200304"
    date = cons.convert_date(date) if date is not None else datetime.date.today()
    if date.strftime("%Y%m%d") not in calendar:
        warnings.warn("%s非交易日" % date.strftime("%Y%m%d"))
        return None
    if symbol1:
        var = symbol_varieties(symbol1)
    if not isinstance(df, pd.DataFrame):
        market = symbol_market(var)
        df = get_futures_daily(start_day=date, end_day=date, market=market)
    if var:
        df = df[~df["symbol"].str.contains("efp")]  # 20200304 由于交易所获取的数据中会有比如 "CUefp"，所以在这里过滤
        df = df[df["variety"] == var].sort_values("open_interest", ascending=False)
        df["close"] = df["close"].astype("float")
        symbol1 = df["symbol"].tolist()[0]
        symbol2 = df["symbol"].tolist()[1]

    close1 = df["close"][df["symbol"] == symbol1.upper()].tolist()[0]
    close2 = df["close"][df["symbol"] == symbol2.upper()].tolist()[0]

    a = re.sub(r"\D", "", symbol1)
    a_1 = int(a[:-2])
    a_2 = int(a[-2:])
    b = re.sub(r"\D", "", symbol2)
    b_1 = int(b[:-2])
    b_2 = int(b[-2:])
    c = (a_1 - b_1) * 12 + (a_2 - b_2)
    if close1 == 0 or close2 == 0:
        return False
    if c > 0:
        return np.log(close2 / close1) / c * 12, symbol2, symbol1
    else:
        return np.log(close2 / close1) / c * 12, symbol1, symbol2


if __name__ == "__main__":
    get_roll_yield_bar_df = get_roll_yield_bar(
        type_method="var", date="20200304", plot=True
    )
    print(get_roll_yield_bar_df)
    get_roll_yield_bar_range_df = get_roll_yield_bar(
        type_method="date",
        var="CF",
        start_day="20191210",
        end_day="20200305",
        plot=True,
    )
    print(get_roll_yield_bar_range_df)
    get_roll_yield_bar_symbol = get_roll_yield_bar(
        type_method="symbol", var="RB", date="20191009", plot=True
    )
    print(get_roll_yield_bar_symbol)

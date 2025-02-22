# -*- coding:utf-8 -*-
# /usr/bin/env python
"""
Author: Tong Du
date: 2019/11/4 16:36
contact: dtshare@126.com
desc: 获取金十数据-其他-加密货币实时行情
"""
import json
import time

import pandas as pd
import requests

from dtseek.economic.cons import bitcoin_url, bitcoin_payload, bitcoin_headers


def get_js_dc_current():
    """
    主流数字货币的实时行情数据, 一次请求返回具体某一时刻行情数据
    https://datacenter.jin10.com/reportType/dc_bitcoin_current
    :return: pandas.DataFrame
    """
    bit_payload = bitcoin_payload.copy()
    bit_payload.update({"_": int(time.time() * 1000)})
    bit_payload.update(
        {
            "_": int(time.time() * 1000)
        }
    )
    r = requests.get(bitcoin_url, params=bit_payload, headers=bitcoin_headers)
    data_json = r.json()
    data_df = pd.DataFrame(data_json["data"])
    data_df.set_index("reported_at", drop=True, inplace=True)
    data_df.index = pd.to_datetime(data_df.index)
    return data_df


def macro_fx_sentiment(start_date="2020-02-07", end_date="2020-02-07"):
    """
    金十数据-外汇-投机情绪报告
    外汇投机情绪报告显示当前市场多空仓位比例，数据由8家交易平台提供，涵盖11个主要货币对和1个黄金品种。
    报告内容: 品种: 澳元兑日元、澳元兑美元、欧元兑美元、欧元兑澳元、欧元兑日元、英镑兑美元、英镑兑日元、纽元兑美元、美元兑加元、美元兑瑞郎、美元兑日元以及现货黄金兑美元。
             数据: 由Shark - fx整合全球8家交易平台（ 包括Oanda、 FXCM、 Insta、 Dukas、 MyFxBook以及FiboGroup） 的多空投机仓位数据而成。
    名词释义: 外汇投机情绪报告显示当前市场多空仓位比例，数据由8家交易平台提供，涵盖11个主要货币对和1个黄金品种。
    工具使用策略: Shark-fx声明表示，基于“主流通常都是错误的”的事实，当空头头寸超过60%，交易者就应该建立多头仓位； 同理，当市场多头头寸超过60%，交易者则应该建立空头仓位。此外，当多空仓位比例接近50%的情况下，我们则倾向于建议交易者不要进场，保持观望。
    https://datacenter.jin10.com/reportType/dc_ssi_trends
    :param start_date: 具体交易日
    :type start_date: str
    :param end_date: 具体交易日, 与 end_date 相同
    :type end_date: str
    :return: 投机情绪报告
    :rtype: pandas.DataFrame
    """
    url = "https://datacenter-api.jin10.com/sentiment/datas"
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "currency_pair": "",
        "_": int(time.time() * 1000),
    }
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "cache-control": "no-cache",
        "origin": "https://datacenter.jin10.com",
        "pragma": "no-cache",
        "referer": "https://datacenter.jin10.com/reportType/dc_ssi_trends",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36",
        "x-app-id": "rU6QIu7JHe2gOUeR",
        "x-csrf-token": "",
        "x-version": "1.0.0",
    }
    res = requests.get(url, params=params, headers=headers)
    return pd.DataFrame(res.json()["data"]["values"])


if __name__ == "__main__":
    get_js_dc_current_df = get_js_dc_current()
    print(get_js_dc_current_df)
    macro_fx_sentiment_df = macro_fx_sentiment(start_date="2020-02-07", end_date="2020-02-07")
    print(macro_fx_sentiment_df)

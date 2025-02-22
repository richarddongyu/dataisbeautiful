# -*- coding:utf-8 -*-
# /usr/bin/env python
"""
Author: Tong Du
Data:2019/10/27 18:02
contact: dtshare@126.com
desc: 东方财富网-数据中心-特色数据-商誉
东方财富网-数据中心-特色数据-商誉-A股商誉市场概况: http://data.eastmoney.com/sy/scgk.html
东方财富网-数据中心-特色数据-商誉-商誉减值预期明细: http://data.eastmoney.com/sy/yqlist.html
东方财富网-数据中心-特色数据-商誉-个股商誉减值明细: http://data.eastmoney.com/sy/jzlist.html
东方财富网-数据中心-特色数据-商誉-个股商誉明细: http://data.eastmoney.com/sy/list.html
东方财富网-数据中心-特色数据-商誉-行业商誉: http://data.eastmoney.com/sy/hylist.html
"""
import requests
import demjson3 as demjson
import pandas as pd
import execjs
from dtseek.stock_feature.cons import stock_em_sy_js

ctx = execjs.compile(stock_em_sy_js)  # 执行 js 渲染


# pd.set_option('display.max_columns', 500)
# pd.set_option('display.max_rows', 500)


def stock_em_sy_profile():
    """
    东方财富网-数据中心-特色数据-商誉-A股商誉市场概况
    http://data.eastmoney.com/sy/scgk.html
    :return: pandas.DataFrame
    """
    url = "http://data.eastmoney.com/sy/scgk.html"
    res = requests.get(url)
    res.encoding = "gb2312"
    data_text = res.text
    data_json = demjson.decode(
        data_text[data_text.find("={") + 1 : data_text.find("]};") + 2]
    )
    data_df = pd.DataFrame(data_json["scgk"])
    data_df.columns = [
        "商誉",
        "商誉减值",
        "MKT",
        "净资产",
        "商誉占净资产比例(%)",
        "商誉减值占净资产比例(%)",
        "报告期",
        "净利润规模(元)",
        "商誉减值占净利润比例(%)",
        "SygmType",
        "SyztType",
    ]
    data_df = data_df[
        [
            "商誉",
            "商誉减值",
            "净资产",
            "商誉占净资产比例(%)",
            "商誉减值占净资产比例(%)",
            "报告期",
            "净利润规模(元)",
            "商誉减值占净利润比例(%)",
        ]
    ]
    data_df["报告期"] = pd.to_datetime(data_df["报告期"])
    return data_df


def _get_page_num_sy_yq_list(symbol="沪深两市", trade_date="2019-12-31"):
    """
    东方财富网-数据中心-特色数据-商誉-商誉减值预期明细
    http://data.eastmoney.com/sy/yqlist.html
    :return: int 获取 商誉减值预期明细 的总页数
    """
    symbol_dict = {
        "沪市主板": f"(MKT='shzb' and ENDDATE=^{trade_date}^)",
        "深市主板": f"(MKT='szzb' and ENDDATE=^{trade_date}^)",
        "中小板": f"(MKT='zxb' and ENDDATE=^{trade_date}^)",
        "创业板": f"(MKT='cyb' and ENDDATE=^{trade_date}^)",
        "沪深两市": f"(ENDDATE=^{trade_date}^)",
    }
    url = "http://dcfm.eastmoney.com/EM_MutiSvcExpandInterface/api/js/get"
    params = {
        "type": "SY_YG",
        "token": "894050c76af8597a853f5b408b759f5d",
        "st": "NOTICEDATE",
        "sr": "-1",
        "p": "1",
        "ps": "50",
        "js": "var {name}=".format(name=ctx.call("getCode", 8))
        + "{pages:(tp),data:(x),font:(font)}",
        "filter": symbol_dict[symbol],
        "rt": "52589731",
    }
    res = requests.get(url, params=params)
    data_json = demjson.decode(res.text[res.text.find("={") + 1 :])
    return data_json["pages"]


def stock_em_sy_yq_list(symbol="沪市主板", trade_date="2018-12-31"):
    """
    东方财富网-数据中心-特色数据-商誉-商誉减值预期明细
    http://data.eastmoney.com/sy/yqlist.html
    :return: pandas.DataFrame
    """
    symbol_dict = {
        "沪市主板": f"(MKT='shzb' and ENDDATE=^{trade_date}^)",
        "深市主板": f"(MKT='szzb' and ENDDATE=^{trade_date}^)",
        "中小板": f"(MKT='zxb' and ENDDATE=^{trade_date}^)",
        "创业板": f"(MKT='cyb' and ENDDATE=^{trade_date}^)",
        "沪深两市": f"(ENDDATE=^{trade_date}^)",
    }
    url = "http://dcfm.eastmoney.com/EM_MutiSvcExpandInterface/api/js/get"
    page_num = _get_page_num_sy_yq_list(symbol=symbol, trade_date=trade_date)
    temp_df = pd.DataFrame()
    for page in range(1, page_num + 1):
        print(f"一共{page_num}页, 正在下载第{page}页")
        params = {
            "type": "SY_YG",
            "token": "894050c76af8597a853f5b408b759f5d",
            "st": "NOTICEDATE",
            "sr": "-1",
            "p": str(page),
            "ps": "50",
            "js": "var {name}=".format(name=ctx.call("getCode", 8))
            + "{pages:(tp),data:(x),font:(font)}",
            "filter": symbol_dict[symbol],
            "rt": "52589731",
        }
        res = requests.get(url, params=params)
        data_text = res.text
        data_json = demjson.decode(data_text[data_text.find("={") + 1 :])
        temp_df = temp_df.append(pd.DataFrame(data_json["data"]), ignore_index=True)
    temp_df.columns = [
        "股票代码",
        "COMPANYCODE",
        "公司名称",
        "MKT",
        "最新一期商誉(元)",
        "公告日期",
        "REPORTDATE",
        "ENDDATE",
        "PARENTNETPROFIT",
        "预计净利润(元)-下限",
        "预计净利润(元)-上限",
        "业绩变动幅度-上限",
        "业绩变动幅度-下限",
        "预告内容",
        "业绩变动原因",
        "FORECASTTYPE",
        "上年度同期净利润(元)",
        "FORECASTINDEXCODE",
        "PERIOD",
        "HYName",
        "HYCode",
        "上年商誉",
    ]
    temp_df = temp_df[
        [
            "股票代码",
            "公司名称",
            "最新一期商誉(元)",
            "公告日期",
            "预计净利润(元)-下限",
            "预计净利润(元)-上限",
            "业绩变动幅度-上限",
            "业绩变动幅度-下限",
            "预告内容",
            "业绩变动原因",
            "上年度同期净利润(元)",
            "上年商誉",
        ]
    ]
    temp_df["公告日期"] = pd.to_datetime(temp_df["公告日期"])
    return temp_df


def _get_page_num_sy_jz_list(symbol="沪市主板", trade_date="2019-06-30"):
    """
    东方财富网-数据中心-特色数据-商誉-个股商誉减值明细
    http://data.eastmoney.com/sy/jzlist.html
    :return: int 获取 个股商誉减值明细 的总页数
    """
    symbol_dict = {
        "沪市主板": f"(MKT='shzb' and REPORTDATE=^{trade_date}^)",
        "深市主板": f"(MKT='szzb' and REPORTDATE=^{trade_date}^)",
        "中小板": f"(MKT='zxb' and REPORTDATE=^{trade_date}^)",
        "创业板": f"(MKT='cyb' and REPORTDATE=^{trade_date}^)",
        "沪深两市": f"(REPORTDATE=^{trade_date}^)",
    }
    url = "http://dcfm.eastmoney.com/EM_MutiSvcExpandInterface/api/js/get"
    params = {
        "type": "SY_MX",
        "token": "894050c76af8597a853f5b408b759f5d",
        "st": "GOODWILL_Change",
        "sr": "-1",
        "p": "2",
        "ps": "50",
        "js": "var {name}=".format(name=ctx.call("getCode", 8))
        + "{pages:(tp),data:(x),font:(font)}",
        "filter": symbol_dict[symbol],
        "rt": "52584576",
    }
    res = requests.get(url, params=params)
    data_json = demjson.decode(res.text[res.text.find("={") + 1 :])
    return data_json["pages"]


def stock_em_sy_jz_list(symbol="沪市主板", trade_date="2019-06-30"):
    """
    东方财富网-数据中心-特色数据-商誉-个股商誉减值明细
    http://data.eastmoney.com/sy/jzlist.html
    :return: pandas.DataFrame
    """
    symbol_dict = {
        "沪市主板": f"(MKT='shzb' and REPORTDATE=^{trade_date}^)",
        "深市主板": f"(MKT='szzb' and REPORTDATE=^{trade_date}^)",
        "中小板": f"(MKT='zxb' and REPORTDATE=^{trade_date}^)",
        "创业板": f"(MKT='cyb' and REPORTDATE=^{trade_date}^)",
        "沪深两市": f"(REPORTDATE=^{trade_date}^)",
    }
    url = "http://dcfm.eastmoney.com/EM_MutiSvcExpandInterface/api/js/get"
    page_num = _get_page_num_sy_jz_list(symbol=symbol, trade_date=trade_date)
    temp_df = pd.DataFrame()
    for page in range(1, page_num + 1):
        print(f"一共{page_num}页, 正在下载第{page}页")
        params = {
            "type": "SY_MX",
            "token": "894050c76af8597a853f5b408b759f5d",
            "st": "GOODWILL_Change",
            "sr": "-1",
            "p": str(page),
            "ps": "50",
            "js": "var {name}=".format(name=ctx.call("getCode", 8))
            + "{pages:(tp),data:(x),font:(font)}",
            "filter": symbol_dict[symbol],
            "rt": "52584576",
        }
        res = requests.get(url, params=params)
        data_text = res.text
        data_json = demjson.decode(data_text[data_text.find("={") + 1 :])
        temp_df = temp_df.append(pd.DataFrame(data_json["data"]), ignore_index=True)
    temp_df.columns = [
        "股票代码",
        "COMPANYCODE",
        "股票简称",
        "MKT",
        "REPORTTIMETYPECODE",
        "COMBINETYPECODE",
        "DATAAJUSTTYPE",
        "商誉(元)",
        "商誉减值(元)",
        "SUMSHEQUITY",
        "SUMSHEQUITY_Rate",
        "商誉减值占净资产比例(%)",
        "NOTICEDATE",
        "REPORTDATE",
        "净利润(元)",
        "商誉减值占净利润比例(%)",
        "HYName",
        "HYCode",
        "SJLTZ",
        "GOODWILL_BeforeYear",
        "公告日期",
        "ListingState",
        "MX_Type",
    ]
    temp_df = temp_df[
        [
            "股票代码",
            "股票简称",
            "商誉(元)",
            "商誉减值(元)",
            "商誉减值占净资产比例(%)",
            "净利润(元)",
            "商誉减值占净利润比例(%)",
            "公告日期",
        ]
    ]
    temp_df["公告日期"] = pd.to_datetime(temp_df["公告日期"])
    return temp_df


def _get_page_num_sy_list(symbol="沪市主板", trade_date="2019-09-30"):
    """
    东方财富网-数据中心-特色数据-商誉-个股商誉明细
    http://data.eastmoney.com/sy/list.html
    :return: int 获取 个股商誉明细 的总页数
    """
    symbol_dict = {
        "沪市主板": f"(MKT='shzb' and REPORTDATE=^{trade_date}^)",
        "深市主板": f"(MKT='szzb' and REPORTDATE=^{trade_date}^)",
        "中小板": f"(MKT='zxb' and REPORTDATE=^{trade_date}^)",
        "创业板": f"(MKT='cyb' and REPORTDATE=^{trade_date}^)",
        "沪深两市": f"(REPORTDATE=^{trade_date}^)",
    }
    url = "http://dcfm.eastmoney.com/EM_MutiSvcExpandInterface/api/js/get"
    params = {
        "type": "SY_MX",
        "token": "894050c76af8597a853f5b408b759f5d",
        "st": "NOTICEDATE",
        "sr": "-1",
        "p": "1",
        "ps": "50",
        "js": "var {name}=".format(name=ctx.call("getCode", 8))
        + "{pages:(tp),data:(x),font:(font)}",
        "filter": symbol_dict[symbol],
        "rt": "52584576",
    }
    res = requests.get(url, params=params)
    data_json = demjson.decode(res.text[res.text.find("={") + 1 :])
    return data_json["pages"]


def stock_em_sy_list(symbol="沪市主板", trade_date="2019-09-30"):
    """
    东方财富网-数据中心-特色数据-商誉-个股商誉明细
    http://data.eastmoney.com/sy/list.html
    :return: pandas.DataFrame
    """
    symbol_dict = {
        "沪市主板": f"(MKT='shzb' and REPORTDATE=^{trade_date}^)",
        "深市主板": f"(MKT='szzb' and REPORTDATE=^{trade_date}^)",
        "中小板": f"(MKT='zxb' and REPORTDATE=^{trade_date}^)",
        "创业板": f"(MKT='cyb' and REPORTDATE=^{trade_date}^)",
        "沪深两市": f"(REPORTDATE=^{trade_date}^)",
    }
    url = "http://dcfm.eastmoney.com/EM_MutiSvcExpandInterface/api/js/get"
    page_num = _get_page_num_sy_list(symbol=symbol, trade_date=trade_date)
    temp_df = pd.DataFrame()
    for page in range(1, page_num + 1):
        print(f"一共{page_num}页, 正在下载第{page}页")
        params = {
            "type": "SY_MX",
            "token": "894050c76af8597a853f5b408b759f5d",
            "st": "NOTICEDATE",
            "sr": "-1",
            "p": str(page),
            "ps": "50",
            "js": "var {name}=".format(name=ctx.call("getCode", 8))
            + "{pages:(tp),data:(x),font:(font)}",
            "filter": symbol_dict[symbol],
            "rt": "52584576",
        }
        res = requests.get(url, params=params)
        data_text = res.text
        data_json = demjson.decode(data_text[data_text.find("={") + 1 :])
        temp_df = temp_df.append(pd.DataFrame(data_json["data"]), ignore_index=True)
    temp_df.columns = [
        "股票代码",
        "COMPANYCODE",
        "股票简称",
        "MKT",
        "REPORTTIMETYPECODE",
        "COMBINETYPECODE",
        "DATAAJUSTTYPE",
        "商誉(元)",
        "GOODWILL_Change",
        "SUMSHEQUITY",
        "商誉占净资产比例(%)",
        "SUMSHEQUITY_Change_Rate",
        "公告日期",
        "REPORTDATE",
        "净利润(元)",
        "PARENTNETPROFIT_Change_Rate",
        "HYName",
        "HYCode",
        "净利润同比(%)",
        "上年商誉(元)",
        "ListingDate",
        "ListingState",
        "MX_Type",
    ]
    temp_df = temp_df[
        [
            "股票代码",
            "股票简称",
            "商誉(元)",
            "商誉占净资产比例(%)",
            "公告日期",
            "净利润(元)",
            "净利润同比(%)",
            "上年商誉(元)",
        ]
    ]
    temp_df["公告日期"] = pd.to_datetime(temp_df["公告日期"])
    return temp_df


def _get_page_num_sy_hy_list(trade_date="2019-09-30"):
    """
    东方财富网-数据中心-特色数据-商誉-行业商誉
    http://data.eastmoney.com/sy/hylist.html
    :return: int 获取 行业商誉 的总页数
    """
    url = "http://dcfm.eastmoney.com/EM_MutiSvcExpandInterface/api/js/get"
    params = {
        "type": "HY_SY_SUM",
        "token": "894050c76af8597a853f5b408b759f5d",
        "st": "SUMSHEQUITY_Rate",
        "sr": "-1",
        "p": "1",
        "ps": "50",
        "js": "var {name}=".format(name=ctx.call("getCode", 8))
        + "{pages:(tp),data:(x),font:(font)}",
        "filter": f"(MKT='all' and REPORTDATE=^{trade_date}^)",
        "rt": "52584617",
    }
    res = requests.get(url, params=params)
    data_json = demjson.decode(res.text[res.text.find("={") + 1 :])
    return data_json["pages"]


def stock_em_sy_hy_list(trade_date="2019-09-30"):
    """
    东方财富网-数据中心-特色数据-商誉-行业商誉
    http://data.eastmoney.com/sy/hylist.html
    :return: pandas.DataFrame
    """
    url = "http://dcfm.eastmoney.com/EM_MutiSvcExpandInterface/api/js/get"
    page_num = _get_page_num_sy_hy_list(trade_date=trade_date)
    temp_df = pd.DataFrame()
    for page in range(1, page_num + 1):
        print(f"一共{page_num}页, 正在下载第{page}页")
        params = {
            "type": "HY_SY_SUM",
            "token": "894050c76af8597a853f5b408b759f5d",
            "st": "SUMSHEQUITY_Rate",
            "sr": "-1",
            "p": str(page),
            "ps": "50",
            "js": "var {name}=".format(name=ctx.call("getCode", 8))
            + "{pages:(tp),data:(x),font:(font)}",
            "filter": f"(MKT='all' and REPORTDATE=^{trade_date}^)",
            "rt": "52584617",
        }
        res = requests.get(url, params=params)
        data_text = res.text
        data_json = demjson.decode(data_text[data_text.find("={") + 1 :])
        temp_df = temp_df.append(pd.DataFrame(data_json["data"]), ignore_index=True)
    temp_df.columns = [
        "行业名称",
        "HYCode",
        "MKT",
        "公司家数",
        "商誉规模(元)",
        "GOODWILL_Change",
        "净资产(元)",
        "商誉规模占净资产规模比例(%)",
        "SUMSHEQUITY_Change_Rate",
        "REPORTDATE",
        "净利润规模(元)",
        "PARENTNETPROFIT_Change_Rate",
        "SygmType",
        "SyztType",
    ]
    temp_df = temp_df[
        ["行业名称", "公司家数", "商誉规模(元)", "净资产(元)", "商誉规模占净资产规模比例(%)", "净利润规模(元)"]
    ]
    return temp_df


if __name__ == "__main__":
    stock_em_sy_profile_df = stock_em_sy_profile()
    print(stock_em_sy_profile_df)
    stock_em_sy_yq_list_df = stock_em_sy_yq_list()
    print(stock_em_sy_yq_list_df)
    stock_em_sy_jz_list_df = stock_em_sy_jz_list()
    print(stock_em_sy_jz_list_df)
    stock_em_sy_list_df = stock_em_sy_list()
    print(stock_em_sy_list_df)
    stock_em_sy_hy_list_df = stock_em_sy_hy_list()
    print(stock_em_sy_hy_list_df)

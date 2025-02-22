# -*- coding:utf-8 -*- 
"""
交易数据接口 
Created on 2019/07/31
@author: Tony Du
@group : Dtshare
@contact: dtshare@126.com
"""
from __future__ import division

import time
import json
import lxml.html
from lxml import etree
import pandas as pd
import numpy as np
import datetime
from dtseek.utils import cons as ct
import re
from dtseek.utils import dateu as du
from dtseek.utils.formula import MA
import os
try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib3 import urlopen, Request
v = pd.__version__ 
if int(v.split('.')[1])>=25 or int(v.split('.')[0])>0:
    from io import StringIO
else:    
    from pandas.compat import StringIO


bs_type = {'1':u'买入', 
           '2': u'卖出', 
           '4': u'-'}


def get_hist_data(code=None, start=None, end=None,
                  ktype='D', retry_count=3,
                  pause=0.001):
    """
        获取个股历史交易记录
    Parameters
    ------
      code:string
                  股票代码 e.g. 600848
      start:string
                  开始日期 format：YYYY-MM-DD 为空时取到API所提供的最早日期数据
      end:string
                  结束日期 format：YYYY-MM-DD 为空时取到最近一个交易日数据
      ktype：string
                  数据类型，D=日k线 W=周 M=月 5=5分钟 15=15分钟 30=30分钟 60=60分钟，默认为D
      retry_count : int, 默认 3
                 如遇网络等问题重复执行的次数 
      pause : int, 默认 0
                重复请求数据过程中暂停的秒数，防止请求间隔时间太短出现的问题
    return
    -------
      DataFrame
          属性:日期 ，开盘价， 最高价， 收盘价， 最低价， 成交量， 价格变动 ，涨跌幅，5日均价，10日均价，20日均价，5日均量，10日均量，20日均量，换手率
    """
    symbol = ct._code_to_symbol(code)
    url = ''
    if ktype.upper() in ct.K_LABELS:
        url = ct.DAY_PRICE_URL%(ct.P_TYPE['http'], ct.DOMAINS['ifeng'],
                                ct.K_TYPE[ktype.upper()], symbol)
    elif ktype in ct.K_MIN_LABELS:
        url = ct.DAY_PRICE_MIN_URL%(ct.P_TYPE['http'], ct.DOMAINS['ifeng'],
                                    symbol, ktype)
    else:
        raise TypeError('ktype input error.')
    
    for _ in range(retry_count):
        time.sleep(pause)
        try:
            request = Request(url)
            lines = urlopen(request, timeout = 10).read()
            if len(lines) < 15: #no data
                return None
        except Exception as e:
            print(e)
        else:
            js = json.loads(lines.decode('utf-8') if ct.PY3 else lines)
            cols = []
            if (code in ct.INDEX_LABELS) & (ktype.upper() in ct.K_LABELS):
                cols = ct.INX_DAY_PRICE_COLUMNS
            else:
                cols = ct.DAY_PRICE_COLUMNS
            if len(js['record'][0]) == 14:
                cols = ct.INX_DAY_PRICE_COLUMNS
            df = pd.DataFrame(js['record'], columns=cols)
            if ktype.upper() in ['D', 'W', 'M']:
                df = df.applymap(lambda x: x.replace(u',', u''))
                df[df==''] = 0
            for col in cols[1:]:
                df[col] = df[col].astype(float)
            if start is not None:
                df = df[df.date >= start]
            if end is not None:
                df = df[df.date <= end]
            if (code in ct.INDEX_LABELS) & (ktype in ct.K_MIN_LABELS):
                df = df.drop('turnover', axis=1)
            df = df.set_index('date')
            df = df.sort_index(ascending = False)
            return df
    raise IOError(ct.NETWORK_URL_ERROR_MSG)


def _parsing_dayprice_json(types=None, page=1):
    """
           处理当日行情分页数据，格式为json
     Parameters
     ------
        pageNum:页码
     return
     -------
        DataFrame 当日所有股票交易数据(DataFrame)
    """
    ct._write_console()
    request = Request(ct.SINA_DAY_PRICE_URL%(ct.P_TYPE['http'], ct.DOMAINS['vsf'],
                                 ct.PAGES['jv'], types, page))
    text = urlopen(request, timeout=10).read()
    if text == 'null':
        return None
    reg = re.compile(r'\,(.*?)\:') 
    text = reg.sub(r',"\1":', text.decode('gbk') if ct.PY3 else text) 
    text = text.replace('"{symbol', '{"symbol')
    text = text.replace('{symbol', '{"symbol"')
    if ct.PY3:
        jstr = json.dumps(text)
    else:
        jstr = json.dumps(text, encoding='GBK')
    js = json.loads(jstr)
    df = pd.DataFrame(pd.read_json(js, dtype={'code':object}),
                      columns=ct.DAY_TRADING_COLUMNS)
    df = df.drop('symbol', axis=1)
#     df = df.ix[df.volume > 0]
    return df


def get_tick_data(code=None, retry_count=3, pause=0.001):
    """
        获取分笔数据
    Parameters
    ------
        code:string
                  股票代码 e.g. 600848
                  如遇网络等问题重复执行的次数
        pause : int, 默认 0
                 重复请求数据过程中暂停的秒数，防止请求间隔时间太短出现的问题
        src : 数据源选择，可输入sn(新浪)、tt(腾讯)、nt(网易)，默认sn
     return
     -------
        DataFrame 当日所有股票交易数据(DataFrame)
              属性:成交时间、成交价格、价格变动，成交手、成交金额(元)，买卖类型
    """
    symbol = ct._code_to_symbol(code)
    url = 'http://push2ex.eastmoney.com/getStockFenShi?pagesize=4444&ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wzfscj&cb=&pageindex=0&id=3000592&sort=1&ft=1&code=%s&market=%s&_=%s'
    for _ in range(retry_count):
        time.sleep(pause)
        try:
            re = Request(url%(code, symbol, _random()))
            lines = urlopen(re, timeout=10).read()
            lines = lines.decode('GBK') 
            lines = json.loads(lines)
            lines = lines['data']['data']
            df = pd.DataFrame(lines)   
            df.columns = ['time', 'price', 'vol', 'type']
            df['price'] = df['price'].map(lambda x: x/1000)
            df['type'] = df['type'].map(lambda x: bs_type[str(x)])
            df['time'] = df['time'].map(lambda x: str(x).zfill(6))
            print(df)    
        except Exception as e:
            print(e)
        else:
            return df
    raise IOError(ct.NETWORK_URL_ERROR_MSG)

def get_realtime_quotes(symbols=None):
    """
        获取实时交易数据 getting real time quotes data
       用于跟踪交易情况（本次执行的结果-上一次执行的数据）
    Parameters
    ------
        symbols : string, array-like object (list, tuple, Series).
        
    return
    -------
        DataFrame 实时交易数据
              属性:0：name，股票名字
            1：open，今日开盘价
            2：pre_close，昨日收盘价
            3：price，当前价格
            4：high，今日最高价
            5：low，今日最低价
            6：bid，竞买价，即“买一”报价
            7：ask，竞卖价，即“卖一”报价
            8：volumn，成交量 maybe you need do volumn/100
            9：amount，成交金额（元 CNY）
            10：b1_v，委买一（笔数 bid volume）
            11：b1_p，委买一（价格 bid price）
            12：b2_v，“买二”
            13：b2_p，“买二”
            14：b3_v，“买三”
            15：b3_p，“买三”
            16：b4_v，“买四”
            17：b4_p，“买四”
            18：b5_v，“买五”
            19：b5_p，“买五”
            20：a1_v，委卖一（笔数 ask volume）
            21：a1_p，委卖一（价格 ask price）
            ...
            30：date，日期；
            31：time，时间；
    """
    symbols_list = ''
    if isinstance(symbols, list) or isinstance(symbols, set) or isinstance(symbols, tuple) or isinstance(symbols, pd.Series):
        for code in symbols:
            symbols_list += ct._code_to_symbol(code) + ','
    else:
        symbols_list = ct._code_to_symbol(symbols)
        
    symbols_list = symbols_list[:-1] if len(symbols_list) > 8 else symbols_list 
    request = Request(ct.LIVE_DATA_URL%(ct.P_TYPE['http'], ct.DOMAINS['sinahq'],
                                                _random(), symbols_list))
    text = urlopen(request,timeout=10).read()
    text = text.decode('GBK')
    reg = re.compile(r'\="(.*?)\";')
    data = reg.findall(text)
    regSym = re.compile(r'(?:sh|sz)(.*?)\=')
    syms = regSym.findall(text)
    data_list = []
    syms_list = []
    for index, row in enumerate(data):
        if len(row)>1:
            data_list.append([astr for astr in row.split(',')[:33]])
            syms_list.append(syms[index])
    if len(syms_list) == 0:
        return None
    df = pd.DataFrame(data_list, columns=ct.LIVE_DATA_COLS)
    df = df.drop('s', axis=1)
    df['code'] = syms_list
    ls = [cls for cls in df.columns if '_v' in cls]
    for txt in ls:
        df[txt] = df[txt].map(lambda x : x[:-2])
    return df


def get_h_data(code, start=None, end=None, autype='qfq',
               index=False, retry_count=3, pause=0.001, drop_factor=True):
    '''
    获取历史复权数据
    Parameters
    ------
      code:string
                  股票代码 e.g. 600848
      start:string
                  开始日期 format：YYYY-MM-DD 为空时取当前日期
      end:string
                  结束日期 format：YYYY-MM-DD 为空时取去年今日
      autype:string
                  复权类型，qfq-前复权 hfq-后复权 None-不复权，默认为qfq
      retry_count : int, 默认 3
                 如遇网络等问题重复执行的次数 
      pause : int, 默认 0
                重复请求数据过程中暂停的秒数，防止请求间隔时间太短出现的问题
      drop_factor : bool, 默认 True
                是否移除复权因子，在分析过程中可能复权因子意义不大，但是如需要先储存到数据库之后再分析的话，有该项目会更加灵活
    return
    -------
      DataFrame
          date 交易日期 (index)
          open 开盘价
          high  最高价
          close 收盘价
          low 最低价
          volume 成交量
          amount 成交金额
    '''
    
    start = du.today_last_year() if start is None else start
    end = du.today() if end is None else end
    qs = du.get_quarts(start, end)
    qt = qs[0]
    ct._write_head()
    data = _parse_fq_data(_get_index_url(index, code, qt), index,
                          retry_count, pause)
    if data is None:
        data = pd.DataFrame()
    if len(qs)>1:
        for d in range(1, len(qs)):
            qt = qs[d]
            ct._write_console()
            df = _parse_fq_data(_get_index_url(index, code, qt), index,
                                retry_count, pause)
            if df is None:  # 可能df为空，退出循环
                break
            else:
                data = data.append(df, ignore_index = True)
    if len(data) == 0 or len(data[(data.date >= start) & (data.date <= end)]) == 0:
        return pd.DataFrame()
    data = data.drop_duplicates('date')
    if index:
        data = data[(data.date >= start) & (data.date <= end)]
        data = data.set_index('date')
        data = data.sort_index(ascending = False)
        return data
    if autype == 'hfq':
        if drop_factor:
            data = data.drop('factor', axis=1)
        data = data[(data.date >= start) & (data.date <= end)]
        for label in ['open', 'high', 'close', 'low']:
            data[label] = data[label].map(ct.FORMAT)
            data[label] = data[label].astype(float)
        data = data.set_index('date')
        data = data.sort_index(ascending = False)
        return data
    else:
        if autype == 'qfq':
            if drop_factor:
                data = data.drop('factor', axis = 1)
            df = _parase_fq_factor(code, start, end)
            df = df.drop_duplicates('date')
            df = df.sort_values('date', ascending = False)
            firstDate = data.head(1)['date']
            frow = df[df.date == firstDate[0]]
            rt = get_realtime_quotes(code)
            if rt is None:
                return pd.DataFrame()
            if ((float(rt['high']) == 0) & (float(rt['low']) == 0)):
                preClose = float(rt['pre_close'])
            
            rate = float(frow['factor']) / preClose
            data = data[(data.date >= start) & (data.date <= end)]
            for label in ['open', 'high', 'low', 'close']:
                data[label] = data[label] / rate
                data[label] = data[label].map(ct.FORMAT)
                data[label] = data[label].astype(float)
            data = data.set_index('date')
            data = data.sort_index(ascending = False)
            return data
        else:
            for label in ['open', 'high', 'close', 'low']:
                data[label] = data[label] / data['factor']
            if drop_factor:
                data = data.drop('factor', axis=1)
            data = data[(data.date >= start) & (data.date <= end)]
            for label in ['open', 'high', 'close', 'low']:
                data[label] = data[label].map(ct.FORMAT)
            data = data.set_index('date')
            data = data.sort_index(ascending = False)
            data = data.astype(float)
            return data


def _parase_fq_factor(code, start, end):
    symbol = ct._code_to_symbol(code)
    request = Request(ct.HIST_FQ_FACTOR_URL%(ct.P_TYPE['http'],
                                             ct.DOMAINS['vsf'], symbol))
    text = urlopen(request, timeout=10).read()
    text = text[1:len(text)-1]
    text = text.decode('utf-8') if ct.PY3 else text
    text = text.replace('{_', '{"')
    text = text.replace('total', '"total"')
    text = text.replace('data', '"data"')
    text = text.replace(':"', '":"')
    text = text.replace('",_', '","')
    text = text.replace('_', '-')
    text = json.loads(text)
    df = pd.DataFrame({'date':list(text['data'].keys()), 'factor':list(text['data'].values())})
    df['date'] = df['date'].map(_fun_except) # for null case
    if df['date'].dtypes == np.object:
        df['date'] = pd.to_datetime(df['date'])
    df = df.drop_duplicates('date')
    df['factor'] = df['factor'].astype(float)
    return df


def _fun_except(x):
    if len(x) > 10:
        return x[-10:]
    else:
        return x


def _parse_fq_data(url, index, retry_count, pause):
    for _ in range(retry_count):
        time.sleep(pause)
        try:
            request = Request(url)
            text = urlopen(request, timeout=10).read()
            text = text.decode('GBK')
            html = lxml.html.parse(StringIO(text))
            res = html.xpath('//table[@id=\"FundHoldSharesTable\"]')
            if ct.PY3:
                sarr = [etree.tostring(node).decode('utf-8') for node in res]
            else:
                sarr = [etree.tostring(node) for node in res]
            sarr = ''.join(sarr)
            if sarr == '':
                return None
            df = pd.read_html(sarr, skiprows = [0, 1])[0]
            if len(df) == 0:
                return pd.DataFrame()
            if index:
                df.columns = ct.HIST_FQ_COLS[0:7]
            else:
                df.columns = ct.HIST_FQ_COLS
            if df['date'].dtypes == np.object:
                df['date'] = pd.to_datetime(df['date'])
            df = df.drop_duplicates('date')
        except ValueError as e:
            # 时间较早，已经读不到数据
            return None
        except Exception as e:
            print(e)
        else:
            return df
    raise IOError(ct.NETWORK_URL_ERROR_MSG)


def get_index():
    """
    获取大盘指数行情
    return
    -------
      DataFrame
          code:指数代码
          name:指数名称
          change:涨跌幅
          open:开盘价
          preclose:昨日收盘价
          close:收盘价
          high:最高价
          low:最低价
          volume:成交量(手)
          amount:成交金额（亿元）
    """
    request = Request(ct.INDEX_HQ_URL%(ct.P_TYPE['http'],
                                             ct.DOMAINS['sinahq']))
    text = urlopen(request, timeout=10).read()
    text = text.decode('GBK')
    text = text.replace('var hq_str_sh', '').replace('var hq_str_sz', '')
    text = text.replace('";', '').replace('"', '').replace('=', ',')
    text = '%s%s'%(ct.INDEX_HEADER, text)
    df = pd.read_csv(StringIO(text), sep=',', thousands=',')
    df['change'] = (df['close'] / df['preclose'] - 1 ) * 100
    df['amount'] = df['amount'] / 100000000
    df['change'] = df['change'].map(ct.FORMAT)
    df['amount'] = df['amount'].map(ct.FORMAT4)
    df = df[ct.INDEX_COLS]
    df['code'] = df['code'].map(lambda x:str(x).zfill(6))
    df['change'] = df['change'].astype(float)
    df['amount'] = df['amount'].astype(float)
    return df
 

def _get_index_url(index, code, qt):
    if index:
        url = ct.HIST_INDEX_URL%(ct.P_TYPE['http'], ct.DOMAINS['vsf'],
                              code, qt[0], qt[1])
    else:
        url = ct.HIST_FQ_URL%(ct.P_TYPE['http'], ct.DOMAINS['vsf'],
                              code, qt[0], qt[1])
    return url


def get_k_data(code=None, start='', end='',
                  ktype='D', autype='qfq', 
                  index=False,
                  retry_count=3,
                  pause=0.001):
    """
    获取k线数据
    ---------
    Parameters:
      code:string
                  股票代码 e.g. 600848
      start:string
                  开始日期 format：YYYY-MM-DD 为空时取上市首日
      end:string
                  结束日期 format：YYYY-MM-DD 为空时取最近一个交易日
      autype:string
                  复权类型，qfq-前复权 hfq-后复权 None-不复权，默认为qfq
      ktype：string
                  数据类型，D=日k线 W=周 M=月 5=5分钟 15=15分钟 30=30分钟 60=60分钟，默认为D
      retry_count : int, 默认 3
                 如遇网络等问题重复执行的次数 
      pause : int, 默认 0
                重复请求数据过程中暂停的秒数，防止请求间隔时间太短出现的问题
    return
    -------
      DataFrame
          date 交易日期 (index)
          open 开盘价
          high  最高价
          close 收盘价
          low 最低价
          volume 成交量
          amount 成交额
          turnoverratio 换手率
          code 股票代码
    """
    symbol = ct.INDEX_SYMBOL[code] if index else ct._code_to_symbol(code)
    url = ''
    dataflag = ''
    autype = '' if autype is None else autype
    if (start is not None) & (start != ''):
        end = du.today() if end is None or end == '' else end
    if ktype.upper() in ct.K_LABELS:
        fq = autype if autype is not None else ''
        if code[:1] in ('1', '5') or index:
            fq = ''
        kline = '' if autype is None else 'fq'
        if (start is None or start == '') & (end is None or end == ''):
            urls = [ct.KLINE_TT_URL%(ct.P_TYPE['http'], ct.DOMAINS['tt'],
                                    kline, fq, symbol, 
                                    ct.TT_K_TYPE[ktype.upper()], start, end,
                                    fq, _random(17))]
        else:
            years = du.tt_dates(start, end)
            urls = []
            for year in years:
                startdate = str(year) + '-01-01'
                enddate = str(year+1) + '-12-31'
                url = ct.KLINE_TT_URL%(ct.P_TYPE['http'], ct.DOMAINS['tt'],
                                    kline, fq+str(year), symbol, 
                                    ct.TT_K_TYPE[ktype.upper()], startdate, enddate,
                                    fq, _random(17))
                urls.append(url)
        dataflag = '%s%s'%(fq, ct.TT_K_TYPE[ktype.upper()])
    elif ktype in ct.K_MIN_LABELS:
        urls = [ct.KLINE_TT_MIN_URL%(ct.P_TYPE['http'], ct.DOMAINS['tt'],
                                    symbol, ktype, ktype,
                                    _random(16))]
        dataflag = 'm%s'%ktype
    else:
        raise TypeError('ktype input error.')
    data = pd.DataFrame()
    for url in urls:
        data = data.append(_get_k_data(url, dataflag, 
                                       symbol, code,
                                       index, ktype,
                                       retry_count, pause), 
                           ignore_index=True)
    if ktype not in ct.K_MIN_LABELS:
        if ((start is not None) & (start != '')) & ((end is not None) & (end != '')):
            if data.empty==False:       
                data = data[(data.date >= start) & (data.date <= end)]
    return data
    raise IOError(ct.NETWORK_URL_ERROR_MSG)
    

def _get_k_data(url, dataflag='',
                symbol='',
                code = '',
                index = False,
                ktype = '',
                retry_count=3,
                pause=0.001):
    for _ in range(retry_count):
            time.sleep(pause)
            try:
                request = Request(url)
                lines = urlopen(request, timeout = 10).read()
                if len(lines) < 100: #no data
                    return None
            except Exception as e:
                print(e)
            else:
                lines = lines.decode('utf-8') if ct.PY3 else lines
                lines = lines.split('=')[1]
                reg = re.compile(r',{"nd.*?}') 
                lines = re.subn(reg, '', lines) 
                js = json.loads(lines[0])
                dataflag = dataflag if dataflag in list(js['data'][symbol].keys()) else ct.TT_K_TYPE[ktype.upper()]
                if len(js['data'][symbol][dataflag]) == 0:
                    return None
                if len(js['data'][symbol][dataflag][0]) == 6:
                    df = pd.DataFrame(js['data'][symbol][dataflag], 
                                  columns = ct.KLINE_TT_COLS_MINS)
                else:
                    df = pd.DataFrame(js['data'][symbol][dataflag], 
                                  columns = ct.KLINE_TT_COLS)
                df['code'] = symbol if index else code
                if ktype in ct.K_MIN_LABELS:
                    df['date'] = df['date'].map(lambda x: '%s-%s-%s %s:%s'%(x[0:4], x[4:6], 
                                                                            x[6:8], x[8:10], 
                                                                            x[10:12]))
                for col in df.columns[1:6]:
                    df[col] = df[col].astype(float)
                return df

def get_hists(symbols, start=None, end=None,
                  ktype='D', retry_count=3,
                  pause=0.001):
    """
    批量获取历史行情数据，具体参数和返回数据类型请参考get_hist_data接口
    """
    df = pd.DataFrame()
    if isinstance(symbols, list) or isinstance(symbols, set) or isinstance(symbols, tuple) or isinstance(symbols, pd.Series):
        for symbol in symbols:
            data = get_hist_data(symbol, start=start, end=end,
                                 ktype=ktype, retry_count=retry_count,
                                 pause=pause)
            data['code'] = symbol
            df = df.append(data, ignore_index=True)
        return df
    else:
        return None
  
 
def get_dt_time(t):
    tstr = str(t)[:-2]
    tstr = tstr.replace('-', '').replace(':', '')
    return tstr



def _get_mkcode(code='', asset='E', xapi=None):
    mkcode = ''
    if asset == 'E':
        mkcode = ct._market_code(code)
    elif asset == 'INDEX':
        mkcode = ct._idx_market_code(code)
    else:
        if os.path.exists(ct.INST_PLK_F):
            mks = pd.read_pickle(ct.INST_PLK_F)
        else:
            mks = get_instrument(xapi)
            mks.to_pickle(ct.INST_PLK_F)
        mkcode = mks[mks.code == code]['market'].values[0]
    return mkcode


def get_instrument(xapi=None):
    """
            获取证券列表
    """
    import dtseek.util.conns as cs
    xapi = cs.xapi_x() if xapi is None else xapi
    if xapi is None:
        print(ct.MSG_NOT_CONNECTED)
        return None
    data=[]
    for i in range(200): # range for python2/3
        ds = xapi.get_instrument_info(i * 300, 300)
        data += ds
        if len(ds) < 300:
            break
    data = xapi.to_df(data)
    return data

def _random(n=13):
    from random import randint
    start = 10**(n-1)
    end = (10**n)-1
    return str(randint(start, end))


if __name__ == '__main__':
#     get_tick_data('600848')
#     print(get_index())
    print(get_k_data('600000'))
    
    

# -*- coding:utf-8 -*-
from sqlalchemy import create_engine
import pymysql 
import pandas as pd
import numpy as np
from pandas.io import sql
from pandas.lib import to_datetime
from pandas.lib import Timestamp
import datetime,time,os
import tushare as ts

import easytrader,easyhistory
import time,os

#ROOT_DIR='E:/work/stockAnalyze'
#ROOT_DIR="C:/中国银河证券海王星/T0002"
#ROOT_DIR="C:\work\stockAnalyze"
RAW_HIST_DIR="C:/中国银河证券海王星/T0002/export/"  
#HIST_DIR=ROOT_DIR+'/update/'
#"""
import tradeTime as tt
import sendEmail as sm
import qq_quotation as qq

"""
from . import tradeTime as tt
from . import sendEmail as sm
from . import qq_quotation as qq
"""

def form_sql(table_name,oper_type='query',select_field=None,where_condition=None,insert_field=None,update_field=None,update_value=None):
    """
    :param table_name: string type, db_name.table_name
    :param select_field: string type, like 'id,type,value'
    :param where_condition: string type, like 'field_value>50'
    :param insert_field: string type, like '(date_time,measurement_id,value)'
    :param update_field: string type, like 'value' or  '(measurement_id,value)'
    :param update_value: value or string type, like '1000' or "'normal_type'"
    :return: sql string
    
    :use example:
    :query: sql_q=form_sql(table_name='stock.account',oper_type='query',select_field='acc_name,initial',where_condition="acc_name='36005'")
    :insert: sql_insert=form_sql(table_name='stock.account',oper_type='insert',insert_field='(acc_name,initial,comm)')
    :update: sql_update=form_sql(table_name='stock.account',oper_type='update',update_field='initial',where_condition='initial=2900019000',set_value_str='29000')
    :delete: sql_delete=form_sql(table_name='stock.account',oper_type='delete',where_condition="initial=14200.0")
    """
    sql=''
    if table_name=='' or not table_name:
        return sql
    if oper_type=='query':
        field='*'
        if select_field:
            field=select_field
        condition=''
        if where_condition:
            condition=' where %s' % where_condition
        sql='select %s from %s'%(field,table_name) + condition +';'
    elif oper_type=='insert' and insert_field:
        num=len(insert_field.split(','))
        value_tail='%s,'*num
        value_tail='('+value_tail[:-1]+')'
        sql='insert into %s '% table_name +insert_field +' values'+ value_tail + ';'
    elif oper_type=='update' and where_condition and update_field:
        """
        update_value_str=str(update_value)
        if isinstance(update_value, str):
            update_value_str="'%s'"%update_value
        """
        sql='update %s set %s='%(table_name,update_field)+ update_value + ' where '+  where_condition + ';'
        """
        sql=''
        num=len(update_field.split(','))
        if num==1:
            sql='update %s set %s='%(table_name,update_field)+ update_value + ' where '+  where_condition + ';'
        elif num>1:
            value_tail='%s,'*num
            value_tail='('+value_tail[:-1]+')'
            update_sql="update test set " + update_field +value_tail + ':'
        else:
            pass
        """
    elif oper_type=='delete':
        condition=''
        if where_condition:
            condition=' where %s' % where_condition
        sql='delete from %s'%table_name + condition + ';'
    else:
        pass
    # print('%s_sql=%s'%(oper_type,sql))
    return sql


def get_raw_hist_df(code_str,latest_count=None):
    file_type='csv'
    file_name='C:/hist/day/data/'+code_str+'.'+file_type
    #print('file_name=',file_name)
    raw_column_list=['date','open','high','low','close','volume','rmb','factor']
    #print('file_name=',file_name)
    df_0=pd.DataFrame({},columns=raw_column_list)
    try:
        #print('code_str=%s'%code_str)
        #df=pd.read_csv(file_name,names=raw_column_list, header=0,encoding='gb2312' #='gb18030')#'utf-8')   #for python3 
        hist_df = pd.read_csv(file_name)
        hist_df['rmb'] = hist_df['amount']
        #del hist_df['amount']
        #del hist_df['MA1']
        #print(hist_df)
        #print('pd.read_csv=',df)
        if hist_df.empty:
            #print('code_str=',code_str)
            return df_0
        
        return hist_df
    except OSError as e:
        #print('OSError:',e)
        return df_0

def get_yh_raw_hist_df(code_str,latest_count=None):
    file_type='csv'
    RAW_HIST_DIR="C:/中国银河证券海王星/T0002/export/"
    file_name=RAW_HIST_DIR+code_str+'.'+file_type
    raw_column_list=['date','open','high','low','close','volume','amount']
    #print('file_name=',file_name)
    df_0=pd.DataFrame({},columns=raw_column_list)
    try:
        #print('code_str=%s'%code_str)
        df=pd.read_csv(file_name,names=raw_column_list, header=0,encoding='gb2312')#'utf-8')   #for python3
        #print('pd.read_csv=',df)
        if df.empty:
            #print('code_str=',code_str)
            df_0.to_csv(file_name,encoding='utf-8')
            return df_0
        #else:
        #    return
        last_date=df.tail(1).iloc[0].date
        if last_date=='数据来源:通达信':
            df=df[:-1]
            #print('数据来源:通达信')
            #print(df.tail(1).iloc[0].date)
            if df.empty:
                df_0.to_csv(file_name,encoding='utf-8')
                return df_0
            #else:
            #   return
            last_volume=df.tail(1).iloc[0].volume
            if int(last_volume)==0:
                df=df[:-1]
            df['date'].astype(Timestamp)
            df_to_write = df.set_index('date')
            df_to_write.to_csv(file_name,encoding='utf-8')
        else:
            pass
        return df
    except OSError as e:
        #print('OSError:',e)
        df_0.to_csv(file_name,encoding='utf-8')
        return df_0
    
def get_easyhistory_df(code_str,source='easyhistory'):  #ta_lib
    data_path = 'C:/hist/day/data/'
    if source=='YH' or source=='yh':
        data_path = 'C:/中国银河证券海王星/T0002/export/'
    his = easyhistory.History(dtype='D', path=data_path,type='csv',codes=[code_str])
    res = his.get_hist_indicator(code_str)
    return res


def update_one_hist(code_str,stock_sql_obj,histdata_last_df,update_db=True):
    """
    :param code_str: string type, code string_name
    :param stock_sql_obj: StockSQL type, 
    :param histdata_last_df: dataframe type, df from table histdata
    :return: 
    """
    df=get_raw_hist_df(code_str)
    if df.empty:
        return 0
    code_list=[code_str]*len(df)
    df['code']=pd.Series(code_list,index=df.index)
    p=df.pop('code')
    df.insert(0,'code',p)
    #print("update_one_hist1")
    last_db_date=stock_sql_obj.get_last_db_date(code_str,histdata_last_df)
    #print("update_one_hist2")
    last_db_date_str=''
    #print('last_db_date',last_db_date,type(last_db_date))
    #print('last_db_date_str',last_db_date_str)
    #criteria0=df.volume>0
    #df=df[df.volume>0]
    if last_db_date:
        last_db_date_str='%s' % last_db_date
        last_db_date_str=last_db_date_str[:10]
        #criteria1=df.date>last_db_date_str
        df=df[df.date>last_db_date_str]
        #print('sub df', df)
    if df.empty:
        #print('History data up-to-date for %s, no need update' % code_str)
        return 0
    if update_db:
        stock_sql_obj.insert_table(df, 'histdata')
    #print(df.tail(1))
    #print(df.tail(1).iloc[0])
    update_date=df.tail(1).iloc[0].date
    #last_date=histdata_last_df.loc[date[-1],'date']
    #update_date= 2015-11-20 <class 'str'>
    #print('update_date=',update_date,type(update_date))
    stock_sql_obj.update_last_db_date(code_str,last_db_date_str,update_date)
    return len(df)

def get_file_timestamp(file_name):
    #get last modify time of given file
    file_mt_str=''
    try:
        file_mt= time.localtime(os.stat(file_name).st_mtime)
        file_mt_str=time.strftime("%Y-%m-%d %X",file_mt)
    except:
        #file do not exist
        pass
    return file_mt_str

#get the all file source data in certain DIR
def get_dir_latest_modify_time(hist_dir,codes={}):
    """
    :param hist_dir: string type, DIR of export data
    :return: list type, code string list 
    """
    all_code=[]
    latest_time = '1970-01-01 00:00:00'
    if codes:
        for code in codes:
            full_file_name = hist_dir + '%s.csv' % code
            file_mt_str = get_file_timestamp(full_file_name)
            if file_mt_str > latest_time:
                latest_time = file_mt_str
            all_code = codes  
    else:
        for filename in os.listdir(hist_dir):#(r'ROOT_DIR+/export'):
            code=filename[:-4]
            if len(code)==6:
                all_code.append(code)
            full_file_name = hist_dir + filename
            file_mt_str = get_file_timestamp(full_file_name)
            if file_mt_str > latest_time:
                latest_time = file_mt_str
    return all_code,latest_time

#get the all file source data in certain DIR
def get_all_code(hist_dir):
    """
    :param hist_dir: string type, DIR of export data
    :return: list type, code string list 
    """
    all_code=[]
    for filename in os.listdir(hist_dir):#(r'ROOT_DIR+/export'):
        code=filename[:-4]
        if len(code)==6:
            all_code.append(code)
    return all_code

def get_different_symbols(hist_dir='C:/hist/day/data/'):
    indexs= ['cyb', 'zxb', 'sz', 'sh', 'sz300', 'zx300', 'hs300', 'sh50']
    all_codes = get_all_code(hist_dir)
    funds =[]
    b_stock = []
    for code in all_codes:
        if code.startswith('1') or code.startswith('5'):
            funds.append(code)
        elif code.startswith('9'):
            b_stock.append(code)
    except_codes = ['000029']
    all_stocks = list(set(all_codes).difference(set(funds+indexs+except_codes)))
    return indexs,funds,b_stock,all_stocks
    
def update_all_hist_data(codes,update_db=True):
    """
    :param codes: list type, code string list 
    :return: 
    """
    starttime=datetime.datetime.now()
    stock_sql_obj=StockSQL()
    print('histdata_last_df1',datetime.datetime.now())
    histdata_last_df=stock_sql_obj.query_data(table='histdata_last')
    print('histdata_last_df2',datetime.datetime.now())
    for code_str in codes:
        update_one_hist(code_str, stock_sql_obj,histdata_last_df,update_db)
    deltatime=datetime.datetime.now()-starttime
    print('update duration=',deltatime.days*24*3600+deltatime.seconds)
    print('update completed')

def get_position(broker='yh',user_file='yh.json'):
    user = easytrader.use(broker)
    user.prepare(user_file)
    holding_stocks_df = user.position#['证券代码']  #['code']
    user_balance = user.balance#['证券代码']  #['code']
    account = '36005'
    if user_file== 'yh1.json':
        account = '38736'
    holding_stocks_df['account'] = account
    this_day=datetime.datetime.now()
    date_format='%Y/%m/%d'
    time_format = date_format + ' %X'
    time_str=this_day.strftime(time_format)
    holding_stocks_df['update'] = time_str
    #holding_stocks_df['valid'] = 1
    """
            当前持仓  股份可用     参考市值   参考市价  股份余额    参考盈亏 交易市场   参考成本价 盈亏比例(%)        股东代码  \
            0  6300  6300  24885.0   3.95  6300  343.00   深A   3.896   1.39%  0130010635   
            1   400   400   9900.0  24.75   400  163.00   深A  24.343   1.67%  0130010635   
            2   600   600  15060.0  25.10   600  115.00   深A  24.908   0.77%  0130010635   
            3  1260     0  13041.0  10.35  1260  906.06   沪A   9.631   7.47%  A732980330   
            
                 证券代码  证券名称  买入冻结 卖出冻结  
            0  000932  华菱钢铁     0    0  
            1  000977  浪潮信息     0    0  
            2  300326   凯利泰     0    0  
            3  601009  南京银行     0    0  
    """
    #print(holding_stocks_df)
    return holding_stocks_df,user_balance       

def update_one_stock(symbol,realtime_update=False,dest_dir='C:/hist/day/data/', force_update_from_YH=False):
    """
    运行之前先下载及导出YH历史数据
    """
    """
    :param symbol: string type, stock code
    :param realtime_update: bool type, True for K data force update during trade time 
    :param dest_dir: string type, like csv dir
    :param force_update_from_YH: bool type, force update K data from YH
    :return: Dataframe, history K data for stock
    """
    index_symbol_maps = {'sh':'999999','sz':'399001','zxb':'399005','cyb':'399006',
                     'sh50':'000016','sz300':'399007','zx300':'399008','hs300':'000300'}
    qq_index_symbol_maps = {'sh':'000001','sz':'399001','zxb':'399005','cyb':'399006',
                         'sh50':'000016','sz300':'399007','zx300':'399008','hs300':'000300'}
    FIX_FACTOR = 1.0
    d_format='%Y/%m/%d'
    last_date_str = tt.get_last_trade_date(date_format=d_format)
    latest_date_str = tt.get_latest_trade_date(date_format=d_format)
    #print('last_date_str=',last_date_str)
    #print('latest_date_str=',latest_date_str)
    next_date_str = tt.get_next_trade_date(date_format=d_format)
    #print(next_date_str)
    dest_file_name = dest_dir+ '%s.csv' % symbol
    dest_df = get_raw_hist_df(code_str=symbol)
    file_type='csv'
    RAW_HIST_DIR = "C:/中国银河证券海王星/T0002/export/"
    yh_file_name = RAW_HIST_DIR+symbol+'.'+file_type
    if symbol in index_symbol_maps.keys():
        symbol = index_symbol_maps[symbol]
        dest_file_name = dest_dir+ '%s.csv' % symbol
    if dest_df.empty:
        if symbol in index_symbol_maps.keys():
            symbol = index_symbol_maps[symbol]
        yh_file_name = RAW_HIST_DIR+symbol+'.'+file_type
        #yh_index_df = get_yh_raw_hist_df(code_str=symbol)
        yh_index_df = pd.read_csv(yh_file_name)
        yh_index_df['factor'] = 1.0
        yh_df = yh_index_df.set_index('date')
        yh_df.to_csv(dest_file_name ,encoding='utf-8')
        dest_df = yh_index_df
        #del dest_df['rmb']
        return yh_df
    #print(dest_df)
    dest_df_last_date = dest_df.tail(1).iloc[0]['date']
    #print('dest_df_last_date=',dest_df_last_date)
    quotation_datetime = datetime.datetime.now()
    if dest_df_last_date<latest_date_str:     
        quotation_date = ''
        try:
            quotation_index_df = qq.get_qq_quotations([symbol], ['code','datetime','date','open','high','low','close','volume','amount'])
            quotation_date = quotation_index_df.iloc[0]['date']
            quotation_date = quotation_index_df.iloc[0]['date']
            quotation_datetime = quotation_index_df.iloc[0]['datetime']
            del quotation_index_df['datetime']
            if dest_df_last_date==quotation_date:
                return dest_df
            #quotation_index_df = ts.get_index()
        except:
            time.sleep(3)
            quotation_index_df = qq.get_qq_quotations([symbol], ['code','date','open','high','low','close','volume','amount'])
            quotation_date = quotation_index_df.iloc[0]['date']
            quotation_datetime = quotation_index_df.iloc[0]['datetime']
            del quotation_index_df['datetime']
            if dest_df_last_date==quotation_date:
                return dest_df
        #print('quotation_date=',quotation_date)
        #print(quotation_index_df)
        quotation_index_df['factor'] = 1.0
        quotation_index_df = quotation_index_df[['date','open','high','low','close','volume','amount','factor']]
        #quotation_index_df.iloc[0]['volume'] = 0
        #quotation_index_df.iloc[0]['amount'] = 0
        #print(quotation_index_df)
        #print(quotation_index_df)
        need_to_send_mail = []
        sub = ''
        index_name = symbol
        #table_update_times = self.get_table_update_time()
        
        if quotation_date:
            yh_symbol = symbol
            if symbol in index_symbol_maps.keys():
                yh_symbol = index_symbol_maps[index_name]
            yh_file_name = RAW_HIST_DIR+yh_symbol+'.'+file_type
            #yh_index_df = get_yh_raw_hist_df(code_str=symbol)
            yh_index_df = pd.read_csv(yh_file_name,encoding='GBK')
            yh_index_df['factor'] = FIX_FACTOR
            yh_last_date = yh_index_df.tail(1).iloc[0]['date']
            #print('yh_last_date=',yh_last_date)
            #print( yh_index_df)#.head(len(yh_index_df)-1))
            
            if yh_last_date>dest_df_last_date:  #dest_df_last_date<latest_date_str
                #date_data = self.query_data(table=index_name,fields='date',condition="date>='%s'" % last_date_str)
                #data_len = len(date_data)
                #this_table_update_time = table_update_times[index_name]
                #print('this_table_update_time=', this_table_update_time)
                if yh_last_date<last_date_str: #no update more than two day
                    """需要手动下载银河客户端数据"""
                    print('Need to manual update %s index from YH APP! Please make suere you have sync up YH data' % index_name)
                    need_to_send_mail.append(index_name)
                    sub = '多于两天没有更新指数数据库'
                    content = '%s 数据表更新可能异常' % need_to_send_mail
                    sm.send_mail(sub,content,mail_to_list=None)
                elif yh_last_date==last_date_str: # update by last date
                    """只需要更新当天数据"""
                    realtime_update = tt.is_trade_time_now()
                    if realtime_update:
                        if yh_last_date<latest_date_str:
                            print(' force update %s index' % symbol)
                            yh_index_df = yh_index_df.append(quotation_index_df, ignore_index=True)
                        
                        #elif yh_last_date==latest_date_str:
                        #    print(' delete last update, then force update %s index' % symbol)
                        #    yh_index_df=yh_index_df[:-1]
                        #    yh_index_df = yh_index_df.append(quotation_index_df, ignore_index=True)
                        
                        else:
                            pass
                        #print(yh_index_df)
                    else:
                        pass
                else:# yh_last_date>latest_date_str: #update to  latest date
                    """YH已经更新到今天，要更新盘中获取的当天数据"""
                    print(' %s index updated to %s; not need to update' % (index_name,latest_date_str))
                    """
                    if force_update:
                        print(' force update %s index' % index_name)
                        yh_index_df0 = yh_index_df.head(len(yh_index_df)-1)
                        print(yh_index_df0)
                        yh_index_df = yh_index_df0.append(quotation_index_df, ignore_index=True)
                        print(yh_index_df)
                    else:
                        pass
                    """
                yh_index_df = yh_index_df.set_index('date')
                """
                try:
                    os.remove(file_name)
                    print('Delete and update the csv file')
                except:
                    pass
                """
                yh_index_df.to_csv(dest_file_name ,encoding='utf-8')
            else:
                if force_update_from_YH and yh_last_date==dest_df_last_date:
                    yh_index_df = yh_index_df.set_index('date')
                    yh_index_df.to_csv(dest_file_name ,encoding='utf-8')
                pass
    elif dest_df_last_date==latest_date_str:
        print('No need to update data')
        realtime_update = tt.is_trade_time_now()
        if realtime_update:
            quotation_index_df = qq.get_qq_quotations([symbol], ['code','date','open','high','low','close','volume','amount'])
            #quotation_index_df['factor'] = 1.0
            quotation_index_df = quotation_index_df[['date','open','high','low','close','volume','amount']]#'factor']]
            #print(quotation_index_df)
            print(' force update %s index' % symbol)
            dest_df0 = dest_df
            if dest_df_last_date==latest_date_str:
                dest_df0 = dest_df.head(len(dest_df)-1)
                #dest_df0 = dest_df0[:-1]
            #print(dest_df0)
            dest_df = dest_df0.append(quotation_index_df, ignore_index=True)
            #print(dest_df)
            if quotation_index_df.empty:
                pass
            else:
                yh_index_df = yh_index_df.set_index('date')
                dest_df.to_csv(dest_file_name ,encoding='utf-8')
        else:
            pass
    else:
        pass
    return dest_df

update_one_stock(symbol='999999',dest_dir="C:/中国银河证券海王星/T0002/export/", force_update_from_YH=False)
def update_realtime_k():
    RAW_HIST_DIR = "C:/中国银河证券海王星/T0002/export/"
    update_one_stock(symbol, realtime_update, RAW_HIST_DIR, force_update_from_YH)
    return 

def update_codes_from_YH(codes, realtime_update=False, dest_dir='C:/hist/day/data/', force_update_from_YH=False):
    #index_symbol_maps = {'sh':'999999','sz':'399001','zxb':'399005','cyb':'399006',
    #                 'sh50':'000016','sz300':'399007','zx300':'399008','hs300':'000300'}
    #print(list(index_symbol_maps.keys()))
    #通常为指数和基金从银河的更新
    for symbol in codes: # #list(index_symbol_maps.keys()):
        update_one_stock(symbol, realtime_update, dest_dir, force_update_from_YH)
    return

def get_exit_data(symbol,dest_df,last_date_str):
    df=pd.read_csv('C:/hist/day/temp/%s.csv' % symbol)
    dest_df = get_raw_hist_df(code_str=symbol)
    if dest_df.empty:
        pass
    else:
        dest_df_last_date = dest_df.tail(1).iloc[0]['date']
        if dest_df_last_date==last_date_str:
            exit_price = dest_df.tail(3)
    return

def get_exit_price(hold_codes=['300162'],data_path='C:/中国银河证券海王星/T0002/export/' ):#, has_update_history=False):
    #exit_dict={'300162': {'exit_half':22.5, 'exit_all': 19.0},'002696': {'exit_half':17.10, 'exit_all': 15.60}}
    has_update_history = True
    """
    if not has_update_history:
        easyhistory.init('D', export='csv', path="C:/hist",stock_codes=hold_codes)
        easyhistory.update(path="C:/hist",stock_codes=hold_codes)
        #has_update_history = True
    """
    #his = easyhistory.History(dtype='D', path='C:/hist',codes=hold_codes)
    #data_path = 'C:/hist/day/data/'
    #data_path = 'C:/中国银河证券海王星/T0002/export/' 
    exit_dict = dict()
    his = easyhistory.History(dtype='D', path=data_path, type='csv',codes=hold_codes)
    d_format='%Y/%m/%d'
    last_date_str = tt.get_last_trade_date(date_format=d_format)
    latest_date_str = tt.get_latest_trade_date(date_format=d_format)
    for code in hold_codes:
        #code_hist_df = hist[code].MA(1).tail(3).describe()
        if code=='sh000001' or code=='sh':
            code = '999999'
        if code=='cyb':
            code = '399006'
        exit_data = dict()
        hist_df  =his[code].ROC(1) 
        hist_last_date = hist_df.tail(1).iloc[0].date
        #print('hist_last_date=',hist_last_date)
        tolerance_exit_rate = 0.0
        t_rate = 0.0
        min_close = 0.0
        min_low =0.0
        if hist_last_date<last_date_str:
            hist_df['l_change'] = ((hist_df['low']-hist_df['close'].shift(1))/hist_df['close'].shift(1)).round(3)
            hist_df['h_change'] = ((hist_df['high']-hist_df['close'].shift(1))/hist_df['close'].shift(1)).round(3)
            hist_low_describe = hist_df.tail(60).describe()
            #print(hist_low_describe)
            tolerance_exit_rate = round(hist_low_describe.loc['25%'].l_change,4)
            t_rate = round(hist_low_describe.loc['75%'].h_change,4)
            #print('hist_low_change=',hist_low_change)
            #if hist_low_change< tolerance_exit_rate:
            #tolerance_exit_rate = hist_low_change
            #print('tolerance_exit_rate=',tolerance_exit_rate)
        else:
            hist_df['l_change'] = ((hist_df['low']-hist_df['close'].shift(1))/hist_df['close'].shift(1)).round(3)
            hist_df['h_change'] = ((hist_df['high']-hist_df['close'].shift(1))/hist_df['close'].shift(1)).round(3)
            hist_low_describe = hist_df.tail(60).describe()
            tolerance_exit_rate = round(hist_low_describe.loc['25%'].l_change,4)
            t_rate = round(hist_low_describe.loc['75%'].h_change,4)
            #tolerance_exit_rate = hist_low_change
            #print('tolerance_exit_rate=',tolerance_exit_rate)
            hist_df = hist_df[hist_df.date<=last_date_str]
            describe_df = his[code].MA(1).tail(3).describe()
            min_low =round(describe_df.loc['min'].low, 2)
            min_close = round(round(describe_df.loc['min'].close,2),2)
            max_close = round(describe_df.loc['max'].close,2)
            max_high = round(describe_df.loc['max'].high,2)
        exit_data['exit_half'] = min_close
        exit_data['exit_all'] = min_low
        exit_data['exit_rate'] = tolerance_exit_rate
        exit_data['t_rate'] = t_rate
        exit_dict[code] = exit_data
    #print('exit_dict=%s' % exit_dict)
    return exit_dict

def get_index_exit_data(indexs=['sh','cyb'],yh_index_symbol_maps = {'sh':'999999','sz':'399001','zxb':'399005','cyb':'399006',
                         'sh50':'000016','sz300':'399007','zx300':'399008'}):#['sh','sz','zxb','cyb','sz300','sh50']):
    yh_index_symbol_maps = {'sh':'999999','sz':'399001','zxb':'399005','cyb':'399006',
                         'sh50':'000016','sz300':'399007','zx300':'399008'}#'hs300':'000300'}
    hold_codes = []
    for index in indexs:
        if index in list(yh_index_symbol_maps.keys()):
            yh_code = yh_index_symbol_maps[index]
            hold_codes.append(yh_code)
    index_exit_data = get_exit_price(hold_codes)
    return index_exit_data

def is_system_risk(indexs=['sh','cyb'],index_exit_data=get_index_exit_data(['sh','cyb']),
                   yh_index_symbol_maps = {'sh':'999999','sz':'399001','zxb':'399005','cyb':'399006',
                         'sh50':'000016','sz300':'399007','zx300':'399008'}):
    exit_data =index_exit_data
    if not exit_data:
        exit_data = get_index_exit_data(indexs)
    index_quot = qq.get_qq_quotations(codes=indexs)
    #overlap_index = list(set(list(exit_data.keys())) & set(list(index_quot.keys())))
    if not exit_data or not index_quot:
        return {}
    risk_data = {}
    risk_datas = []
    for index in indexs:
        this_risk = {}
        index_now = index_quot[index]['now']
        index_exit_half = exit_data[yh_index_symbol_maps[index]]['exit_half']
        index_exit_all = exit_data[yh_index_symbol_maps[index]]['exit_all']
        index_exit_rate = exit_data[yh_index_symbol_maps[index]]['exit_rate']
        risk_state = 0
        if index_exit_all==0:
            last_close = index_quot[index]['close']
            index_exit_all = (1+2*index_exit_rate) * last_close
            index_exit_half = (1+index_exit_rate) * last_close
        else:
            pass
        if index_now<index_exit_all:
            risk_state = 1.0
        elif index_now<index_exit_half:
            risk_state = 0.5
        else:
            pass
        if risk_state>0:
            this_risk['index'] = index
            this_risk['index_value'] = index_now
            this_risk['index_state'] = risk_state
            this_risk['date_time'] = datetime.datetime.now()
            risk_datas.append([])
        risk_data[index] = this_risk
    print(risk_data)
    return risk_data

def get_hold_stock_statistics(hold_stocks= ['000007', '000932', '601009', '150288', '300431', '002362', '002405', '600570', '603398'],
                              stock_dir='C:/hist/day/temp/'):
    if len(hold_stocks)<1:
            return False
    first_stock = hold_stocks[0]
    statistics_df = pd.read_csv(stock_dir + '%s.csv' % first_stock).tail(1)
    statistics_df['code'] = first_stock
    if len(hold_stocks)>=2:
        hold_stocks.pop(0)
        for stock in hold_stocks:
                temp_hold_df = pd.read_csv(stock_dir + '%s.csv' % stock).tail(1)
                temp_hold_df['code'] = stock
                statistics_df = statistics_df.append(temp_hold_df)
    statistics_df = statistics_df.set_index('code')
    return statistics_df
        
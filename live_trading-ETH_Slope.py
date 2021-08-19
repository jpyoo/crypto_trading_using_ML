#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import pandas as pd
import time
import datetime
import json
import krakenex
import requests
import cryptocompare
from keras.models import load_model
import schedule

def post_message(token, channel, text):
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )
    print(response)

myToken = "xoxb-2036823281344-2036860223840-vZRO0TK4IX9LF0cwASdoc6pk"
api = krakenex.API()
api.load_key('kraken.key')

cryptocompare.cryptocompare._set_api_key_parameter('81b3a3bca41babe483f4a8df1150d9c6e26fa9371e64f0d8f6df39843687e47f')


# In[2]:


model5 = load_model('ETH_model5_wavenet_12bat_20epochs_kernal_3_NotScaled_Slope.h5')


# In[7]:


def Get_Signal():
    candles = cryptocompare.get_historical_price_hour(
            'ETH', currency='USD', limit=500, toTs=datetime.datetime.now()
        )

    # create lists to hold our different data elements
    open_dataset = pd.DataFrame(candles)
    dataset = np.array(open_dataset[['open','close','volumefrom']])

    open_data_slope = []
    close_data_slope = []
    volumes_slope = []
    for i in range(1,dataset.shape[0]-1):
        open_data_slope.append(float(dataset[i,0])-float(dataset[i-1,0]))
        close_data_slope.append(dataset[i,1]-dataset[i-1,1])
        volumes_slope.append(dataset[i,2]-dataset[i-1,2])

    train_data = np.array([open_data_slope,close_data_slope,volumes_slope]).T

    combine = 11

    x_train = []
    for i in range(combine, train_data.shape[0]-1):
        x_train.append(train_data[i-combine:i, :])
    x_train = np.array(x_train)

    y_hat5 = model5.predict(x_train)

    signal = None
    if y_hat5[-1,-1,1] > 0:
        signal = 'Buy'
    else:
        signal = 'Sell'
    return signal


# In[8]:


def api_limit_order(order_type, want_price, volume):
    response = api.query_private('AddOrder',
                                    {'pair': 'ETHUSD',
                                     'type': order_type,
                                     'ordertype': 'limit',
                                     'price': format(float(want_price), '.2f'),
                                     'volume': volume,
                                     'close[ordertype]': 'limit',
                                     'close[price]': format(float(want_price) * 1.006, '.2f')
                                    }
                                )
    return response

def api_limit_order3(order_type, want_price, volume):
    response = api.query_private('AddOrder',
                                    {'pair': 'ETHUSD',
                                     'type': order_type,
                                     'ordertype': 'limit',
                                     'price': format(float(want_price), '.2f'),
                                     'volume': volume
                                     }
                                )
    return response

def api_cancel_all_order(open_order):
    for x in list(open_order):
        api.query_private('CancelOrder',
            {
                'txid': x
            }
        )

def api_cancel_order(open_order, list_position):
    x =  list(open_order)[list_position]
    api.query_private('CancelOrder',
        {
            'txid': x
        }
    )

def Clean_Old_Order(data):
    if len(data.open_order) != 0:
        for i in range(len(data.open_order)):
            if int(data.open_order[list(data.open_order)[i]]['opentm']) < int(time.time()) - 60*60*1:
                api_cancel_order(data.open_order,i)


# In[9]:


class Trading_Data():
    def __init__(self, price, volume, open_order, order_type, bank):
        self.price = float(price)
        self.volume = float(volume)
        self.open_order = open_order
        self.order_type = order_type
        self.bank = float(bank)


# In[10]:


def Get_Data():
    price = np.array(api.query_public('OHLC', data = {'pair': 'ETHUSD'})['result']['XETHZUSD'])[-1,4]
    volume = float(api.query_private('Balance')['result']['XETH'])
    bank = float(api.query_private('Balance')['result']['ZUSD'])
    open_order = api.query_private('OpenOrders')['result']['open']
    if len(open_order) == 0:
        order_type = 'None'
    else:
        order_type = open_order[list(open_order)[-1]]['descr']['type']

    return Trading_Data(price, volume, open_order, order_type, bank)

def Get_Status(data):
    Clean_Old_Order(data)

    #Holding Crypto
    if data.volume*data.price > data.bank:
        if len(data.open_order) == 0:
            post_message(myToken,"#notify","No order pending, Holding Crypto")
            ping = 111

        elif len(data.open_order) != 0:
            post_message(myToken,"#notify","Open order pending, Holding Crypto")
            if data.order_type == 'buy':
                post_message(myToken,"#notify","Type: Buy")
                ping = 444
            elif data.order_type == 'sell':
                post_message(myToken,"#notify","Type: Sell")
                ping = 777
            else: ping = 'error1'
        else: ping = 'error3'

    #Holding Cash
    elif data.volume*data.price < data.bank:
        if len(data.open_order) == 0:
            post_message(myToken,"#notify","No order pending, Holding Cash")
            ping = 0

        elif len(data.open_order) != 0:
            post_message(myToken,"#notify","Open order pending, Holding Cash")
            if data.order_type == 'buy':
                post_message(myToken,"#notify","Type: Buy")
                ping = 77
            elif data.order_type == 'sell':
                post_message(myToken,"#notify","Type: Sell")
                ping = 44
            else: ping = 'error2'
        else: ping = 'error4'

    return ping


# In[13]:


def live_trading():
    #trading strategy
    data = Get_Data()
    status = Get_Status(data)
    signal = Get_Signal()

    if signal == 'Buy':
        if status == 0:
            api_limit_order3('buy', data.price, format(data.bank / data.price, '.8f'))
        elif status == 44:
            api_cancel_all_order(data.open_order)
            api_limit_order3('buy', data.price, format(data.bank / data.price, '.8f'))
        elif status == 77:
            api_cancel_all_order(data.open_order)
            api_limit_order3('buy', data.price, format(data.bank / data.price, '.8f'))
        elif status == 111:
            api_limit_order3('buy', data.price, format(data.bank / data.price, '.8f'))
        elif status == 444:
            api_cancel_all_order(data.open_order)
            api_limit_order3('buy', data.price, format(data.bank / data.price, '.8f'))
        elif status == 777:
            api_cancel_all_order(data.open_order)
            api_limit_order3('buy', data.price, format(data.bank / data.price, '.8f'))
        else: post_message(myToken,"#notify","Error6")

    elif signal == 'Sell':
        if status == 0:
            api_limit_order3('sell', data.price, format(data.volume, '.8f'))
        elif status == 44:
            api_cancel_all_order(data.open_order)
            api_limit_order3('sell', data.price, format(data.volume, '.8f'))
        elif status == 77:
            api_cancel_all_order(data.open_order)
            api_limit_order3('sell', data.price, format(data.volume, '.8f'))
        elif status == 111:
            api_limit_order3('sell', data.price, format(data.volume, '.8f'))
        elif status == 444:
            api_cancel_all_order(data.open_order)
            api_limit_order3('sell', data.price, format(data.volume, '.8f'))
        elif status == 777:
            api_cancel_all_order(data.open_order)
            api_limit_order3('sell', data.price, format(data.volume, '.8f'))
        else: post_message(myToken,"#notify","Error5")

    else: post_message(myToken,"#notify","Error7")
    post_message(myToken,"#notify",str(signal))
    post_message(myToken,"#notify",str(status))


# In[14]:
#run every hour at x:59
schedule.every().hour.at(":59").do(live_trading)
while True:
    schedule.run_pending()
    time.sleep(60)



# In[ ]:

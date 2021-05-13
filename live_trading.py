#!/usr/bin/env python
# coding: utf-8

# In[180]:


from keras.models import load_model
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import time
import datetime
import cryptocompare
import json
import krakenex
import requests

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


# In[181]:


def last_time_step_mse(Y_true, Y_pred):
    return keras.metrics.mean_squared_error(Y_true[:,-1], Y_pred[:,-1])
model1 = load_model('model1_LSTM_32bat_20epochs_Close.h5')
model4 = load_model('model4_GRU_32bat_20epochs_Close.h5')
model5 = load_model('model5_wavenet_32bat_20epochs_Close.h5', custom_objects={'last_time_step_mse': last_time_step_mse})
model6 = load_model('model6_GRU_32bat_20epochs_m2m_Close.h5', custom_objects={'last_time_step_mse': last_time_step_mse})


# In[182]:


lev = '3'
def brief(y_hat):
    return float(float(y_hat[y_hat.shape[0]-2,-1]) -float(y_hat[y_hat.shape[0]-1,-1]))
def brief10(y_hat):
    return float(float(y_hat[y_hat.shape[0]-1,y_hat.shape[1]-1,-1]) - float(y_hat[y_hat.shape[0]-1,y_hat.shape[1]-1,0]))
def match10(y_hat):
    return float(float(y_hat[y_hat.shape[0]-1,y_hat.shape[1]-1,1]) - float(y_hat[y_hat.shape[0]-1,y_hat.shape[1]-1,0]))

def api_buy_order(order_type, want_price, volume, leverage):
    response = api.query_private('AddOrder',
                                    {'pair': 'XBTUSD',
                                     'type': order_type,
                                     'ordertype': 'limit',
                                     'price': want_price,
                                     'volume': volume,
                                     'leverage' : leverage,
                                     'close[ordertype]': 'limit',
                                     'close[price]': format(float(want_price) * 1.005, '.1f')
                                    }
                                )
    return response

def api_sell_order(order_type, want_price, volume, leverage):
    response = api.query_private('AddOrder',
                                    {'pair': 'XBTUSD',
                                     'type': order_type,
                                     'ordertype': 'limit',
                                     'price': want_price,
                                     'volume': volume,
                                     'leverage' : leverage,
                                     'close[ordertype]': 'limit',
                                     'close[price]': format(float(want_price) * 0.995, '.1f')
                                    }
                                )
    return response

def api_clear_position(order_type, want_price, volume, leverage):
    response = api.query_private('AddOrder',
                                    {'pair': 'XBTUSD',
                                     'type': order_type,
                                     'ordertype': 'limit',
                                     'price': want_price,
                                     'volume': volume,
                                     'leverage' : leverage
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


# In[183]:


#get trading signals with live 1500m data
def Get_Signal(min_limit = 1500):
    candles = cryptocompare.get_historical_price_minute(
            'BTC', currency='USD', limit=min_limit, toTs=datetime.datetime.now()
        )

    # create lists to hold our different data elements
    close_data = []
    dates = []
    # convert from the Shrimpy candlesticks to the plotly graph objects format
    for candle in candles:
        close_data.append(candle['close'])
        dates.append(candle['time'])

    close_data = np.array(close_data)

    # Normalise features
    sc = MinMaxScaler(feature_range = (0, 1))
    training_set_scaled = sc.fit_transform(close_data.reshape(-1,1))
    combine = 60

    x_train = []
    y_train = []
    for i in range(combine, training_set_scaled.shape[0]-1):
        x_train.append(training_set_scaled[i-combine:i, :])
        y_train.append(training_set_scaled[i+1, :])

    x_train, y_train = np.array(x_train), np.array(y_train)

    x_train_m2m = x_train[:,:combine-10,:]
    y_train_m2m = np.empty((y_train.shape[0], combine-10, 10))
    for step_ahead in range(1,10+1):
        y_train_m2m[:,:,step_ahead-1] = x_train[:,step_ahead:step_ahead+combine-10,0]

    y_hat1 = model1.predict(x_train)
    y_hat4 = model4.predict(x_train)
    y_hat5 = model5.predict(x_train_m2m)
    y_hat6 = model6.predict(x_train_m2m)

    #trading signals
    # if brief10(y_hat5)> 0 and brief10(y_hat6) > 0 and match10(y_hat5)> 0 and match10(y_hat6) > 0 and brief(y_hat1) > 0 and brief(y_hat4) > 0 :
    #     signal = 1 #buying
    # elif brief10(y_hat5)< 0 and brief10(y_hat6) < 0 and match10(y_hat5)< 0 and match10(y_hat6) < 0 and brief(y_hat1) < 0 and brief(y_hat4) < 0 :
    #     signal = 2 #buying
    if brief10(y_hat5) < 0 and brief10(y_hat6) < 0 :
        signal = 1 #buying exit
    elif brief10(y_hat5) > 0 and brief10(y_hat6) > 0 :
        signal = 2 #sell exit
    else:
        signal = 0 #no signal
    return signal


# In[184]:


class Trading_Data():
    def __init__(self, price, volume, open_position, position_type, position_volume, open_order, order_type):
        self.price = price
        self.volume = volume
        self.open_position = open_position
        self.position_type = position_type
        self.position_volume = position_volume
        self.open_order = open_order
        self.order_type = order_type


# In[185]:


def Get_Data():
    price = np.array(api.query_public('OHLC', data = {'pair': 'XBTUSD'})['result']['XXBTZUSD'])[-1,4]
    volume = float(api.query_private('Balance')['result']['XXBT'])

    open_position = api.query_private('OpenPositions')['result']
    if len(open_position) == 0:
        position_volume = 0
        position_type = 'None'
    else:
        position_volume = 0
        for x in open_position:
            position_volume += float(open_position[x]['vol'])
        position_type = open_position[list(open_position)[-1]]['type']

    open_order = api.query_private('OpenOrders')['result']['open']
    if len(open_order) == 0:
        order_type = 'None'
    else:
        order_type = open_order[list(open_order)[-1]]['descr']['type']

    return Trading_Data(price, volume, open_position, position_type, position_volume, open_order, order_type)

def Get_Status(data):
    if len(data.open_order) == 0 and len(data.open_position) == 0:
        ping = 0

    elif len(data.open_order) == 0 and len(data.open_position) != 0:
        if data.position_type == 'buy':
            ping = 1
        elif data.position_type == 'sell':
            ping = 2
        else: ping = 'error1'

    elif len(data.open_order) != 0 and len(data.open_position) == 0:
        if int(data.open_order[list(data.open_order)[-1]]['opentm']) < int(time.time()) - 600:
            api_cancel_all_order(data.open_order)
            ping = 0
        else:
            if data.order_type == 'buy':
                ping = 100
            elif data.order_type == 'sell':
                ping = 200
            else: ping = 'error2'

    elif len(data.open_order) != 0 and len(data.open_position) != 0:
            if data.position_type == 'buy':
                if data.order_type == 'sell':
                    ping = 88
                elif data.order_type == 'buy':
                    ping = 300
            elif data.position_type == 'sell':
                if data.order_type == 'sell':
                    ping = 400
                elif data.order_type == 'buy':
                    ping = 99
            else: ping = 'error3'

    else: ping = 'error4'

    return ping


# In[186]:


def live_trading(signal):
    #trading strategy
    data = Get_Data()
    status = Get_Status(data)
    #empty
    if status == 0:
        if signal == 0:
            pass
        elif signal == 1:
            api_buy_order('buy', str(data.price), format(data.volume, '.8f'), lev)
        elif signal == 2:
            api_sell_order('sell', str(data.price), format(data.volume, '.8f'), lev)
        # elif signal == 3:
        #     pass
        # elif signal == 4:
        #     pass


    #existing buy position
    elif status == 1:
        if signal == 0:
            pass
        elif signal == 1:
            pass
        elif signal == 2:
            api_clear_position('sell', str(data.price), format(data.position_volume, '.8f'), lev)
        # elif signal == 3:
        #     api_limit_order('sell', str(data.price), format(data.position_volume, '.8f'), lev)
        # elif signal == 4:
        #     pass

    #existing sell position
    elif status == 2:
        if signal == 0:
            pass
        elif signal == 1:
            api_clear_position('buy', str(data.price), format(data.position_volume, '.8f'), lev)
        elif signal == 2:
            pass
        # elif signal == 3:
        #     pass
        # elif signal == 4:
        #     api_limit_order('buy', str(data.price), format(data.position_volume, '.8f'), lev)

    elif status == 100:
        if int(data.open_order[list(data.open_order)[0]]['opentm']) < int(time.time()) - 600:
            api_cancel_all_order(data.open_order)
        if signal == 0:
            pass
        elif signal == 1:
            api_cancel_all_order(data.open_order)
            api_buy_order('buy', str(data.price), format(data.position_volume, '.8f'), lev)
        elif signal == 2:
            api_cancel_all_order(data.open_order)
        # elif signal == 3:
        #     api_cancel_all_order(data.open_order)
        # elif signal == 4:
        #     pass

    elif status == 200:
        if int(data.open_order[list(data.open_order)[0]]['opentm']) < int(time.time()) - 600:
            api_cancel_all_order(data.open_order)
        if signal == 0:
            pass
        elif signal == 2:
            api_cancel_all_order(data.open_order)
            api_sell_order('sell', str(data.price), format(data.position_volume, '.8f'), lev)
        elif signal == 1:
            api_cancel_all_order(data.open_order)
        # elif signal == 3:
        #     pass
        # elif signal == 4:
        #     api_cancel_all_order(data.open_order)
    elif status == 300:
        if signal == 0:
            pass
        elif signal == 2:
            api_cancel_all_order(data.open_order)
            api_clear_position('sell', str(data.price), format(data.position_volume, '.8f'), lev)
        elif signal == 1:
            api_cancel_all_order(data.open_order)
            api_buy_order('buy', str(data.price), format(data.position_volume, '.8f'), lev)
        # elif signal == 3:
        #     api_cancel_all_order(data.open_order)
        #     api_limit_order('sell', str(data.price), format(data.position_volume, '.8f'), lev)
        # elif signal == 4:
        #     pass
    elif status == 400:
        if signal == 0:
            pass
        elif signal == 2:
            api_cancel_all_order(data.open_order)
            api_sell_order('sell', str(data.price), format(data.position_volume, '.8f'), lev)
        elif signal == 1:
            api_cancel_all_order(data.open_order)
            api_clear_position('buy', str(data.price), format(data.position_volume, '.8f'), lev)
        # elif signal == 3:
        #     pass
        # elif signal == 4:
        #     api_cancel_all_order(data.open_order)
        #     api_limit_order('sell', str(data.price), format(data.position_volume, '.8f'), lev)
    elif status == 88:
        if int(data.open_order[list(data.open_order)[0]]['opentm']) < int(time.time()) - 600:
            api_cancel_all_order(data.open_order)
            api_clear_position('sell', str(data.price), format(data.position_volume, '.8f'), lev)
        else:
            if signal == 0:
                pass
            elif signal == 2:
                api_cancel_all_order(data.open_order)
                api_clear_position('sell', str(data.price), format(data.position_volume, '.8f'), lev)
            elif signal == 1:
                api_cancel_all_order(data.open_order)
            # elif signal == 3:
            #     api_cancel_all_order(data.open_order)
            #     api_limit_order('sell', str(data.price), format(data.position_volume, '.8f'), lev)
            # elif signal == 4:
            #     pass
    elif status == 99:
        if int(data.open_order[list(data.open_order)[0]]['opentm']) < int(time.time()) - 600:
            api_cancel_all_order(data.open_order)
            api_clear_position('buy', str(data.price), format(data.position_volume, '.8f'), lev)
        else:
            if signal == 0:
                pass
            elif signal == 2:
                api_cancel_all_order(data.open_order)
            elif signal == 1:
                api_cancel_all_order(data.open_order)
                api_clear_position('sell', str(data.price), format(data.position_volume, '.8f'), lev)
            # elif signal == 3:
            #     pass
            # elif signal == 4:
            #     api_cancel_all_order(data.open_order)
            #     api_limit_order('sell', str(data.price), format(data.position_volume, '.8f'), lev)
    else:
        pass

    return status


# In[ ]:


req_data = {'docalcs': 'true'}

while True:
    sig = Get_Signal(1500)
    s = live_trading(sig)

    # Send a message to #general channel
    slacker_msg = "Last Run time : " + str(datetime.datetime.now()) + "\nStatus : "+str(s)+ " Signal : "+str(sig)
    post_message(myToken,"#notify",slacker_msg)
    time.sleep(60)


# In[ ]:

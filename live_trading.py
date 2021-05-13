import numpy as np
import time
import datetime
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

lev = '3'

def api_limit_order(order_type, want_price, volume, leverage):
    response = api.query_private('AddOrder',
                                    {'pair': 'ETHUSD',
                                     'type': order_type,
                                     'ordertype': 'limit',
                                     'price': format(float(want_price)*0.99, '.2f'),
                                     'volume': volume,
                                     'leverage' : leverage,
                                     'close[ordertype]': 'limit',
                                     'close[price]': format(float(want_price) * 1.005, '.2f')
                                    }
                                )
    return response

def api_limit_order2(order_type, want_price, volume, leverage):
    response = api.query_private('AddOrder',
                                    {'pair': 'ETHUSD',
                                     'type': order_type,
                                     'ordertype': 'limit',
                                     'price': format(want_price, '.2f'),
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

def api_cancel_last_order(open_order):
    x =  list(open_order)[-1]
    api.query_private('CancelOrder',
        {
            'txid': x
        }
    )

class Trading_Data():
    def __init__(self, price, volume, open_position, position_type, position_volume, open_order, order_type, position_price):
        self.price = price
        self.volume = volume
        self.open_position = open_position
        self.position_type = position_type
        self.position_volume = position_volume
        self.open_order = open_order
        self.order_type = order_type
        self.position_price = position_price

def Get_Price():
    price = np.array(api.query_public('OHLC', data = {'pair': 'ETHUSD'})['result']['XETHZUSD'])[-1,5]
    return float(price)
# Get Data from Kraken API
def Get_Data():
    price = np.array(api.query_public('OHLC', data = {'pair': 'ETHUSD'})['result']['XETHZUSD'])[-1,5]
    volume = float(api.query_private('Balance')['result']['XETH'])*int(lev)

    open_position = api.query_private('OpenPositions')['result']
    if len(open_position) == 0:
        position_volume = 0
        position_type = 'None'
        position_price = '0'
    else:
        position_volume = 0
        for x in open_position:
            position_volume += float(open_position[x]['vol'])
        position_type = open_position[list(open_position)[-1]]['type']
        position_price = format(float(open_position[list(open_position)[0]]['cost'])/float(open_position[list(open_position)[0]]['vol']),'.2f')

    open_order = api.query_private('OpenOrders')['result']['open']
    if len(open_order) == 0:
        order_type = 'None'
    else:
        order_type = open_order[list(open_order)[-1]]['descr']['type']

    return Trading_Data(price, volume, open_position, position_type, position_volume, open_order, order_type, position_price)

#Check older than 3 hours orders and cancel them
def Clean_Old_Order(data):
    if len(data.open_order) != 0 and len(data.open_position) == 0:
        if int(data.open_order[list(data.open_order)[-1]]['opentm']) < int(time.time()) - (60*180):
            api_cancel_all_order(data.open_order)

    if len(data.open_order) == 2 and len(data.open_position) == 1:
        if int(data.open_order[list(data.open_order)[-1]]['opentm']) < int(time.time()) - (60*180):
            api_cancel_last_order(data.open_order)

#Get status of the trading, such as open positions, open orders and return ping status
def Get_Status(data):
    if len(data.open_order) == 0 and len(data.open_position) == 0:
        ping = 0
    elif len(data.open_position) == 1 and float(data.position_price) < float(data.price)*0.95:
        ping = 21

    elif len(data.open_order) == 0 and len(data.open_position) != 0:
        if data.position_type == 'buy':
            ping = 1
        elif data.position_type == 'sell':
            ping = 2
        else: ping = 'error1'

    elif len(data.open_order) != 0 and len(data.open_position) == 0:
        if data.order_type == 'buy':
            ping = 44
        elif data.order_type == 'sell':
            ping = 55
        else: ping = 'error2'

    elif len(data.open_order) != 0 and len(data.open_position) != 0:
            if data.position_type == 'buy':
                if data.order_type == 'sell':
                    ping = 88
                elif data.order_type == 'buy':
                    ping = 66
            elif data.position_type == 'sell':
                if data.order_type == 'sell':
                    ping = 77
                elif data.order_type == 'buy':
                    ping = 99
            else: ping = 'error3'

    else: ping = 'error4'

    return ping

#Get data, clean old orders and Place orders based on current status
def live_trading():
    data = Get_Data()
    Clean_Old_Order(data)
    status = Get_Status(data)
    if status == 0:
        post_message(myToken,"#notify","Time now : " + str(datetime.datetime.now()) + "Ready to Buy in 1 hour")
        time.sleep(60*60*1)
        price = Get_Price()
        api_limit_order('buy', str(price), format(data.volume/2, '.8f'), lev)
    if status == 21:
        post_message(myToken,"#notify","Second order activated")
        price = Get_Price()
        api_limit_order2('buy', str(price*0.98), format(data.volume/2, '.8f'), lev)
        api_limit_order2('sell', str(price*1.02), format(data.position_volume, '.8f'), lev)

    return status

req_data = {'docalcs': 'true'}

#run live trading every minute
while True:
    s = live_trading()
    # Send a message to #general channel
    slacker_msg = "Pinging"
    post_message(myToken,"#notify",slacker_msg)
    time.sleep(60)

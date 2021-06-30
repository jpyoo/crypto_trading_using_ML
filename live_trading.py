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

def api_limit_order(order_type, want_price, volume):
    response = api.query_private('AddOrder',
                                    {'pair': 'ETHUSD',
                                     'type': order_type,
                                     'ordertype': 'limit',
                                     'price': format(float(want_price)*0.99, '.2f'),
                                     'volume': volume,
                                     'close[ordertype]': 'limit',
                                     'close[price]': format(float(want_price) * 1.005, '.2f')
                                    }
                                )
    return response

def api_limit_order2(order_type, want_price, volume, op):
    response = api.query_private('AddOrder',
                                    {'pair': 'ETHUSD',
                                     'type': order_type,
                                     'ordertype': 'limit',
                                     'price': format(float(want_price), '.2f'),
                                     'volume': volume,
                                     'close[ordertype]': 'limit',
                                     'close[price]': format(float(op), '.2f')
                                    }
                                )
    return response

def api_limit_order3(order_type, want_price, volume):
    response = api.query_private('AddOrder',
                                    {'pair': 'ETHUSD',
                                     'type': order_type,
                                     'ordertype': 'limit',
                                     'price': format(want_price, '.2f'),
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

class Trading_Data():
    def __init__(self, price, volume, open_position, position_type, position_volume, open_order, order_type, position_price, order_price, order_price2):
        self.price = float(price)
        self.volume = float(volume)
        self.open_position = open_position
        self.position_type = position_type
        self.position_volume = float(position_volume)
        self.open_order = open_order
        self.order_type = order_type
        self.position_price = float(position_price)
        self.order_price = float(order_price)
        self.order_price2 = float(order_price2)

# Get Data from Kraken API
def Get_Data():
    price = float(api.query_public('OHLC', data = {'pair': 'ETHUSD'})['result']['XETHZUSD'][-1][4])
    time.sleep(1)
    volume = float(api.query_private('Balance')['result']['XETH'])
    time.sleep(1)
    open_position = api.query_private('OpenPositions')['result']
    time.sleep(1)
    if len(open_position) == 0:
        position_type = 'None'
        position_price = '0'
        position_volume = '0'
    else:
        position_volume = open_position[list(open_position)[0]]['vol']
        position_type = open_position[list(open_position)[-1]]['type']
        position_price = format(float(open_position[list(open_position)[0]]['cost'])/float(open_position[list(open_position)[0]]['vol']),'.2f')

    open_order = api.query_private('OpenOrders')['result']['open']
    if len(open_order) == 0:
        order_type = 'None'
        order_price = '0'
        order_price2 = '0'
    elif len(open_order) == 1:
        order_type = open_order[list(open_order)[-1]]['descr']['type']
        order_price = open_order[list(open_order)[0]]['descr']['price']
        order_price2 = '0'
    elif len(open_order) == 2:
            order_type = open_order[list(open_order)[-1]]['descr']['type']
            order_price = open_order[list(open_order)[0]]['descr']['price']
            order_price2 = open_order[list(open_order)[1]]['descr']['price']

    return Trading_Data(price, volume, open_position, position_type, position_volume, open_order, order_type, position_price, order_price, order_price2)

#Check older than 3 hours orders and cancel them
def Clean_Old_Order(data):
    if len(data.open_order) != 0 and len(data.open_position) == 0:
        post_message(myToken,"#notify","Open order pending")
        if int(data.open_order[list(data.open_order)[-1]]['opentm']) < int(time.time()) - (60*180):
            api_cancel_order(data.open_order,0)

    if len(data.open_order) == 2 and len(data.open_position) == 1:
        post_message(myToken,"#notify","Open order and Open position pending")
        if int(data.open_order[list(data.open_order)[-1]]['opentm']) < int(time.time()) - (60*180):
            api_cancel_order(data.open_order,-1)

#Get status of the trading, such as open positions, open orders and return ping status
def Get_Status(data):
    if len(data.open_order) == 0 and len(data.open_position) == 0:
        post_message(myToken,"#notify","Time now : " + str(datetime.datetime.now()) + "Ready to Buy")
        time.sleep(60*30)
        ping = 0
    elif len(data.open_position) == 1 and len(data.open_order) == 1 and float(data.position_price) < float(data.price)*0.95:
        post_message(myToken,"#notify","Second order activated")
        ping = 21
    elif len(data.open_position) == 2 and len(data.open_order) == 2 and data.order_price == data.order_price2:
        post_message(myToken,"#notify","Third order activated")
        ping = 22
    elif data.order_price > data.price * 2:
        post_message(myToken,"#notify","Exit activated")
        ping = 99

    else: ping = 'else'

    return ping

#Get data, clean old orders and Place orders based on current status
def live_trading():
    data = Get_Data()
    Clean_Old_Order(data)
    status = Get_Status(data)
    if status == 0:
        api_limit_order('buy', str(data.price), format(data.volume/2, '.8f'))
        post_message(myToken,"#notify","Initiated Position Opening Order")
    if status == 21:
        api_limit_order2('buy', data.price*0.98, format(data.volume/2, '.8f'), data.order_price)
        post_message(myToken,"#notify","Initiated Loss control, second order placed.")
    if status == 22:
        api_cancel_order(data.open_order,0)
        post_message(myToken,"#notify","Cancelled First Order")
        api_limit_order3('sell', data.price*1.02, format(data.position_volume, '.8f'))
        post_message(myToken,"#notify","Placed new Order,")
    if status == 99:
        api_cancel_all_order(data.open_order)
        post_message(myToken,"#notify","Cancelled ALL Order")
        api_limit_order3('sell', data.price, format(data.position_volume, '.8f'))
        post_message(myToken,"#notify","Sell Market")

    return status

req_data = {'docalcs': 'true'}

#run live trading every minute
s = live_trading()
# Send a message to #general channel
slacker_msg = "Pinging"
post_message(myToken,"#notify",slacker_msg)

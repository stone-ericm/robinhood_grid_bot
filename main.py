'''
Script to run a grid bot on Robinhood trading Etherium
'''

import robin_stocks.robinhood as r
import pyotp
import time
import pandas as pd

# local file with login information
from credentials import username, password, auth_key

totp = pyotp.TOTP(auth_key).now()
login = r.login(username, password, mfa_code=totp)

my_coins = r.crypto.get_crypto_positions()
# [0]['cost_bases'][0]
# owned_eth = my_coins['direct_quantity']
# wallet = .3    #amount in etherium
grid_transaction_size = .05

# starting with entire wallet in etherium
# 5 grids
grids = 6
# grid size is half a percent


def init():
    # gage opening price
    opening_price = float(r.crypto.get_crypto_quote('ETH', info='ask_price'))
    # print(opening_price)
    prev_price = opening_price

    order_details = pd.DataFrame()

    for each in range(grids):
        grid_price = prev_price * 1.005
        order_details = pd.concat(order_details, r.orders.order_sell_crypto_limit("ETH", grid_transaction_size, round(grid_price)))
    return(order_details)

def create_order(type, previous_price, order_details):

    next_order_price = previous_price * 1.005
    if type == 'sell':
        response = r.orders.order_sell_crypto_limit("ETH", grid_transaction_size, round(next_order_price))
    elif type =='buy':
        response = r.orders.order_buy_crypto_limit("ETH", grid_transaction_size, round(next_order_price))

    order_details = pd.concat(order_details, response)
    if response['state'] != 'confirmed':
        order_details.to_csv('log')
        raise RuntimeError(f'Failed to create {type} order')

    return(order_details)

def monitor(order_details):
    time.sleep(5)
    open_orders = order_details[order_details['state'] == 'confirmed']
    # open_sales = open_orders.value_counts()
    for order in open_orders:
        response = r.orders.get_crypto_order_info(order['id'])
        if response['state'] == 'filled':
            order_details.iloc[order.index] = response
            if order['side'] == 'sell':
                # place next sell order
                create_order('sell', open_orders['price'].max(), order_details)
                # next_order_price = open_orders['price'].max() * 1.005
                # info = r.orders.order_sell_crypto_limit("ETH", grid_transaction_size, round(next_order_price))
                # order_details = pd.concat(order_details, info)

                # cancel lowest buy order
                order_to_cancel = open_orders.iloc[open_orders['price'].idxmin()]['id']
                response = r.orders.cancel_crypto_order(order_to_cancel)
                order_details.iloc[order_to_cancel.index] = response

                if response['state'] != 'canceled':
                    order_details.to_csv('log')
                    raise RuntimeError("Lowest buy order failed to cancel")
                else:
                    # open new buy order


#
# print(order_info)
# order_id = '62148575-4fdd-4237-aec8-2c7bfdca6b24'
# 'c9e8e6ae-d9fe-4d96-8baa-3ff7e63b4120'

print(r.orders.get_crypto_order_info(order_id))

# 5 limit buys are set
# next we need to check to see if


# set limit buy at first_grid_price

# create 5 sell points



# print(r.crypto.get_crypto_info('ETH'))

# print(r.crypto.get_crypto_quote('ETH', info='ask_price'))

# print(my_coins)



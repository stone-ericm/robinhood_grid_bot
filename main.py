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
    opening_price = float(r.crypto.get_crypto_quote('ETH', info='mark_price'))
    # print(opening_price)
    prev_price = opening_price

    order_details = pd.DataFrame()

    for each in range(grids):
        grid_price = prev_price * 1.005
        order_details = pd.concat([order_details,
                                  pd.DataFrame([pd.Series(r.orders.order_sell_crypto_limit("ETH", grid_transaction_size, round(grid_price)))])])
        # if 'account_id' not in order_details.columns:
        #     order_details = order_details.T
        # print(order_details.head(2))
        prev_price = grid_price
    return (monitor(order_details))


def create_order(type, previous_price, order_details):
    next_order_price = previous_price * 1.005
    if type == 'sell':
        response = r.orders.order_sell_crypto_limit("ETH", grid_transaction_size, round(next_order_price))
    elif type == 'buy':
        response = r.orders.order_buy_crypto_limit("ETH", grid_transaction_size, round(next_order_price))

    order_details = pd.concat([order_details, pd.DataFrame([response])])
    if response['state'] != 'confirmed':
        order_details.to_csv('log')
        r.orders.cancel_all_crypto_orders()
        raise RuntimeError(f'Failed to create {type} order')

    return (order_details)


def monitor(order_details, prior_price=0):
    while True:
        try:
            time.sleep(20)
            open_orders = order_details[order_details['state'] != 'filled']
            open_orders['price'] = open_orders['price'].apply(lambda x: round(x, 2))
            print(open_orders[['side', 'price']])
            # open_sales = open_orders.value_counts()

            for index, order in open_orders.iterrows():
                response = r.orders.get_crypto_order_info(order['id'])
                if response['state'] == 'filled':
                    order_details.iloc[order.index] = response
                    if order['side'] == 'sell':
                        print(f"Sale at {order['price']}")
                        # place next sell order
                        order_details = create_order('sell', open_orders['price'].max(), order_details)

                        # cancel lowest buy order
                        order_to_cancel = open_orders.iloc[open_orders['price'].idxmin()]['id']
                        response = r.orders.cancel_crypto_order(order_to_cancel)
                        order_details.iloc[order_to_cancel.index] = response

                        if response['state'] != 'canceled':
                            order_details.to_csv('log')
                            raise RuntimeError("Lowest buy order failed to cancel")
                        else:
                            # open new buy order
                            order_details = create_order('buy',
                                                         open_orders[(open_orders['side'] == 'buy') & (
                                                                     open_orders['state'] == 'confirmed')]['price'].max(),
                                                         order_details)
                    elif order['side'] == 'buy':
                        # place next buy order
                        order_details = create_order('buy', open_orders['price'].min(), order_details)

                        # cancel highest buy order
                        order_to_cancel = open_orders.iloc[open_orders['price'].idxmax()]['id']
                        response = r.orders.cancel_crypto_order(order_to_cancel)
                        order_details.iloc[order_to_cancel.index] = response

                        if response['state'] != 'canceled':
                            order_details.to_csv('log')
                            raise RuntimeError("Highest buy order failed to cancel")
                        else:
                            # open new sell order
                            order_details = create_order('sell',
                                                         open_orders[(open_orders['side'] == 'sell') &
                                                                     (open_orders['state'] == 'confirmed')]['price'].max(),
                                                         order_details)
                else:
                    pass
            current_price = round(float(r.crypto.get_crypto_quote('ETH', info='bid_price')), 2)
            if current_price > prior_price:
                print('\033[92m', current_price, '\033[0m')
            else:
                print('\033[91m', current_price, '\033[0m')
            prior_price = current_price
        except:
            r.orders.cancel_all_crypto_orders()
            order_details.to_csv('log')
            raise KeyboardInterrupt


init()
#
# print(order_info)
# order_id = '62148575-4fdd-4237-aec8-2c7bfdca6b24'
# 'c9e8e6ae-d9fe-4d96-8baa-3ff7e63b4120'

# print(r.orders.get_crypto_order_info(order_id))

# 5 limit buys are set
# next we need to check to see if


# set limit buy at first_grid_price

# create 5 sell points


# print(r.crypto.get_crypto_info('ETH'))

# print(r.crypto.get_crypto_quote('ETH', info='ask_price'))

# print(my_coins)

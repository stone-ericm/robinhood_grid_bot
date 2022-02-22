import robin_stocks
import robin_stocks.robinhood as r
import pyotp

from credentials import username, password, auth_key

totp = pyotp.TOTP(auth_key).now()
login = r.login(username, password, mfa_code=totp)

my_stocks = r.crypto.get_crypto_positions()[0]
for key,value in my_stocks.items():
    print(my_stocks)


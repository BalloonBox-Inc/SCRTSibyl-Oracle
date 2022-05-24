from binance.spot import Spot as Client
from market.coinapi import *


def binance_client(key, secret):
    return Client(key, secret)


def binance_spot_balance(client, api_key):

    try:
        # binance balances
        balance = client.account()['balances']
        balance = [d for d in balance if float(d['free']) > 0]

        for d in balance:
            for key, value in d.items():
                if key != 'asset':
                    d[key] = float(value)

        # assets USD rate
        assets = [d['asset'] for d in balance]
        usd_rate = dict()

        for asset in assets:
            value = coinexchange_rate(asset, 'USD', api_key)
            if isinstance(value, float):
                usd_rate[asset] = value

        # USD balances
        keys = usd_rate.keys()

        for d in balance:
            currency = d['asset']
            if currency in usd_rate:
                d['free'] *= usd_rate[currency]
                d['locked'] *= usd_rate[currency]

        r = [d for d in balance if d['asset'] in keys]

    except Exception as e:
        r = str(e)

    finally:
        return r

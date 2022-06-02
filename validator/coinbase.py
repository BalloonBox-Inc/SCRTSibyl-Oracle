from coinbase.wallet.error import CoinbaseError
from coinbase.wallet.client import OAuthClient
from datetime import datetime
from icecream import ic
import numpy as np
import json


def coinbase_client(access_token, refresh_token):
    '''Connect to a client's Coinbase account using their tokens'''
    return OAuthClient(access_token, refresh_token)


def format_error(e):
    error = {'error': {
        'status_code': e.status_code,
        'message': e.message,
        'error_type': e.id
    }
    }
    ic(error)
    return error


def convert_to_json(obj):
    ''' Prettify, read, and return json data'''
    return json.loads(json.dumps(obj))


def coinbase_currencies(client):
    '''Get all Coinbase fiat currencies'''
    try:
        r = client.get_currencies()
        r = dict([(n['id'], float(n['min_size'])) for n in r['data']])

    except CoinbaseError as e:
        r = format_error(e)

    finally:
        return r


def coinbase_native_currency(client):
    '''Check what currency is currently set as default 'native currency' in the user's Coinbase account'''
    try:
        r = client.get_current_user()['native_currency']

    except CoinbaseError as e:
        r = format_error(e)

    finally:
        return r


def coinbase_set_native_currency(client, symbol):
    '''Reset the currency of the user's Coinbase account to its initial default native currency'''
    try:
        r = client.update_current_user(native_currency=symbol)

    except CoinbaseError as e:
        r = format_error(e)

    finally:
        return r


def coinbase_accounts(client):
    '''Returns list of accounts with balance > $0. Current balances are reported both in native currency and in USD for each account.'''
    try:
        r = convert_to_json(client.get_accounts()['data'])
        r = [n for n in r if float(n['native_balance']['amount']) != 0]

        for d in r:
            create_at = datetime.strptime(
                d['created_at'], '%Y-%m-%dT%H:%M:%SZ').date()
            native_balance = float(d['native_balance']['amount'])
            balance = float(d['balance']['amount'])
            d['created_at'] = create_at
            d['native_balance']['amount'] = native_balance
            d['balance']['amount'] = balance

    except CoinbaseError as e:
        r = format_error(e)

    finally:
        return r


def coinbase_transactions(client, account_id):
    '''Returns Coinbase data for all user's accounts'''
    try:
        r = convert_to_json(client.get_transactions(account_id)['data'])

    except CoinbaseError as e:
        r = format_error(e)

    finally:
        return r


def coinbase_accounts_and_transactions(client, currencies, txn_types):
    '''Returns user accounts and transactions'''
    try:
        # fetching accounts
        acc = coinbase_accounts(client)
        if 'error' in acc:
            raise Exception(acc['error']['message'])

        # formating accounts
        acc = [n for n in acc if n['currency'] in currencies]

        # fetching transactions
        txn = [coinbase_transactions(client, n['id']) for n in acc]

        # formatting transactions
        txn = [x for n in txn for x in n]
        txn = [n for n in txn
               if n['status'] == 'completed'
               and n['type'] in txn_types]

        for d in txn:
            if d['type'] == 'send' and np.sign(float(d['amount']['amount'])) == 1:
                d['type'] = 'send_credit'

            elif d['type'] == 'send' and np.sign(float(d['amount']['amount'])) == -1:
                d['type'] = 'send_debit'

    except Exception as e:
        acc = str(e)

    return acc, txn

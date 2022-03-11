from coinbase.wallet.error import CoinbaseError
from coinbase.wallet.client import Client
from datetime import datetime

import json

def coinbase_client(api_key, secret):
    return Client(api_key, secret)


def format_error(e):
    return {'error': {
                'status_code': e.status_code,
                'display_message': e.message,
                'error_type': e.id
                }
            }


def convert_to_json(obj):
    return json.loads(json.dumps(obj))


def coinbase_currencies(client):

    try:
        response = client.get_currencies()
        response = dict([(n['id'], float(n['min_size'])) for n in response['data']])
        
    except CoinbaseError as e:
        response = format_error(e)
    
    return response


def coinbase_native_currency(client):

    try:
        response = client.get_current_user()['native_currency']

    except CoinbaseError as e:
        response = format_error(e)
    
    return response


def coinbase_set_native_currency(client, symbol):

    try:
        client.update_current_user(native_currency=symbol)
        return
    
    except CoinbaseError as e:
        return format_error(e)


def coinbase_accounts(client):

    try:
        response = convert_to_json(client.get_accounts()['data'])
        response = [n for n in response if float(n['native_balance']['amount'])!=0]
        
        for d in response:
            create_at = datetime.strptime(d['created_at'], '%Y-%m-%dT%H:%M:%SZ').date()
            native_balance = float(d['native_balance']['amount'])
            balance = float(d['balance']['amount'])
            d['created_at'] = create_at
            d['native_balance']['amount'] = native_balance
            d['balance']['amount'] = balance
    
    except CoinbaseError as e:
        response = format_error(e)
    
    return response


def coinbase_transactions(client, account_id):

    try:
        response = convert_to_json(client.get_transactions(account_id)['data'])

    except CoinbaseError as e:
        response = format_error(e)
    
    return response

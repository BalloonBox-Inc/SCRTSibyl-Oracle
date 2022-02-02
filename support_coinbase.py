from coinbase.wallet.client import Client
from coinbase.wallet.error import CoinbaseError

import json


def coinbase_client(api_key, secret):
    return Client(api_key, secret)


def convert_to_json(api_obj):
    return json.loads(json.dumps(api_obj['data'][0]))


def format_error(e):
    return {'error': {
                'status_code': e.status_code,
                'display_message': e.message,
                'error_type': e.id
                }
            }


def coinbase_accounts(client):

    try:
        response = convert_to_json(client.get_accounts())

    except CoinbaseError as e:
        response = format_error(e)
    
    return response


def coinbase_transactions(client, account_id):

    try:
        response = convert_to_json(client.get_transactions(account_id))

    except CoinbaseError as e:
        response = format_error(e)
    
    return response


def coinbase_buys(client, account_id):

    try:
        response = convert_to_json(client.get_buys(account_id))

    except CoinbaseError as e:
        response = format_error(e)
    
    return response


def coinbase_sells(client, account_id):

    try:
        response = convert_to_json(client.get_sells(account_id))

    except CoinbaseError as e:
        response = format_error(e)
    
    return response


def coinbase_deposits(client, account_id):

    try:
        response = convert_to_json(client.get_deposits(account_id))

    except CoinbaseError as e:
        response = format_error(e)
    
    return response


def coinbase_withdrawals(client, account_id):

    try:
        response = convert_to_json(client.get_withdrawals(account_id))

    except CoinbaseError as e:
        response = format_error(e)
    
    return response

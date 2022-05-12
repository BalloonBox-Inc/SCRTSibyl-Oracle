'''This is a standalone .py file used for the sole purpose of demoing the credit scoring algorithm.
This file does not invoke any DApp frontend component, but runs entirely in the backend.'''

from flask import make_response
from coinbase.wallet.client import Client
from datetime import datetime, timezone
from dotenv import load_dotenv, dotenv_values
from icecream import ic

from app import *
from support.score import *
from support.feedback import *
from validator.plaid import *
from validator.coinbase import *
from support.metrics_plaid import *
from support.metrics_coinbase import *


# ------------------------------------- #
#                 PLAID                 #
# ------------------------------------- #
def create_feedback_plaid():
    '''create a feedback dict for Plaid'''
    return {'fetch': {}, 'credit': {}, 'velocity': {}, 'stability': {}, 'diversity': {}}


def hit_plaid_api(plaid_client_id, plaid_client_secret, plaid_token, coinmarketcap_key):
    '''
    Description:
        Import Plaid Sandbox data, calculate credit score for Sandbox user, return the numerical score and a qualitative feedback

    Parameters:
        plaid_client_id (str): client API key
        plaid_client_secret (str): client API secret key
        plaid_token (str): Plaid access token
        coinmarketcap_key: Coinmarketcap API key

    Returns:
        output (dict): credit score (numerical and qualitative)
    '''
    try:
        # client connection
        client = plaid_client('sandbox', plaid_client_id, plaid_client_secret)

        # data fetching and formatting
        plaid_txn = plaid_transactions(plaid_token, client, 360)
        if 'error' in plaid_txn:
            raise Exception(plaid_txn['error']['message'])

        plaid_txn = {k: v for k, v in plaid_txn.items(
        ) if k in ['accounts', 'item', 'transactions']}
        plaid_txn['transactions'] = [
            t for t in plaid_txn['transactions'] if not t['pending']]

        # compute score
        feedback = create_feedback_plaid()
        feedback = plaid_bank_name(
            client, plaid_txn['item']['institution_id'], feedback)
        score, feedback = plaid_score(plaid_txn, feedback)
        message = qualitative_feedback_plaid(
            score, feedback, coinmarketcap_key)
        feedback = interpret_score_plaid(score, feedback)

        status_code = 200
        status = 'success'

    except Exception as e:
        status_code = 400
        status = 'error'
        score = 0
        feedback = {}
        message = str(e)

    finally:
        timestamp = datetime.now(timezone.utc).strftime(
            '%m-%d-%Y %H:%M:%S GMT')
        output = {
            'endpoint': '/credit_score/plaid',
            'title': 'Credit Score',
            'status_code': status_code,
            'status': status,
            'timestamp': timestamp,
            'score': int(score),
            'feedback': feedback,
            'message': message
        }
        if score == 0:
            output.pop('score', None)
            output.pop('feedback', None)

        ic(output)
        return make_response(output, output['status_code'])


# ------------------------------------- #
#               COINBASE                #
# ------------------------------------- #
def create_feedback_coinbase():
    return {'kyc': {}, 'history': {}, 'liquidity': {}, 'activity': {}}


def hit_coinbase_api(coinbase_client_id, coinbase_client_secret, coinmarketcap_key):
    '''
    Description:
        Import your Coinbase account data, calculate your credit score, return the numerical score and a qualitative feedback

    Parameters:
        coinbase_client_id (str): Coinbase id key
        coinbase_client_secret (str): Coinbase secret key
        coinmarketcap_key: Coinmarketcap API key

    Returns:
        output (dict): credit score (numerical and qualitative)
    '''
    try:
        # client connection
        client = Client(coinbase_client_id, coinbase_client_secret)

        # coinmarketcap
        # fetch top X cryptos from coinmarketcap API
        top_coins = coinmarketcap_coins(coinmarketcap_key, 25)
        currencies = coinbase_currencies(client)
        if 'error' in currencies:
            raise Exception(currencies['error']['message'])

        odd_fiats = ['BHD', 'BIF', 'BYR', 'CLP', 'DJF', 'GNF', 'HUF', 'IQD', 'ISK', 'JOD', 'JPY', 'KMF', 'KRW',
                     'KWD', 'LYD', 'MGA', 'MRO', 'OMR', 'PYG', 'RWF', 'TND', 'UGX', 'VND', 'VUV', 'XAF', 'XOF', 'XPF']
        currencies = {k: 1 for (k, v) in currencies.items()
                      if v == 0.01 or k in odd_fiats}
        top_coins.update(currencies)
        coins = list(top_coins.keys())

        # change coinbase native currency to USD
        native = coinbase_native_currency(client)

        if 'error' in native:
            raise Exception(native['error']['message'])
        if native != 'USD':
            set_native = coinbase_set_native_currency(client, 'USD')

        # fetch and format data from user's Coinbase account
        coinbase_acc = coinbase_accounts(client)
        if 'error' in coinbase_acc:
            raise Exception(coinbase_acc['error']['message'])
        coinbase_acc = [n for n in coinbase_acc if n['currency'] in coins]

        coinbase_txn = [coinbase_transactions(
            client, n['id']) for n in coinbase_acc]
        coinbase_txn = [x for n in coinbase_txn for x in n]

        # keep only certain transaction types
        txn_types = ['fiat_deposit', 'request', 'buy',
                     'fiat_withdrawal', 'vault_withdrawal', 'sell', 'send']
        coinbase_txn = [n for n in coinbase_txn if n['status']
                        == 'completed' and n['type'] in txn_types]
        for d in coinbase_txn:
            # If the txn is of 'send' type and is a credit, then relabel its type to 'send_credit'
            if d['type'] == 'send' and np.sign(float(d['amount']['amount'])) == 1:
                d['type'] = 'send_credit'
            # If the txn is of 'send' type and is a debit, then relabel its type to 'send_debit'
            elif d['type'] == 'send' and np.sign(float(d['amount']['amount'])) == -1:
                d['type'] = 'send_debit'

        # reset native currency
        set_native = coinbase_set_native_currency(client, native)

        # compute score
        feedback = create_feedback_coinbase()
        score, feedback = coinbase_score(coinbase_acc, coinbase_txn, feedback)
        message = qualitative_feedback_coinbase(
            score, feedback, coinmarketcap_key)
        feedback = interpret_score_coinbase(score, feedback)

        status_code = 200
        status = 'success'

    except Exception as e:
        status_code = 400
        status = 'error'
        score = 0
        feedback = {}
        message = str(e)

    finally:
        timestamp = datetime.now(timezone.utc).strftime(
            '%m-%d-%Y %H:%M:%S GMT')
        output = {
            'endpoint': '/credit_score/coinbase',
            'title': 'Credit Score',
            'status_code': status_code,
            'status': status,
            'timestamp': timestamp,
            'score': int(score),
            'feedback': feedback,
            'message': message
        }
        if score == 0:
            output.pop('score', None)
            output.pop('feedback', None)

        ic(output)
        return make_response(output, output['status_code'])


# ------------------------------------- #
#                  DEMO                 #
# ------------------------------------- #
if __name__ == '__main__':
    load_dotenv()
    config = dotenv_values()

    # Plaid
    hit_plaid_api(
        config['PLAID_CLIENT_ID'],
        config['PLAID_CLIENT_SECRET'],
        config['PLAID_ACCESS_TOKEN'],
        config['COINMARKETCAP_KEY']
    )
    print()

    # Coinbase
    hit_coinbase_api(
        config['COINBASE_CLIENT_ID'],
        config['COINBASE_CLIENT_SECRET'],
        config['COINMARKETCAP_KEY']
    )

from flask import request, make_response
from dotenv import load_dotenv
from os import getenv

from validator_api.coinbase import *
from validator_api.plaid import *
from support.score import *

from app import *

load_dotenv()


def create_feedback_plaid():
    return {'data': [], 'credit': [], 'velocity': [], 'stability': [], 'diversity': []}


def create_feedback_coinbase():
    return {'data': [], 'kyc': [], 'history': [], 'liquidity': [], 'activity': []}


# @app.route('/credit_score', methods=['POST'])
def credit_score_plaid():

    try:
        # plaid_token = request.json.get('plaid_public_token', None)
        # keplr_token = request.json.get('keplr_token', None)
        plaid_token = getenv('PLAID_ACCESS_TOKEN')
        plaid_client_id = getenv('PLAID_CLIENT_ID')
        plaid_client_secret = getenv('PLAID_CLIENT_SECRET')
    except Exception as e:
        return str(e)

    try:
        # client connection
        client = plaid_client('sandbox', plaid_client_id, plaid_client_secret)
        # client = plaid_client('production', plaid_client_id, plaid_client_secret)
        
        # data fetching and formatting
        plaid_txn = plaid_transactions(plaid_token, client, 360)
        plaid_txn = {k:v for k,v in plaid_txn.items() if k in ['accounts','transactions']}
        plaid_txn['transactions'] = [t for t in plaid_txn['transactions'] if not t['pending']]
        
        for d in plaid_txn['transactions']:
            d.update((k, v.strftime('%Y-%m-%d')) for k,v in d.items() if k=='date')

        # compute score
        feedback = create_feedback_plaid()
        output, feedback = plaid_score(plaid_txn, feedback)

        return output, feedback
    
    except Exception as e:
        return 'Error', str(e)


def credit_score_coinbase():

    # front-end inputs
    # coinbase_token = request.json.get('coinbase_public_token', None)
    # coinmarketcap_key = request.json.get('coinmarketcap_key', None)
    # keplr_token = request.json.get('keplr_token', None)
    coinbase_token = getenv('COINBASE_CLIENT_ID')
    coinbase_secret = getenv('COINBASE_CLIENT_SECRET')
    coinmarketcap_key = getenv('COINMARKETCAP_KEY')

    # coinbase credit score
    if coinbase_token:
        # get Coinmarketcap top coins
        feedback = create_feedback_coinbase()
        top_coins = top_currencies(coinmarketcap_key, coinbase_api_key, coinbase_api_secret, feedback)

        # data fetching
        acc = unfiltered_acc(coinbase_api_key, coinbase_api_secret, feedback)
        tx = unfiltered_tx(coinbase_api_key, coinbase_api_secret, acc, feedback)
        # acc = filter_acc(coinbase_api_key, coinbase_api_secret, top_coins)
        # tx = filter_tx(coinbase_api_key, coinbase_api_secret, acc)
        tx = refactor_send_tx(tx, feedback)

        # compute score
        feedback = create_feedback_coinbase()
        score, feedback = coinbase_score(acc, tx, feedback)

        return score, feedback

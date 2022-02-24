from flask import request, make_response
from dotenv import load_dotenv
from os import getenv

# from support_coinbase import *
from support_plaid import *
from support_score import *
from debugging import *

from app import *

load_dotenv()


# @app.route('/credit_score', methods=['POST'])
def credit_score_plaid():

    # front-end inputs
    # plaid_token = request.json.get('plaid_public_token', None)
    # coinbase_token = request.json.get('coinbase_public_token', None)
    # keplr_token = request.json.get('keplr_token', None)

    plaid_token = getenv('ACCESS_TOKEN')

    # plaid credit score
    if plaid_token:
        # create client connection
        client_plaid = plaid_client('sandbox', getenv('CLIENT_ID'), getenv('SECRET'))
        # client_plaid = plaid_client('production', getenv('CLIENT_ID'), getenv('SECRET'))
        
        # fetch data
        plaid_txn = plaid_transactions(plaid_token, client_plaid, 330)
        # format data
        tx = dict_to_json(plaid_txn)

        # compute score
        output, feedback = plaid_score(tx)

        return output, feedback





def credit_score_coinbase():

    # front-end inputs
    # plaid_token = request.json.get('plaid_public_token', None)
    # coinbase_token = request.json.get('coinbase_public_token', None)
    # keplr_token = request.json.get('keplr_token', None)

    coinbase_token = getenv('COINBASE_API_KEY')

    # coinbase credit score
    if coinbase_token:
        # declare API keys
        coinbase_api_key = getenv('COINBASE_API_KEY')
        coinbase_api_secret = getenv('COINBASE_API_SECRET')
        coinmarketcap_key = getenv('COINMARKETCAP_KEY')

        # get Coinmarketcap top coins
        top_coins = top_currencies(coinmarketcap_key, coinbase_api_key, coinbase_api_secret)

        # fetch data
        # acc = unfiltered_acc(coinbase_api_key, coinbase_api_secret)
        # tx = unfiltered_tx(coinbase_api_key, coinbase_api_secret, acc)
        acc = filter_acc(coinbase_api_key, coinbase_api_secret, top_coins)
        tx = filter_tx(coinbase_api_key, coinbase_api_secret, acc)
        tx = refactor_send_tx(tx)

        # compute score
        score, feedback = coinbase_score(acc, tx)

        return score, feedback









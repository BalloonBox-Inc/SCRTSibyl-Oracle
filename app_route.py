from flask import request, make_response
from dotenv import load_dotenv
from os import getenv

from support_coinbase import *
from support_plaid import *
from support_score import *
from debugging import *

from app import *

load_dotenv()


# @app.route('/credit_score', methods=['POST'])
def credit_score():

    # front-end inputs
    # plaid_token = request.json.get('plaid_public_token', None)
    plaid_token = getenv('PLAID_ACCESS_TOKEN')
    # coinbase_token = request.json.get('coinbase_public_token', None)
    coinbase_token = None

    # keplr_token = request.json.get('keplr_token', None)

    # plaid credit score
    if plaid_token:
        # create client connection
        client_plaid = plaid_client('sandbox', getenv('PLAID_CLIENT_ID'), getenv('PLAID_SECRET'))
        
        # fetch data
        plaid_id = plaid_identity(plaid_token, client_plaid)
        plaid_txn = plaid_transactions(plaid_token, client_plaid, 360)
        plaid_hldg = plaid_holdings(plaid_token, client_plaid)
        plaid_invt = plaid_investment_transactions(plaid_token, client_plaid, 360)

        # compute score
        output = plaid_score(plaid_txn, plaid_id, plaid_hldg, plaid_invt)

    # coinbase credit score
    elif coinbase_token:
        # create client connection
        client_coinbase = coinbase_client(getenv('COINBASE_API_KEY'), getenv('COINBASE_API_SECRET'))

        # fetch data
        coinbase_attr = None

        # compute score
        output = coinbase_score(coinbase_attr)
    
    return make_response(output, 200)

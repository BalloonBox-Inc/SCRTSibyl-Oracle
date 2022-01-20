from flask import request, make_response
from dotenv import load_dotenv
from os import getenv

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

    # client connection
    if plaid_token:
        client_plaid = plaid_client('sandbox', getenv('PLAID_CLIENT_ID'), getenv('PLAID_SECRET'))
    if coinbase_token:
        client_coinbase = None

    # compute credit score
    if plaid_token and coinbase_token:
        # plaid
        plaid_id = plaid_identity(plaid_token, client_plaid)
        plaid_txn = plaid_transactions(plaid_token, client_plaid, 30)
        plaid_hldg = plaid_holdings(plaid_token, client_plaid)
        plaid_invt = plaid_investment_transactions(plaid_token, client_plaid, 30)

        # coinbase
        
        output = plaid_and_coinbase_score(plaid_txn, plaid_id, plaid_hldg, plaid_invt)

    else:
        if plaid_token and not coinbase_token:
            plaid_id = plaid_identity(plaid_token, client_plaid)
            plaid_txn = plaid_transactions(plaid_token, client_plaid, 30)
            plaid_hldg = plaid_holdings(plaid_token, client_plaid)
            plaid_invt = plaid_investment_transactions(plaid_token, client_plaid, 30)

            output = plaid_score(plaid_txn, plaid_id, plaid_hldg, plaid_invt)
        
        elif coinbase_token and not plaid_token:

            output = coinbase_score()
        
        else:
            output = 'do nothing'
    
    return make_response(output, 200)

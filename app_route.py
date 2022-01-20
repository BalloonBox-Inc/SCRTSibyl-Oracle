from flask import request, make_response
from dotenv import load_dotenv
from os import getenv

from support_plaid import *
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
        
        # coinbase
        
        output = 'do plaid and coinbase'

    else:
        if plaid_token and not coinbase_token:

            output = 'do plaid'
        
        elif coinbase_token and not plaid_token:

            output = 'do coinbase'
        
        else:
            output = 'do nothing'
    
    return make_response(output, 200)

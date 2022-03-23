from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest

from plaid.api import plaid_api
from dotenv import load_dotenv
from datetime import timedelta
from datetime import datetime
from icecream import ic
from os import getenv

import plaid
import json

load_dotenv()

if getenv('ENV') == 'production':
    ic.disable()


def plaid_environment(plaid_env):
    if plaid_env == 'sandbox':
        host = plaid.Environment.Sandbox

    if plaid_env == 'development':
        host = plaid.Environment.Development

    if plaid_env == 'production':
        host = plaid.Environment.Production

    return host


def plaid_client(plaid_env, client_id, secret):
    config = plaid.Configuration(
        host=plaid_environment(plaid_env),
        api_key={
            'clientId': client_id,
            'secret': secret
            }
        )
    return plaid_api.PlaidApi(plaid.ApiClient(config))


def format_error(e):
    r = json.loads(e.body)
    error = {'error': {
                'status_code': e.status,
                'message': r['error_message'],
                'error_code': r['error_code'],
                'error_type': r['error_type']
                }
            }
    ic(error) 
    return error


def plaid_transactions(access_token, client, timeframe):

    start_date = (datetime.now() - timedelta(days=timeframe))
    end_date = datetime.now()

    try:
        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date.date(),
            end_date=end_date.date(),
            options=TransactionsGetRequestOptions()
            )
        
        r = client.transactions_get(request).to_dict()
    
    except plaid.ApiException as e:
        r = format_error(e)
    
    finally:
        return r


def plaid_institutions(client, bank_id):
    try:
        # Do not supply the country_code parameter so that it defaults to US
        request = InstitutionsGetByIdRequest(institution_id=bank_id, country_codes=[]) 
        r = client.institutions_get_by_id(request).to_dict()
    
    except plaid.ApiException as e:
        r = format_error(e)
    
    finally:
        return r
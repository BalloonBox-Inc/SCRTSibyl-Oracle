from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.accounts_get_request import AccountsGetRequest

from plaid.api import plaid_api
from datetime import timedelta
from datetime import datetime

import plaid
import json


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
    response = json.loads(e.body)
    return {'error': {
                'status_code': e.status,
                'display_message': response['error_message'],
                'error_code': response['error_code'],
                'error_type': response['error_type']
                }
            }


def plaid_accounts(access_token, client):

    try:
        request = AccountsGetRequest(
            access_token=access_token
            )
        response = client.accounts_get(request).to_dict()
        
    except plaid.ApiException as e:
        response = format_error(e)
    
    return response


def plaid_balance(access_token, client):

    try:
        request = AccountsBalanceGetRequest(
            access_token=access_token
            )

        response = client.accounts_balance_get(request).to_dict()
        
    except plaid.ApiException as e:
        response = format_error(e)
    
    return response


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
        
        response = client.transactions_get(request).to_dict()
    
    except plaid.ApiException as e:
        response = format_error(e)
    
    return response

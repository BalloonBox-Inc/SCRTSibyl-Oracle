from plaid.api import plaid_api

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

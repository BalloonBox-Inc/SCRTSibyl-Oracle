import numpy as np


# CURRENCIES
def allowed_currencies():
    return ['USD', 'EUR', 'BTC', 'ETH', 'USDT', 'USDC', 'BNB', 'XRP', 'SCRT']


# RANGES
def score_range():
    return np.array([500, 560, 650, 740, 800, 870])


def loan_range():
    return np.array([0.5, 1, 5, 10, 15, 20, 25])*1000


def qualitative_range():
    return ['very poor', 'poor', 'fair', 'good', 'very good', 'excellent', 'exceptional']


# SCORES
def plaid_score_weights(**kw):
    # [ credit, velocity, stability, diversity ]
    if kw['credit']:
        return [0.42, 0.2, 0.28, 0.1]
    else:
        # adds up to 0.95 for lack of credit card - it's a penalty
        return [0.0, 0.33, 0.42, 0.2]


def coinbase_score_weights():
    # [ kyc, history, liquidity, activity ]
    return [0.1, 0.1, 0.4, 0.4]


# MODELS
def plaid_credit_model_weights():
    # [ limit, util_ratio, interest, length, livelihood ]
    return [0.45, 0.12, 0.05, 0.26, 0.12]


def plaid_velocity_model_weights():
    # [ withdrawals, deposits, net_flow, txn_count, slope ]
    return [0.16, 0.25, 0.25, 0.16, 0.18]


def plaid_stability_model_weights():
    # [ balance, run_balance ]
    return [0.7, 0.3]


def plaid_diversity_model_weights():
    # [ acc_count, profile ]
    return [0.4, 0.6]


def coinbase_liquidity_model_weights():
    # [ balance, run_balance ]
    return [0.6, 0.4]


def coinbase_activity_model_weights():
    # [ credit_volume, debit_volume, credit_consistency, debit_consistency, inception ]
    return [0.2, 0.2, 0.2, 0.2, 0.2]


# FEEDBACK
def create_feedback_plaid():
    return {'fetch': {}, 'credit': {}, 'velocity': {}, 'stability': {}, 'diversity': {}}


def create_feedback_coinbase():
    return {'kyc': {}, 'history': {}, 'liquidity': {}, 'activity': {}}


# MESSAGES
def no_score_message():
    return {
        'plaid': 'SCRTsibyl could not calculate your credit score as there is no active credit line nor transaction history associated with your bank account. Try to log into an alternative bank account if you have one',
        'coinbase': 'SCRTsibyl could not calculate your credit score as there is no active wallet nor transaction history associated with your account. Try to log into Coinbase with a different account'
    }


def score_message(quality, score, scrt, usd):
    return f'Congrats! Your SCRTsibyl score is {quality} - {score} points. This score qualifies you for a short term loan of up to {scrt} SCRT ({usd} USD)'


# COINBASE
def coinbase_txn_types():
    return ['fiat_deposit', 'request', 'buy', 'fiat_withdrawal', 'vault_withdrawal', 'sell', 'send']


def coinbase_odd_fiats():
    return ['BHD', 'BIF', 'BYR', 'CLP', 'DJF', 'GNF', 'HUF', 'IQD', 'ISK', 'JOD', 'JPY', 'KMF', 'KRW',
            'KWD', 'LYD', 'MGA', 'MRO', 'OMR', 'PYG', 'RWF', 'TND', 'UGX', 'VND', 'VUV', 'XAF', 'XOF', 'XPF']

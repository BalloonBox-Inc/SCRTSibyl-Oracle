import numpy as np


# CURRENCIES
def exchange_currencies():
    # dict of allowed coins and decimal places to round when diplaying
    return {
        'USD': 0,
        'EUR': 0,
        'BTC': 4,
        'ETH': 4,
        'USDT': 0,
        'USDC': 0,
        'BNB': 2,
        'XRP': 0,
        'SCRT': 0
    }


# RANGES
def score_range():
    return np.array([500, 560, 650, 740, 800, 870])


def loan_range():
    return np.array([0.5, 1, 5, 10, 15, 20, 25])*1000


def qualitative_range():
    return ['very poor', 'poor', 'fair', 'good', 'very good', 'excellent', 'exceptional']


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


def score_message(coin, quality, score, loan, rate):
    msg = f'Congrats! Your SCRTsibyl score is {quality} - {score} points. This score qualifies you for a short term loan of up to {loan} {coin}'
    if coin == 'SCRT':
        return msg
    else:
        return msg + f' ({rate} SCRT)'

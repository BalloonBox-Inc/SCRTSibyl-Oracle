from support.models import *
from config.params import *
from support.helper import *


def plaid_score(txn, feedback):

    credit, feedback = credit_mix(txn, feedback)

    if credit == 0:
        velocity, feedback = plaid_velocity(txn, feedback)
        stability, feedback = plaid_stability(txn, feedback)
        diversity, feedback = plaid_diversity(txn, feedback)

        a = plaid_score_weights(credit=False)

    else:
        credit, feedback = plaid_credit(txn, feedback)
        velocity, feedback = plaid_velocity(txn, feedback)
        stability, feedback = plaid_stability(txn, feedback)
        diversity, feedback = plaid_diversity(txn, feedback)

        a = plaid_score_weights(credit=True)

    b = [credit, velocity, stability, diversity]

    score = 300 + 600*(dot_product(a, b))

    return score, feedback


def coinbase_score(acc, txn, feedback):

    kyc, feedback = coinbase_kyc(acc, txn, feedback)
    history, feedback = coinbase_history(acc, feedback)
    liquidity, feedback = coinbase_liquidity(acc, txn, feedback)
    activity, feedback = coinbase_activity(acc, txn, feedback)

    a = coinbase_score_weights()
    b = [kyc, history, liquidity, activity]

    score = 300 + 600*(dot_product(a, b))

    return score, feedback


def binance_score(balances, wallets, trades, savings, nfts, swaps, feedback):

    history, feedback = (wallets, feedback)
    liquidity, feedback = (balances, wallets, savings, feedback)
    activity, feedback = (trades, nfts, swaps, feedback)
    diversity, feedback = (balances, feedback)

    a = binance_score_weights()
    b = [history, liquidity, activity, diversity]

    score = 300 + 600*(dot_product(a, b))

    return score, feedback

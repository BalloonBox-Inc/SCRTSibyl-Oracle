from support.models import *
from support.helper import *


def plaid_score(txn, feedback, weights, penalties):

    credit, feedback = credit_mix(txn, feedback)

    if credit == 0:
        velocity, feedback = plaid_velocity(txn, feedback)
        stability, feedback = plaid_stability(txn, feedback)
        diversity, feedback = plaid_diversity(txn, feedback)

        a = list(penalties.values())

    else:
        credit, feedback = plaid_credit(txn, feedback)
        velocity, feedback = plaid_velocity(txn, feedback)
        stability, feedback = plaid_stability(txn, feedback)
        diversity, feedback = plaid_diversity(txn, feedback)

        a = list(weights.values())

    # must be in the same order as showed in the config.json file
    b = [credit, velocity, stability, diversity]

    score = 300 + 600*(dot_product(a, b))

    return score, feedback


def coinbase_score(acc, txn, feedback, weights):

    kyc, feedback = coinbase_kyc(acc, txn, feedback)
    history, feedback = coinbase_history(acc, feedback)
    liquidity, feedback = coinbase_liquidity(acc, txn, feedback)
    activity, feedback = coinbase_activity(acc, txn, feedback)

    a = list(weights.values())

    # must be in the same order as showed in the config.json file
    b = [kyc, history, liquidity, activity]

    score = 300 + 600*(dot_product(a, b))

    return score, feedback


def binance_score(balances, wallets, trades, savings, nfts, swaps, feedback, weights):

    # history, feedback = (wallets, feedback)
    # liquidity, feedback = (balances, wallets, savings, feedback)
    # activity, feedback = (trades, nfts, swaps, feedback)
    # diversity, feedback = (balances, feedback)
    history = 2
    liquidity = 1.3
    activity = 1.4
    diversity = 1.2

    a = list(weights.values())

    # must be in the same order as showed in the config.json file
    b = [history, liquidity, activity, diversity]

    score = 300 + 600*(dot_product(a, b))

    return score, feedback

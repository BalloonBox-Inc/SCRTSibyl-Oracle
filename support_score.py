from support_models import *


def plaid_and_coinbase_score(plaid_txn, plaid_id, plaid_hldg, plaid_invt):
    return None


def plaid_score(plaid_txn, plaid_id, plaid_hldg, plaid_invt):

    cash_flow = plaid_cash_flow(...)
    velocity = plaid_velocity(...)
    stability = plaid_stability(...)
    diversity = plaid_diversity(...)

    score = 0.55*cash_flow \
        + 0.20*velocity \
        + 0.15*stability \
        + 0.10*diversity \

    return score


def coinbase_score():
    return None

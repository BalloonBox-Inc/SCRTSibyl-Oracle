from support_models import *


# Initialize feedback dict
def create_feedback_plaid():
    return {'data_fetch': [], 'credit': [], 'velocity': [], 'stability': [], 'diversity': []}

def create_feedback_coinbase():
    return {'data fetch': [], 'kyc': [], 'history': [], 'liquidity': [], 'activity': []}



# Plaid
def plaid_score(txn):

    feedback = create_feedback_plaid()

    credit, feedback = plaid_credit(txn, feedback)
    velocity, feedback = plaid_velocity(txn, feedback)
    stability, feedback = plaid_stability(txn, feedback)
    diversity, feedback = plaid_diversity(txn, feedback)

    score = 300 + 600*(0.45*credit + 0.35*velocity + 0.15*stability + 0.05*diversity)
    
    return score, feedback


# Coinbase
def coinbase_score(acc, txn):

    feedback = create_feedback_coinbase()

    kyc, feedback = plaid_kyc(acc, txn, feedback)
    history, feedback = plaid_history(acc, feedback)
    liquidity, feedback = plaid_liquidity(acc, txn, feedback)
    activity, feedback = plaid_activity(acc, txn, feedback)

    score = 300 + 600*(0.10*kyc + 0.10*history + 0.40*liquidity + 0.40*activity)

    return score, feedback


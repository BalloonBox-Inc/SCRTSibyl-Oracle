from support_models import *


# Initialize feedback dict
def create_feedback_plaid():
    return {'data_fetch': [], 'credit': [], 'velocity': [], 'stability': [], 'diversity': []}

def create_feedback_coinbase():
    return {'data_fetch': [], 'kyc': [], 'history': [], 'liquidity': [], 'activity': []}



# Plaid
def plaid_score(txn):

    feedback = create_feedback_plaid()
    mix, feedback = credit_mix(txn, feedback)
    feedback = create_feedback_plaid()

    if mix == 0:
        feedback['credit'].append("User owns NO credit cards")
        velocity, feedback = plaid_velocity(txn, feedback)
        stability, feedback = plaid_stability(txn, feedback)
        diversity, feedback = plaid_diversity(txn, feedback)
        score = 300 + 600*(0.33*velocity + 0.42*stability + 0.20*diversity) # adds up to 0.95

    else:   
        credit, feedback = plaid_credit(txn, feedback)
        velocity, feedback = plaid_velocity(txn, feedback)
        stability, feedback = plaid_stability(txn, feedback)
        diversity, feedback = plaid_diversity(txn, feedback)
        score = 300 + 600*(0.42*credit + 0.20*velocity + 0.28*stability + 0.10*diversity)
    
    return score, feedback


# Coinbase
def coinbase_score(acc, txn, feedback):

    kyc, feedback = coinbase_kyc(acc, txn, feedback)
    history, feedback = coinbase_history(acc, feedback)
    liquidity, feedback = coinbase_liquidity(acc, txn, feedback)
    activity, feedback = coinbase_activity(acc, txn, feedback)

    score = 300 + 600*(0.10*kyc + 0.10*history + 0.40*liquidity + 0.40*activity)

    return score, feedback




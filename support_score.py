from support_models import *
from support_metrics_plaid import * # to be removed later since tx will come through the api



# Initialize feedback dict
def create_feedback_plaid():
    return {'data_fetch': [], 'credit': [], 'velocity': [], 'stability': [], 'diversity': []}

def create_feedback_coinbase():
    return {'data fetch': [], 'kyc': [], 'history': [], 'liquidity': [], 'activity': []}



# Plaid
def plaid_score(txn):

    feedback = create_feedback_plaid()

    credit = plaid_credit(txn, feedback)
    velocity = plaid_velocity(txn, feedback)
    stability = plaid_stability(txn, feedback)
    diversity = plaid_diversity(txn, feedback)

    # credit score, range = [300, 900]
    score = 300 + 600*(
        0.45*credit \
        + 0.35*velocity \
        + 0.15*stability \
        + 0.05*diversity)
    return score, feedback
    


# Coinbase
def coinbase_score(acc, tx):
    
    feedback = create_feedback_coinbase()

    # kyc = plaid_kyc(acc, tx)
    # history = plaid_history(acc)
    # liquidity = plaid_liquidity(acc, tx)
    # activity = plaid_activity(acc, tx)

    # # credit score, range = [300, 900]
    # score = 300 + 600*(
    #     0.10*kyc \
    #     + 0.10*history \
    #     + 0.40*liquidity \
    #     + 0.40*activity)
    # return score, feedback
    return None






# import time
# # Define path to locally stored real users data. Next, import data
# config = dotenv_values()
# path_dir = config['PATH_REAL_USERS_DATA']

# # Calculate score for all users you have data for
# for userid in [4]:
#     start_time = time.time()
#     tx = get_tx(path_dir, userid)
#     score, feedback = plaid_score(tx)
#     runtime = round(time.time() - start_time, 3)
#     print()
#     print('User #{} got a Coinbase SCRTSybil score (computed in {} sec) of {}/900 points'.format(userid, runtime, round(score)))
#     print()
#     print('Score feedback.credit = {}'.format(feedback['credit']))
#     print('Score feedback.velocity = {}'.format(feedback['velocity']))
#     print('Score feedback.stability = {}'.format(feedback['stability']))
#     print('Score feedback.diversity = {}'.format(feedback['diversity']))
#     print()


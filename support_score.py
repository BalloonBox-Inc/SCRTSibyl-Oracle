from support_models import *
from support_metrics import * # to be removed later since tx will come through the api


# Plaid
def plaid_score(tx):

    credit = plaid_credit(tx)
    velocity = plaid_velocity(tx)
    stability = plaid_stability(tx)
    diversity = plaid_diversity(tx)

    # credit score, range = [300, 900]
    score = 300 + 600*(
        0.45*credit \
        + 0.35*velocity \
        + 0.15*stability \
        + 0.05*diversity)
    return score, feedback


# Coinbase
def coinbase_score():
    return None


# import time
# # Define path to locally stored real users data. Next, import data
# path_dir=PATH_REAL_UDERS_DATA

# # Calculate score for all users you have data for
# for user in [1,2,3,4,5,6,7,8,9,11,12]:
#     start_time = time.time()
#     tx = get_tx(path_dir, user)
#     score, feedback = main(tx)
#     runtime = round(time.time() - start_time, 3)
#     print('User #{} got a SCRTSybil score (computed in {} sec) of {}/900 points'.format(user, runtime, round(score)))

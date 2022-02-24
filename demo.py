import time
from app_route import *
from support_score import *
from support_models import *
from support_metrics_plaid import *





# -------------------------------------------------------------------------- #
#                                   PLAID                                    #
# -------------------------------------------------------------------------- #  

# Local
# Define path to locally stored dummy data
config = dotenv_values()
path_dir = config['PATH_REAL_USERS_DATA']

# Calculate score for all users you have data for
for userid in [1,2,3,4,5,6,7,8,9,10]:
    start_time = time.time()
    tx = get_tx(path_dir, userid)
    score, feedback = plaid_score(tx)
    runtime = round(time.time() - start_time, 3)
    print()
    print('User #{} got a Plaid SCRTSibyl score (computed in {} sec) of {}/900 points'.format(userid, runtime, round(score)))
    print()
    print('Credit: {}'.format(feedback['credit']))
    print('Velocity: {}'.format(feedback['velocity']))
    print('Stability: {}'.format(feedback['stability']))
    print('Diversity: {}'.format(feedback['diversity']))
    print()



# Remote
start_time = time.time()
score, feedback = credit_score_plaid()
runtime = round(time.time() - start_time, 3)
print()
print('User #0 got a Plaid SCRTSibyl score (computed in {} sec) of {}/900 points'.format(runtime, round(score)))
print()
print('Credit: {}'.format(feedback['credit']))
print('Velocity: {}'.format(feedback['velocity']))
print('Stability: {}'.format(feedback['stability']))
print('Diversity: {}'.format(feedback['diversity']))
print()



# -------------------------------------------------------------------------- #
#                                  COINBASE                                  #
# -------------------------------------------------------------------------- # 

config = dotenv_values()
APIKey = config['COINBASE_API_KEY']
APISecret = config['COINBASE_API_SECRET']
coinmarketcap_key = config['COINMARKETCAP_KEY']
path_dir_coinbase = config['PATH_DIR_COINBASE_DATA']


# Local
# Compute score for a local user 
for userid in ['1', '2', '3', '4']:
    start_time = time.time()
    top_coins = top_currencies(coinmarketcap_key, APIKey, APISecret)
    acc, tx = local_get_data(path_dir_coinbase, userid, top_coins)
    tx = refactor_send_tx(tx)
    score, feedback = coinbase_score(acc, tx)
    runtime = round(time.time() - start_time, 3)
    print()
    print('User #{} got a Coinbase SCRTSibyl score (computed in {} sec) of {}/900 points'.format(userid, runtime, round(score)))
    print()
    print('Kyc: {}'.format(feedback['kyc']))
    print('History: {}'.format(feedback['history']))
    print('Liquidity: {}'.format(feedback['liquidity']))
    print('Activity {}'.format(feedback['activity']))
    print()
    print('_____________________________________________')
    print()



# # Compute score for a remote user via Coinbase API 
start_time = time.time()
score, feedback = credit_score_coinbase()
runtime = round(time.time() - start_time, 3)
print()
print('User #0 got a Coinbase SCRTSibyl score (computed in {} sec) of {}/900 points'.format(runtime, round(score)))
print()
print('Kyc: {}'.format(feedback['kyc']))
print('History: {}'.format(feedback['history']))
print('Liquidity: {}'.format(feedback['liquidity']))
print('Activity {}'.format(feedback['activity']))
print()
import time
from app_route import *
from support_score import *
from support_models import *
from support_metrics_plaid import *





# -------------------------------------------------------------------------- #
#                                   PLAID                                    #
# -------------------------------------------------------------------------- #  

# # Local
# # Define path to locally stored dummy data
# config = dotenv_values()
# path_dir = config['PATH_REAL_USERS_DATA']
# # Calculate score for all users you have data for
# list_of_feedback = []
# for userid in [i for i in [0, 1, 2, 3]]:
#     start_time = time.time()
#     feedback = create_feedback_plaid()
#     tx = get_tx(path_dir, userid, feedback)
#     score, feedback = plaid_score(tx)
#     runtime = round(time.time() - start_time, 3)
#     print('_____________________________________________')
#     print()
#     print('TEST USER #{} got a score of {}/900 points'.format(userid, round(score)))
#     print('Runtime: {} seconds'.format(runtime))
#     print('Validator: Plaid')
#     print()
#     for k in feedback.keys():
#         if k != 'data_fetch':
#             print('{}'.format(k.upper()))
#             for elem in feedback[k]:
#                 print(elem)
#             print()
#     print('_____________________________________________')
#     print()
#     list_of_feedback.append(feedback)

# print(list_of_feedback)
# with open('feedback_plaid.json', 'w') as json_file:
#     json.dump(list_of_feedback, json_file, indent = 4)




# # # Remote
# start_time = time.time()
# score, feedback = credit_score_plaid()
# runtime = round(time.time() - start_time, 3)
# print('_____________________________________________')
# print()
# print('TEST USER #0 got a score of {}/900 points'.format(round(score)))
# print('Runtime: {} seconds'.format(runtime))
# print('Validator: Plaid')
# print()
# for k in feedback.keys():
#     if k != 'data_fetch':
#         print('{}'.format(k.upper()))
#         for elem in feedback[k]:
#             print(elem)
#         print()
# print('_____________________________________________')
# print()


# -------------------------------------------------------------------------- #
#                                  COINBASE                                  #
# -------------------------------------------------------------------------- # 

config = dotenv_values()
APIKey = config['COINBASE_CLIENT_ID']
APISecret = config['COINBASE_CLIENT_SECRET']
coinmarketcap_key = config['COINMARKETCAP_KEY']
path_dir_coinbase = config['PATH_DIR_COINBASE_DATA']


# Local
# Compute score for a local user 
list_of_feedback = []
for userid in ['0', '1', '2']:
    start_time = time.time()
    feedback = create_feedback_coinbase()
    top_coins = top_currencies(coinmarketcap_key, APIKey, APISecret, feedback)
    acc, tx = local_get_data(path_dir_coinbase, userid, top_coins, feedback)
    tx = refactor_send_tx(tx, feedback)
    score, feedback = coinbase_score(acc, tx, feedback)
    runtime = round(time.time() - start_time, 3)
    print('_____________________________________________')
    print()
    print('TEST USER #{} got a score of {}/900 points'.format(userid, round(score)))
    print('Runtime: {} seconds'.format(runtime))
    print('Validator: Coinbase')
    print()
    for k in feedback.keys():
        if k != 'data_fetch':
            print('{}'.format(k.upper()))
            for elem in feedback[k]:
                print(elem)
            print()
    print('_____________________________________________')
    print()
    list_of_feedback.append(feedback)



# # Compute score for a remote user via Coinbase API 
start_time = time.time()
feedback = create_feedback_plaid()
score, feedback = credit_score_coinbase()
runtime = round(time.time() - start_time, 3)
print('_____________________________________________')
print()
print('TEST USER #0 got a score of {}/900 points'.format(round(score)))
print('Runtime: {} seconds'.format(runtime))
print('Validator: Coinbase')
print()
for k in feedback.keys():
    if k != 'data_fetch':
        print('{}'.format(k.upper()))
        for elem in feedback[k]:
            print(elem)
        print()
print('_____________________________________________')
print()
list_of_feedback.append(feedback)

print(list_of_feedback)
with open('feedback_coinbase.json', 'w') as json_file:
    json.dump(list_of_feedback, json_file, indent = 4)

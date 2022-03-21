from email import message
import time
from app_route import *
from support.score import *
from support.models import *
from support.metrics_plaid import *
from feedback.qualitative_score import *
from local_helper import *  # to be removed eventually
from dotenv import dotenv_values



# -------------------------------------------------------------------------- #
#                                   PLAID                                    #
# -------------------------------------------------------------------------- #  

# # Local
# # Define path to locally stored dummy data
# config = dotenv_values()
# path_dir = config['PATH_REAL_USERS_DATA']
# # Calculate score for all users you have data for
# list_of_feedback = []
# for userid in [i for i in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]]:
#     start_time = time.time()
#     feedback = create_feedback_plaid()
#     tx = get_tx(path_dir, userid, feedback)
#     tx = str_to_datetime(tx, feedback)
#     score, feedback = plaid_score(tx, feedback)
#     msg = qualitative_feedback_plaid(score, feedback)
#     interpret = interpret_score_plaid(score, feedback)
#     runtime = round(time.time() - start_time, 3)
#     print('_____________________________________________')
#     print()
#     print('TEST USER #{} got a score of {}/900 points'.format(userid, round(score)))
#     print('Runtime: {} seconds'.format(runtime))
#     print('Validator: Plaid')
#     print()
#     for k in feedback.keys():
#         print()
#         print(k.upper())
#         for sub_key in feedback[k].keys():
#             print('{} : {}'.format(sub_key, feedback[k][sub_key]))
#     print()
#     print(msg)
#     print(interpret)
#     # print('_____________________________________________')
#     # print()
#     list_of_feedback.append(interpret)

# with open('interpret_plaid.json', 'w') as json_file:
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
#     print(k)
#     print(k.upper())
#     for sub_key in feedback[k].keys():
#         print('{} : {}'.format(sub_key, feedback[k][sub_key]))
#     print()
# print('_____________________________________________')



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
    feedback = create_feedback_coinbase()
    top_coins = coinmarketcap_coins(coinmarketcap_key, 50)
    acc, tx = local_get_data(path_dir_coinbase, userid, top_coins)
    tx = refactor_send_tx(tx)
    acc = str_to_date(acc, feedback)
    score, feedback = coinbase_score(acc, tx, feedback)
    interpret = interpret_score_coinbase(score, feedback)
    msg = qualitative_feedback_coinbase(score, feedback)

    print('_____________________________________________')
    print()
    print('TEST USER #0 got a score of {}/900 points'.format(round(score)))
    print()
    for k in interpret.keys():
        print()
        print(k.upper())
        for sub_key in interpret[k].keys():
            print('{} : {}'.format(sub_key, interpret[k][sub_key]))
    print()
    for k in feedback.keys():
        print()
        print(k.upper())
        for sub_key in feedback[k].keys():
            print('{} : {}'.format(sub_key, feedback[k][sub_key]))
    print(msg)
    print()
    print(interpret)
    print('_____________________________________________')
    print()
    list_of_feedback.append(interpret)

print(list_of_feedback)
with open('feedback_coinbase.json', 'w') as json_file:
    json.dump(list_of_feedback, json_file, indent = 4)





# # # Compute score for a remote user via Coinbase API 
# score, feedback, message = credit_score_coinbase()
# interpret = interpret_score_coinbase(score, feedback)
# msg = qualitative_feedback_coinbase(score, feedback)
# list_of_feedback = []

# print('_____________________________________________')
# print()
# print('TEST USER #0 got a score of {}/900 points'.format(round(score)))
# print()
# for k in feedback.keys():
#     print()
#     print(k.upper())
#     for sub_key in feedback[k].keys():
#         print('{} : {}'.format(sub_key, feedback[k][sub_key]))
# print()
# print(feedback)
# print()
# for k in interpret.keys():
#     print()
#     print(k.upper())
#     for sub_key in interpret[k].keys():
#         print('{} : {}'.format(sub_key, interpret[k][sub_key]))
# print()
# print(interpret)
# print()
# print(msg)
# print('_____________________________________________')
# print()
# list_of_feedback.append(interpret)

# print(list_of_feedback)
# with open('feedback_coinbase.json', 'w') as json_file:
#     json.dump(list_of_feedback, json_file, indent = 4)


import numpy as np


# Scoring grids (identical for both Plaid and Coinbase)
score_bins = np.array([500, 560, 650, 740, 800, 870])
loan_bins = np.array([0.5, 1, 5, 10, 15, 20, 25])*1000
score_quality = ['very poor', 'poor', 'fair', 'good', 'very good', 'excellent', 'exceptional']




# -------------------------------------------------------------------------- #
#                                   Plaid                                    #
# -------------------------------------------------------------------------- #

def create_interpret_plaid():
    '''
   Description:
        Initializes a dict with a concise summary to communicate and interpret the SCRTSibyl score. 
        It includes the most important metrics used by the credit scoring algorithm (for Plaid).
    '''
    return {'score': 
    {
        'score_exist':False, \
        'points':None, \
        'quality':None, \
        'loan_amount':None, \
        'loan_duedate':None, \
        'card_names':None, \
        'cum_balance':None, \
        'bank_accounts':None
        }, 
            'advice': 
    {
        'credit_exist':False, \
        'credit_error':False, \
        'velocity_error':False, \
        'stability_error':False, \
        'diversity_error':False
        }
    }





def interpret_score_plaid(score, feedback):
    '''
    Description:
        returns a dict explaining the meaning of the numerical score
    
    Parameters:
        score (float): user's SCRTSibyl numerical score
        feedback (dict): score feedback, reporting stats on main Plaid metrics

    Returns:
        interpret (dict): dictionaries with the major contributing score metrics 
    '''
    try:
        # Create 'interpret' dict to interpret the numerical score
        interpret = create_interpret_plaid()


        # Score
        if feedback['fetch']:
            pass
        else:
            interpret['score']['score_exist'] = True
            interpret['score']['points'] = int(round(score, 3))
            interpret['score']['quality'] = score_quality[np.digitize(score, score_bins, right=False)]
            interpret['score']['loan_amount'] = int(loan_bins[np.digitize(score, score_bins, right=False)])
            if ('loan_duedate' in list(feedback['stability'].keys())):
                interpret['score']['loan_duedate'] = int(feedback['stability']['loan_duedate'])
            if ('card_names' in list(feedback['credit'].keys())) and (feedback['credit']['card_names']):
                interpret['score']['card_names'] = [c.capitalize() for c in feedback['credit']['card_names']]
            if 'cumulative_current_balance' in list(feedback['stability'].keys()):
                interpret['score']['cum_balance'] = feedback['stability']['cumulative_current_balance']
            if 'bank_accounts' in list(feedback['diversity'].keys()):
                interpret['score']['bank_accounts'] = feedback['diversity']['bank_accounts']


        # Advice
            if 'no credit card' not in list(feedback['credit'].values()):
                interpret['advice']['credit_exist'] = True
            if 'error' in list(feedback['credit'].keys()):
                interpret['advice']['credit_error'] = True
            if 'error' in list(feedback['velocity'].keys()):
                interpret['advice']['velocity_error'] = True
            if 'error' in list(feedback['stability'].keys()):
                interpret['advice']['stability_error'] = True
            if 'error' in list(feedback['diversity'].keys()):
                interpret['advice']['diversity_error'] = True


    except Exception as e:
        interpret = str(e)

    finally:
        return interpret






def qualitative_feedback_plaid(score, feedback):
    '''
    Description:
        A function to format and return a qualitative description of the numerical score obtained by the user
    
    Parameters:
        score (float): user's SCRTSibyl numerical score
        feedback (dict): score feedback, reporting stats on main Plaid metrics

    Returns:
        msg (str): qualitative message explaining the numerical score to the user. Return this message to the user in the front end of the Dapp
    '''
    # SCORE

    all_keys = [x for y in [list(feedback[k].keys()) for k in feedback.keys()] for x in y]
    # Case #1: NO score exists. Return fetch error when the Oracle did not fetch any data and computed no score
    if feedback['fetch']:
        msg = 'SCRTSibyl was unable to retrieve your data and therefore could not calculate your credit score. Try to log in using a different bank account.'
    
    # Case #2: a score exists. Return descriptive score feedback
    else:
        # Declare score variables
        quality = score_quality[np.digitize(score, score_bins, right=False)]
        points = int(round(score, 0))
        loan_amount = int(loan_bins[np.digitize(score, score_bins, right=False)])

        # Communicate the score
        msg0 = 'Your SCRTSibyl score is {0}, with a total of {1} points, which qualifies you for a loan of up to ${2} USD'\
                .format(quality.upper(), points, loan_amount)
        if ('loan_duedate' in list(feedback['stability'].keys())):
            msg0 = msg0 + ' with a recommended payback period of {0} months.'.format(feedback['stability']['loan_duedate'])
        else:
            msg0 = msg0 + '.'

        # Interpret the score        
        if ('card_names' in all_keys) or ('cumulative_current_balance' in all_keys) or ('bank_accounts' in all_keys):
            msg0 = msg0 + ' SCRTSibyl computed your score accounting for '

            # Credit cards 
            if 'card_names' in all_keys:
                msg0 = msg0 + 'your {} credit card'.format(', '.join([c.capitalize() for c in feedback['credit']['card_names']]))
                if len(feedback['credit']['card_names']) > 1:
                    msg0 = msg0 +'s '
                else:
                    msg0 = msg0 +' '

            # Tot balance now
            if  'cumulative_current_balance' in all_keys:
                msg0 = msg0 + 'your total current balance of ${} '.format(feedback['stability']['cumulative_current_balance'])

            # All credit accounts    
            if  ('bank_accounts' in all_keys) and (feedback['diversity']['bank_accounts']>1):
                if ('card_names' in all_keys) or ('cumulative_current_balance' in all_keys):
                    msg0 = msg0 + 'and your {} different bank accounts'.format(feedback['diversity']['bank_accounts'])
                else:
                    msg0 = msg0 + 'your {} different bank accounts'.format(feedback['diversity']['bank_accounts'])
            msg0 = msg0 + '.'
                



        # ADVICE

        # Case #1: there's NO error. Calculation ran smoothly
        if 'error' not in all_keys:

            # Subcase #1.1: the score is below median -> provide standard advice for improvement
            if score < score_bins[int(round(len(score_bins)/2, 0)-1)]:
                msg1= ' You can always improve your score by keeping a consistent and lively transaction history, owning a diverse set of active accunts (checking, credit, savings, investment,...), and by paying back regularly your credit card balance due.'
            
            # Subcase #1.2: the score is above median --> congratulate the user
            else:
                msg1 = ' Well done, your score is above average!'



        # Case #2: there's error(s). Either some functions broke or data is missing.       
        else: 

            # Subcase #2.1: the error is that no credit card exists
            if 'no credit card' in list(feedback['credit'].values()):
                msg1 = ' There is no credit card associated with your bank account. Credit scores rely heavily on credit card history. Improve your score by selecting a different bank account showing you own a credit line.'
            
            # Subcase #2.2: the error is elsewhere
            else:
                metrics_w_errors = [k for k in feedback.keys() if 'error' in list(feedback[k].keys())]
                msg1 =' An error occurred during computation of the metrics: {}, and your score was rounded down. Try again later or log in using a different account.'.format(', '.join(metrics_w_errors))

        # Concatenate and return message
        msg = msg0 +msg1


    return msg



# -------------------------------------------------------------------------- #
#                                  Coinbase                                  #
# -------------------------------------------------------------------------- #

def create_interpret_coinbase():
    '''
   Description:
        Initializes a dict with a concise summary to communicate and interpret the SCRTSibyl score. 
        It includes the most important metrics used by the credit scoring algorithm (for Coinbase).
    '''
    return {'score': 
    {
        'score_exist':False, \
        'points':None, \
        'quality':None, \
        'loan_amount':None, \
        'loan_duedate':None, \
        'wallet_age(days)':None, \
        'current_balance':None
        }, 
            'advice': 
    {
        'kyc_error':False, \
        'history_error':False, \
        'liquidity_error':False, \
        'activity_error':False
        }
    }





def interpret_score_coinbase(score, feedback):
    '''
    Description:
        returns a dict explaining the meaning of the numerical score
    
    Parameters:
        score (float): user's SCRTSibyl numerical score
        feedback (dict): score feedback, reporting stats on main Coinbase metrics

    Returns:
        interpret (dict): dictionaries with the major contributing score metrics 
    '''
    try:
        # Create 'interpret' dict to interpret the numerical score
        interpret = create_interpret_coinbase()


        # Score
        if ('kyc' in feedback.keys()) & (feedback['kyc']['verified']==False):
            pass
        else:
            interpret['score']['score_exist'] = True
            interpret['score']['points'] = int(round(score, 3))
            interpret['score']['quality'] = score_quality[np.digitize(score, score_bins, right=False)]
            interpret['score']['loan_amount'] = int(loan_bins[np.digitize(score, score_bins, right=False)])
            interpret['score']['loan_duedate'] = int(feedback['liquidity']['loan_duedate'])
            if ('wallet_age(days)' in list(feedback['history'].keys())) and (feedback['history']['wallet_age(days)']):
                interpret['score']['wallet_age(days)'] = feedback['history']['wallet_age(days)']
            if 'current_balance' in list(feedback['liquidity'].keys()):
                interpret['score']['current_balance'] = feedback['liquidity']['current_balance']


        # Advice
            if 'error' in list(feedback['kyc'].keys()):
                interpret['advice']['kyc_error'] = True
            if 'error' in list(feedback['history'].keys()):
                interpret['advice']['history_error'] = True
            if 'error' in list(feedback['liquidity'].keys()):
                interpret['advice']['liquidity_error'] = True
            if 'error' in list(feedback['activity'].keys()):
                interpret['advice']['activity_error'] = True


    except Exception as e:
        interpret = str(e)

    finally:
        return interpret




        

def qualitative_feedback_coinbase(score, feedback):
    '''
    Description:
        A function to format and return a qualitative description of the numerical score obtained by the user
    
    Parameters:
        score (float): user's SCRTSibyl numerical score
        feedback (dict): score feedback, reporting stats on main Coinbase metrics

    Returns:
        msg (str): qualitative message explaining the numerical score to the user. Return this message to the user in the front end of the Dapp
    '''
    # SCORE

    all_keys = [x for y in [list(feedback[k].keys()) for k in feedback.keys()] for x in y]
    # Case #1: NO score exists. Return fetch error when the Oracle did not fetch any data and computed no score
    if ('kyc' in feedback.keys()) & (feedback['kyc']['verified']==False):
        msg = 'SCRTSibyl could not calculate your credit score because there is no active wallet nor transaction history in your Coinbase account. Try to log into Coinbase with a different account.'
    
    # Case #2: a score exists. Return descriptive score feedback
    else:
        # Declare score variables
        quality = score_quality[np.digitize(score, score_bins, right=False)]
        points = int(round(score, 0))
        loan_amount = int(loan_bins[np.digitize(score, score_bins, right=False)])

        # Communicate the score
        msg0 = 'Your SCRTSibyl score is {0}, with a total of {1} points, which qualifies you for a loan of up to ${2} USD'\
                .format(quality.upper(), points, loan_amount)
        if ('loan_duedate' in list(feedback['liquidity'].keys())):
            msg0 = msg0 + ' with a recommended payback period of {0} months.'.format(feedback['liquidity']['loan_duedate'])
        else:
            msg0 = msg0 + '.'

        # Interpret the score        
        if ('wallet_age(days)' in all_keys) or ('current_balance' in all_keys):
            msg0 = msg0 + ' You obtained your score because '


            # Coinbase account duration        
            if 'wallet_age(days)' in all_keys:
                msg0 = msg0 + 'your Coinbase account has been active for {} days'.format(feedback['history']['wallet_age(days)'])
                if ('current_balance' in all_keys):
                    msg0 = msg0 + ' and'

            # Tot balance
            if  'current_balance' in all_keys:
                msg0 = msg0 + ' your total balance across all wallets is ${} USD'.format(feedback['liquidity']['current_balance'])

            msg0 = msg0 + '.'


        # ADVICE

        # Case #1: there's NO error. Calculation ran smoothly
        if 'error' not in all_keys:

            # Subcase #1.1: the score is below median -> provide standard advice for improvement
            if score < score_bins[int(round(len(score_bins)/2, 0)-1)]:
                msg1= ' You can always improve your score by trading top trusted cryptocurrencies and having a lively trading history.'
            
            # Subcase #1.2: the score is above median --> congratulate the user
            else:
                msg1 = ' Well done, your score is above average!'


        # Case #2: there's error(s). Either some functions broke or data is missing.       
        else: 

            metrics_w_errors = [k for k in feedback.keys() if 'error' in list(feedback[k].keys())]
            msg1 =' An error occurred during computation of the metrics: {}, and your score was rounded down. Try again later or log in using a different Coinbase account.'.format(', '.join(metrics_w_errors))

        # Concatenate and return message
        msg = msg0 +msg1


    return msg
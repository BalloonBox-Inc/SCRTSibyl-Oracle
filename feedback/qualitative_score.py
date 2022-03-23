
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
            interpret['score']['points'] = int(score)
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
        msg = 'Sorry! SCRTSibyl could not calculate your credit score as there is no active credit line nor transaction history associated with your bank account. Try to log into an alternative bank account if you have one.'
    

    # Case #2: a score exists. Return descriptive score feedback
    else:
        # Declare score variables
        quality = score_quality[np.digitize(score, score_bins, right=False)]
        points = int(score)
        loan_amount = int(loan_bins[np.digitize(score, score_bins, right=False)])

        # Communicate the score
        msg = 'Your SCRTSibyl score is {0} - {1} points. This score qualifies you for a sort term loan of up to ${2} USD'\
                .format(quality.upper(), points, loan_amount)
        if ('loan_duedate' in list(feedback['stability'].keys())):
            msg = msg + 'over a recommended pay back period of {0} monthly installments.'.format(feedback['stability']['loan_duedate'])
        else:
            msg = msg + '.'

        # Interpret the score        
        if ('card_names' in all_keys) or ('cumulative_current_balance' in all_keys):
            msg = msg + ' Part of your score is based on '

            # Credit cards 
            if 'card_names' in all_keys:
                msg = msg + 'the transaction history of your {} credit card'.format(', '.join([c.capitalize() for c in feedback['credit']['card_names']]))
                if len(feedback['credit']['card_names']) > 1:
                    msg = msg +'s.'
                else:
                    msg = msg +'.'

            # Tot balance now
            if  'cumulative_current_balance' in all_keys:
                msg = msg + ' Your total current balance is ${} USD across all accounts.'.format(feedback['stability']['cumulative_current_balance'])


                
        # ADVICE

        # Case #1: there's error(s). Either some functions broke or data is missing.       
        if 'error' in all_keys:

            # Subcase #1.1: the error is that no credit card exists
            if 'no credit card' in list(feedback['credit'].values()):
                msg = msg + ' SCRTSibyl found no credit card associated with your bank account. Credit scores rely heavily on credit card history. Improve your score by selecting a different bank account which shows credit history.'
            
            # Subcase #1.2: the error is elsewhere
            else:
                metrics_w_errors = [k for k in feedback.keys() if 'error' in list(feedback[k].keys())]
                msg = msg + ' An error occurred while computing your score which consists of the following metrics: {}. As a result, your score was rounded down. Try again later or select an alternative bank account if you have one.'.format(', '.join(metrics_w_errors))

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
            interpret['score']['points'] = int(score)
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
        msg = 'Sorry! SCRTSibyl could not calculate your credit score as there is no active wallet or transaction history associated with your account. Try to log into Coinbase with a different account.'
    
    # Case #2: a score exists. Return descriptive score feedback
    else:
        # Declare score variables
        quality = score_quality[np.digitize(score, score_bins, right=False)]
        points = int(score)
        loan_amount = int(loan_bins[np.digitize(score, score_bins, right=False)])

        # Communicate the score
        msg = 'Your SCRTSibyl score is {0} - {1} points. This qualifies you for a short term loan of up to ${2} USD'\
                .format(quality.upper(), points, loan_amount)
        if ('loan_duedate' in list(feedback['liquidity'].keys())):
            msg = msg + ' over a recommended pay back period of {0} monthly installments.'.format(feedback['liquidity']['loan_duedate'])
        else:
            msg = msg + '.'


        # Coinbase account duration        
        if ('wallet_age(days)' in all_keys):
            if ('current_balance' in all_keys):
                msg = msg + ' Your Coinbase account has been active for {} days and your total balance across all wallets is ${} USD.'.format(feedback['history']['wallet_age(days)'], feedback['liquidity']['current_balance'])
            else: 
                msg = msg + ' Your Coinbase account has been active for {} days.'.format(feedback['history']['wallet_age(days)'])
        
        # Tot balance
        else:
            if ('current_balance' in all_keys):
                msg = msg + ' Your total balance across all wallets is ${} USD.'.format(feedback['liquidity']['current_balance'])
            else:
                pass



        # ADVICE

        # Case #1: there's error(s). Either some functions broke or data is missing.       
        if 'error' in all_keys:
            metrics_w_errors = [k for k in feedback.keys() if 'error' in list(feedback[k].keys())]
            msg = msg + ' An error occurred while computing your score which consists of the following metrics: {}. As a result, your score was rounded down. Try to log into Coinbase again later.'.format(', '.join(metrics_w_errors))

    return msg
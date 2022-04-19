import unittest
from app_route import *
from support.metrics_plaid import *
from dotenv import dotenv_values



# Helper function -fetch data for testing
def hit_plaid_api(plaid_client_id, plaid_client_secret, plaid_token):
    '''import Plaid Sandbox data'''
    try:
        # client connection
        client = plaid_client('sandbox', plaid_client_id, plaid_client_secret)

        # data fetching and formatting
        plaid_txn = plaid_transactions(plaid_token, client, 360)
        if 'error' in plaid_txn:
            raise Exception(plaid_txn['error']['message'])

        tx = {k:v for k,v in plaid_txn.items() if k in ['accounts', 'item', 'transactions']}
        tx['transactions'] = [t for t in tx['transactions'] if not t['pending']]

    except Exception as e:
        tx = str(e)

    finally:
        return tx


# -------------------------------------------------------------------------- #
#                                  FIXTURES                                  #
#                         - create data to be used as -                      #
#                - input parameters for our testing functions -              #
# -------------------------------------------------------------------------- # 

load_dotenv()
config = dotenv_values()
good_data = hit_plaid_api(config['PLAID_CLIENT_ID'], config['PLAID_CLIENT_SECRET'], config['PLAID_ACCESS_TOKEN'])
good_fb = create_feedback_plaid()



# -------------------------------------------------------------------------- #
#                                TEST CASES                                  #
#                - test core functions of Coinbase algorithm -               #
# -------------------------------------------------------------------------- # 

class TestMetricCredit(unittest.TestCase):

    def test_credit_mix(self):
        '''
        - ensure we remove the word 'credit' from the credit card names 
        - ensure we store the names of ALL owned credit cards
        - if a user owns no credit card, then raise exception 'no credit card'
        '''
        self.assertNotIn('credit', credit_mix(good_data, good_fb))
        self.assertEqual(len(credit_mix.credit), len(credit_mix.card_names))
        self.assertIn('error', credit_mix([], good_fb)[1]['credit'].keys())


    def test_credit_limit(self):
        '''
        - return a float for the credit limit
        - if a user's credit limit is not defined, then raise exception
        '''
        self.assertIsInstance(credit_limit(good_data, good_fb)[1]['credit']['credit_limit'], (float, int))
        self.assertIn('error', credit_limit([], good_fb)[1]['credit'].keys())


    def test_credit_util_ration(self):
        '''
        - if there's good credit data, it should return a credit utilization ratio, as a float >= 0.3
        - the credit util ration should be at most 2 (if exceeds this upper bound, then something's wrong)
        - ensure bad data returns an error
        '''
        a = credit_util_ratio(good_data, good_fb)

        if dynamic_select(good_data, 'credit', good_fb)['id'] != 'inexistent':
            self.assertIn('utilization_ratio', a[1]['credit'].keys())
            self.assertIsInstance(a[1]['credit']['utilization_ratio'], (float, int))
            self.assertGreaterEqual(a[0], 0.3)
        self.assertLess(a[0], 2)
        self.assertIn('error', a[1]['credit'].keys())


    def test_credit_interest(self):
        '''
        - Plaid Sandbox data has an impeccable credit card pedigree and thus should score 1/1
        - bad data should raise an exception
        '''
        self.assertEqual(credit_interest(good_data, good_fb)[0], 1)
        self.assertIn('error',  credit_interest([], good_fb)[1]['credit'].keys())


    def test_credit_length(self):
        '''
        - length should be of type float OR int
        - if a credit card exists, then there should be a positive length
        - bad data should raise an exception
        '''
        a = credit_length(good_data, good_fb)

        if dynamic_select(good_data, 'credit', good_fb)['id']:
            self.assertIsInstance(a[1]['credit']['credit_duration_(days)'], (float, int))
            self.assertGreater(a[1]['credit']['credit_duration_(days)'], 0)
        self.assertIn('error', credit_length([], good_fb)[1]['credit'].keys())


    def test_credit_livelihood(self):
        '''
        - if there exist a non-empty dataframe containing the txn means, then the mean should be positive
        - bad data should raise an error
        '''
        a = credit_livelihood(good_data, good_fb)
        if len(credit_livelihood.d):
            self.assertGreater(a[1]['credit']['avg_count_monthly_txn'], 0)
        self.assertIn('error', a[1]['credit'].keys())


class TestMetricVelocity(unittest.TestCase):

    def test_velocity_withdrawals(self):
        pass

    def test_velocity_deposits(self):
        pass

    def test_velocity_month_net_flow(self):
        pass

    def test_velocity_month_txn_count(self):
        pass

    def test_velocity_slope(self):
        pass



class TestMetricStability(unittest.TestCase):

    def test_stability_tot_balance_now(self):
        pass
    
    def test_stability_min_running_balance(self):
        pass

    def test_stability_loan_duedate(self):
        pass



class TestMetricDiversity(unittest.TestCase):

    def test_diversity_account(self):
        pass

    def test_diversity_profile(self):
        pass


# -------------------------------------------------------------------------- #
#                            PARAMETRIZATION                                 #
#            - run same tests, passing different values each time -          #
#                    - and expecting the same result -                       #
# -------------------------------------------------------------------------- # 

class TestParametrizeOutput(unittest.TestCase):
    '''
    The TestParametrizeOutput object checks that ALL functions 
    of our Coinbase algorithm ALWAYS return a tuple comprising of:
    - an int (i.e., the score)
    - a dict (i.e., the feedback)
    It also checks that the score is ALWAYS in the range [0, 1]
    Finally, it checks that even when all args are NoneTypes, th output is still a tuple
    '''
    def test_output_good(self):
        pass

    def test_output_empty(self):
        pass

if __name__ == '__main__':
    unittest.main()

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
        - bad data should raise an exception because the dynamic_select() function will break
        '''
        self.assertEqual(credit_interest(good_data, good_fb)[0], 1)
        self.assertIn('dynamic_select',  credit_interest([], good_fb)[1]['fetch'].keys())


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
        '''
        - passing a feedback of NoneType, returns a feedback of NoneType too
        - good data but without withdrawals raises the 'no withdrawals' exception
        - bad data returns an error
        '''
        self.assertIsNone(velocity_withdrawals(good_data, None)[1])
        self.assertRegex(velocity_withdrawals(good_data, good_fb)[1]['velocity']['error'], 'no withdrawals')
        self.assertIn('error', velocity_withdrawals([], good_fb)[1]['velocity'].keys())


    def test_velocity_deposits(self):
        '''
        - if there are some 'payroll' trasactions, then the score should be positive
        - bad data returns an error
        '''
        a = velocity_deposits(good_data, good_fb)

        if [t for t in good_data['transactions'] if t['amount'] < -200 and 'payroll' in [x.lower() for x in t['category']]]:
            self.assertGreater(a[0], 0)
        self.assertRegex(a[1]['velocity']['error'], 'no deposits')


    def test_velocity_month_net_flow(self):
        pass


    def test_velocity_month_txn_count(self):
        '''
        - if there is a legit checking account, then the score should be positive
        '''
        checking_acc = [a['account_id'] for a in good_data['accounts'] if a['subtype'].lower()=='checking']
        if [t for t in good_data['transactions'] if t['account_id'] in checking_acc]:
            self.assertGreater(velocity_month_txn_count(good_data, good_fb)[0], 0)
    

    def test_velocity_slope(self):
        pass




class TestMetricStability(unittest.TestCase):

    def test_stability_tot_balance_now(self):
        '''
        - if tot balance variable exists, then the score should be > 0
        - no account data returns an error
        '''
        a = stability_tot_balance_now(good_data, good_fb)
        if stability_tot_balance_now.balance:
            self.assertGreater(a[0], 0)
        self.assertIn('error', stability_tot_balance_now([], good_fb)[1]['stability'].keys())

    
    def test_stability_min_running_balance(self):
        pass
        

    def test_stability_loan_duedate(self):
        '''
        - this function's output should be a feedback dict
        - the max allowed loan duedate is 6 months
        - feeding NoneTypes as function parameters should still return a feedback dict containing an error message
        '''
        a = stability_loan_duedate(good_data, good_fb)
        self.assertIsInstance(a, dict)
        self.assertLessEqual(a['stability']['loan_duedate'], 6)
        self.assertIn('error', stability_loan_duedate(None, good_fb)['stability'].keys())




class TestMetricDiversity(unittest.TestCase):

    def test_diversity_acc_count(self):
        '''
        - if one of the accounts was active for more than 4 months (120 days) --> score should be > 0.25/1
        - users with at least 2 accounts get a positive score
        - missing data raises an exception
        '''
        a = diversity_acc_count(good_data, good_fb)

        if (datetime.now().date() - good_data['transactions'][-1]['date']).days > 120:
            self.assertGreater(a[0], 0.25)
        if len(good_data['accounts']) >= 2:
            self.assertGreater(a[0], 0)
        self.assertRaises(TypeError, 'tuple indices must be integers or slices, not str', diversity_acc_count, (None, good_fb))


    def test_diversity_profile(self):
        '''
        - if user owns an investmenr of saving account, score will be > 0.17
        - Plaid Sandbox data should score 1/1 
        '''
        bonus_acc = ['401k', 'cd', 'money market', 'mortgage', 'student', 'isa', 'ebt', 'non-taxable brokerage account', 'rdsp', 'rrif', 'pension', 'retirement', 'roth', 'roth 401k', 'stock plan', 'tfsa', 'trust', 'paypal', 'savings', 'prepaid', 'business', 'commercial', 'construction', 'loan', 'cash management', 'mutual fund', 'rewards']
        if [a['account_id'] for a in good_data['accounts'] if a['subtype'] in bonus_acc]:
            self.assertGreaterEqual(diversity_profile(good_data, good_fb)[0], 0.17)
        self.assertEqual(diversity_profile(good_data, good_fb)[0], 1)

    def test_helper_dynamic_select(self):
        '''
        - ensure the output is a dict with 2 keys
        - if there exists at least one credit OR one checking account, then the output should return that id as best account
        - bad data should still return a dict with 'inexistent' id for the best account
        (Notice that 'credit' and 'checking' are used interchangeably here and are both equally valid input parameters)
        '''
        a = dynamic_select(good_data, 'credit', good_fb)
        b = dynamic_select([], 'credit', good_fb)
        c = dynamic_select(None, 'credit', good_fb)
        fn = [a,b,c]

        for x in fn:
            with self.subTest():
                self.assertIsInstance(x, dict)

        self.assertEqual(len(a.keys()), 2)
        self.assertIs(dynamic_select([], 'checking', good_fb)['id'], 'inexistent')


    def test_helper_flows(self):
        pass

    def test_helper_balance_now_checking_only(self):
        pass


# -------------------------------------------------------------------------- #
#                            PARAMETRIZATION                                 #
#            - run same tests, passing different values each time -          #
#                    - and expecting the same result -                       #
# -------------------------------------------------------------------------- # 
arg = {
    'good': {'data':good_data, 'feedback':good_fb},
    'empty': {'data':[], 'feedback':good_fb},
    'none': {'data':None, 'feedback':good_fb},
}

func = {
    'fn_good': [
        credit_mix,
        credit_limit,
        credit_util_ratio,
        credit_interest,
        credit_length,
        credit_livelihood,
        velocity_withdrawals,
        velocity_deposits,
        velocity_month_net_flow,
        velocity_month_txn_count,
        velocity_slope,
        stability_tot_balance_now,
        stability_min_running_balance,
        diversity_acc_count,
        diversity_profile
        ]
}

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
        for f in func['fn_good']:
            z  = f(**arg['good'])
            with self.subTest():
                self.assertIsInstance(z, tuple)
                self.assertLessEqual(z[0], 1)
                self.assertIsInstance(z[0], (float, int))
                self.assertIsInstance(z[1], dict)

    def test_output_empty(self):
        for f in func['fn_good']:
            z  = f(**arg['empty'])
            with self.subTest():
                self.assertIsInstance(z, tuple)
                self.assertEqual(z[0], 0)
                self.assertIsInstance(z[0], (float, int))
                self.assertIsInstance(z[1], dict)

    def test_output_none(self):
        for f in func['fn_good']:
            z  = f(**arg['none'])
            with self.subTest():
                self.assertIsInstance(z, tuple)
                self.assertIsNotNone(z[0])
                self.assertIsInstance(z[1], dict)


if __name__ == '__main__':
    unittest.main()
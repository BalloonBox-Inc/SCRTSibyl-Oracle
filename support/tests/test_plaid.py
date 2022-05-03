import json
import unittest
from datetime import datetime
from ..metrics_plaid import *  # import code to get tested


# -------------------------------------------------------------------------- #
#                               Helper Functions                             #
#                                                                            #
# -------------------------------------------------------------------------- #

def create_feedback_plaid():
    return {'fetch': {}, 'credit': {}, 'velocity': {}, 'stability': {}, 'diversity': {}}


def str_to_datetime(plaid_txn, feedback):
    """
    serialize a Python data structure converting string instances into datetime objects
            Parameters:
                plaid_txn (list): locally stored Plaid data used for testing purposes
            Returns:
                tx (dict): serialized dict containing user accounts and transactions. String dates are converted to datetime objects
     """
    try:
        # Keep only completed transactions (filter out pending transactions)
        all_txn = []
        for t in plaid_txn['transactions']:
            if t['pending'] == False:
                t['date'] = datetime.strptime(t['date'], '%Y-%m-%d').date()
                all_txn.append(t)

        # Prettify and write to json
        tx = {'accounts': plaid_txn['accounts'],  'transactions': all_txn}
        return tx

    except Exception as e:
        feedback['fetch'][str_to_datetime.__name__] = str(e)


# -------------------------------------------------------------------------- #
#                      some state-based UNIT TEST CASES                      #
#                - test core functions of Coinbase algorithm -               #
# -------------------------------------------------------------------------- #

class TestMetricCredit(unittest.TestCase):

    # factor out set-up code implementing the setUp() method
    def setUp(self):
        self.fb = create_feedback_plaid()
        with open('data/test_user_plaid.json') as my_file:
            self.data = str_to_datetime(json.load(my_file), self.fb)

    # clean up code at the end of this test class
    def tearDown(self):
        self.fb = None
        self.data = None

    def test_credit_mix(self):
        '''
        - ensure we remove the word 'credit' from the credit card names 
        - ensure we store the names of ALL owned credit cards
        - if a user owns no credit card, then raise exception 'no credit card'
        '''
        self.assertNotIn('credit', credit_mix(self.data, self.fb))
        self.assertEqual(len(credit_mix.credit), len(credit_mix.card_names))
        self.assertIn('error', credit_mix([], self.fb)[1]['credit'].keys())

    def test_credit_limit(self):
        '''
        - return a float for the credit limit
        - if a user's credit limit is not defined, then raise exception
        '''
        self.assertIsInstance(credit_limit(self.data, self.fb)[
                              1]['credit']['credit_limit'], (float, int))
        self.assertIn('error', credit_limit([], self.fb)[1]['credit'].keys())

    def test_credit_util_ratio(self):
        '''
        - if there's good credit data, it should return a credit utilization ratio, as a float >= 0.3
        - the credit util ration should be at most 2 (if exceeds this upper bound, then something's wrong)
        - ensure bad data returns an error
        '''
        a = credit_util_ratio(self.data, self.fb)

        if dynamic_select(self.data, 'credit', self.fb)['id'] != 'inexistent':
            self.assertIn('utilization_ratio', a[1]['credit'].keys())
            self.assertIsInstance(
                a[1]['credit']['utilization_ratio'], (float, int))
            self.assertGreaterEqual(a[0], 0.3)
        self.assertLess(a[0], 2)

        self.assertIn('error', credit_util_ratio(
            [], self.fb)[1]['credit'].keys())

    def test_credit_interest(self):
        '''
        - Plaid Sandbox data has an impeccable credit card pedigree and thus should score 1/1
        - bad data should raise an exception because the dynamic_select() function will break
        '''
        self.assertEqual(credit_interest(self.data, self.fb)[0], 1)
        self.assertIn('dynamic_select',  credit_interest(
            [], self.fb)[1]['fetch'].keys())

    def test_credit_length(self):
        '''
        - length should be of type float OR int
        - if a credit card exists, then there should be a positive length
        - bad data should raise an exception
        '''
        a = credit_length(self.data, self.fb)

        if dynamic_select(self.data, 'credit', self.fb)['id']:
            self.assertIsInstance(
                a[1]['credit']['credit_duration_(days)'], (float, int))
            self.assertGreater(a[1]['credit']['credit_duration_(days)'], 0)
        self.assertIn('error', credit_length([], self.fb)[1]['credit'].keys())

    def test_credit_livelihood(self):
        '''
        - if there exist a non-empty dataframe containing the txn means, then the mean should be positive
        - bad data should raise an error
        '''
        a = credit_livelihood(self.data, self.fb)
        if len(credit_livelihood.d):
            self.assertGreater(a[1]['credit']['avg_count_monthly_txn'], 0)
        self.assertIn('error', credit_livelihood(
            [], self.fb)[1]['credit'].keys())


class TestMetricVelocity(unittest.TestCase):

    def setUp(self):
        self.fb = create_feedback_plaid()
        with open('data/test_user_plaid.json') as my_file:
            self.data = str_to_datetime(json.load(my_file), self.fb)

    def tearDown(self):
        self.fb = None
        self.data = None

    def test_velocity_withdrawals(self):
        '''
        - passing a feedback of NoneType, returns a feedback of NoneType too
        - good data but without withdrawals raises the 'no withdrawals' exception
        - bad data returns an error
        '''
        self.assertIsNone(velocity_withdrawals(self.data, None)[1])
        self.assertRegex(velocity_withdrawals(self.data, self.fb)[
                         1]['velocity']['error'], 'no withdrawals')
        self.assertIn('error', velocity_withdrawals(
            [], self.fb)[1]['velocity'].keys())

    def test_velocity_deposits(self):
        '''
        - if there are some 'payroll' trasactions, then the score should be positive
        - bad data returns an error
        '''
        a = velocity_deposits(self.data, self.fb)

        if [t for t in self.data['transactions'] if t['amount'] < -200 and 'payroll' in [x.lower() for x in t['category']]]:
            self.assertGreater(a[0], 0)
        self.assertRegex(a[1]['velocity']['error'], 'no deposits')

    def test_velocity_month_net_flow(self):
        '''
        - the avg net flow should be a large positive integer
        - bad input data results into an error
        '''
        self.assertGreater(velocity_month_net_flow(self.data, self.fb)[
                           1]['velocity']['avg_net_flow'], 0)
        self.assertIn('error', velocity_month_net_flow(
            [], self.fb)[1]['velocity'].keys())

    def test_velocity_month_txn_count(self):
        '''
        - if there is a legit checking account, then the score should be positive
        '''
        checking_acc = [a['account_id']
                        for a in self.data['accounts'] if a['subtype'].lower() == 'checking']
        if [t for t in self.data['transactions'] if t['account_id'] in checking_acc]:
            self.assertGreater(velocity_month_txn_count(
                self.data, self.fb)[0], 0)

    def test_velocity_slope(self):
        '''
        - if there's more than 10 datapoint for months of transaction history, then the algo should persom linear regression
            otherwise it'll simply calculate the monthly flow as 2 rations
        - bad input data returns error
        '''
        if len(flows(self.data, 24, self.fb)) >= 10:
            self.assertIn('slope', velocity_slope(
                self.data, self.fb)[1]['velocity'].keys())
        else:
            self.assertIn('monthly_flow', velocity_slope(
                self.data, self.fb)[1]['velocity'].keys())

        self.assertIn('error', velocity_slope(
            [], self.fb)[1]['velocity'].keys())


class TestMetricStability(unittest.TestCase):

    def setUp(self):
        self.fb = create_feedback_plaid()
        with open('data/test_user_plaid.json') as my_file:
            self.data = str_to_datetime(json.load(my_file), self.fb)

    def tearDown(self):
        self.fb = None
        self.data = None

    def test_stability_tot_balance_now(self):
        '''
        - if tot balance variable exists, then the score should be > 0
        - no account data returns an error
        '''
        a = stability_tot_balance_now(self.data, self.fb)

        if stability_tot_balance_now.balance:
            self.assertGreater(a[0], 0)
        self.assertIn('error', stability_tot_balance_now(
            [], self.fb)[1]['stability'].keys())

    def test_stability_min_running_balance(self):
        '''
        - check 'timeframe' of txn history for min running balances to be an int
        - good data should return 2 dict keys under the 'stability' scope of the 'feedback' dict
        - bad input data should return error
        '''
        a = stability_min_running_balance(self.data, self.fb)

        self.assertIsInstance(a[1]['stability']['min_running_timeframe'], int)
        self.assertEqual(['min_running' in x for x in a[1]
                         ['stability']].count(True), 2)
        self.assertIn('error', stability_min_running_balance(
            [], self.fb)[1]['stability'].keys())

    def test_stability_loan_duedate(self):
        '''
        - this function's output should be a feedback dict
        - the max allowed loan duedate is 6 months
        - feeding NoneTypes as function parameters should still return a feedback dict containing an error message
        '''
        a = stability_loan_duedate(self.data, self.fb)
        self.assertIsInstance(a, dict)
        self.assertLessEqual(a['stability']['loan_duedate'], 6)
        self.assertRegex(stability_loan_duedate(None, self.fb)[
                         'stability']['error'], "'NoneType' object is not subscriptable")


class TestMetricDiversity(unittest.TestCase):

    def setUp(self):
        self.fb = create_feedback_plaid()
        with open('data/test_user_plaid.json') as my_file:
            self.data = str_to_datetime(json.load(my_file), self.fb)

    def tearDown(self):
        self.fb = None
        self.data = None

    def test_diversity_acc_count(self):
        '''
        - if one of the accounts was active for more than 4 months (120 days) --> score should be > 0.25/1
        - users with at least 2 accounts get a positive score
        - missing data raises an exception
        '''
        a = diversity_acc_count(self.data, self.fb)

        if (datetime.now().date() - self.data['transactions'][-1]['date']).days > 120:
            self.assertGreater(a[0], 0.25)
        if len(self.data['accounts']) >= 2:
            self.assertGreater(a[0], 0)
        self.assertRaises(TypeError, 'tuple indices must be integers or slices, not str',
                          diversity_acc_count, (None, self.fb))

    def test_diversity_profile(self):
        '''
        - if user owns an investmenr of saving account, score will be > 0.17
        - Plaid Sandbox data should score 1/1 
        '''
        bonus_acc = ['401k', 'cd', 'money market', 'mortgage', 'student', 'isa', 'ebt', 'non-taxable brokerage account', 'rdsp', 'rrif', 'pension', 'retirement', 'roth',
                     'roth 401k', 'stock plan', 'tfsa', 'trust', 'paypal', 'savings', 'prepaid', 'business', 'commercial', 'construction', 'loan', 'cash management', 'mutual fund', 'rewards']
        if [a['account_id'] for a in self.data['accounts'] if a['subtype'] in bonus_acc]:
            self.assertGreaterEqual(
                diversity_profile(self.data, self.fb)[0], 0.17)
        self.assertEqual(diversity_profile(self.data, self.fb)[0], 1)


class TestHelperFunctions(unittest.TestCase):

    def setUp(self):
        self.fb = create_feedback_plaid()
        with open('data/test_user_plaid.json') as my_file:
            self.data = str_to_datetime(json.load(my_file), self.fb)

    def tearDown(self):
        self.fb = None
        self.data = None

    def test_dynamic_select(self):
        '''
        - ensure the output is a dict with 2 keys
        - if there exists at least one credit OR one checking account, then the output should return that id as best account
        - bad data should still return a dict with 'inexistent' id for the best account
        (Notice that 'credit' and 'checking' are used interchangeably here and are both equally valid input parameters)
        '''
        a = dynamic_select(self.data, 'credit', self.fb)
        b = dynamic_select([], 'credit', self.fb)
        c = dynamic_select(None, 'credit', self.fb)
        fn = [a, b, c]

        for x in fn:
            with self.subTest():
                self.assertIsInstance(x, dict)

        self.assertEqual(len(a.keys()), 2)
        self.assertIs(dynamic_select([], 'checking', self.fb)
                      ['id'], 'inexistent')

    def test_flows(self):
        '''
        - check output Type is pandas DataFrame
        - if you want to retrieve data history for the last, say, 6 months, then the output should have length of 6
        - bad input data should return a NoneType
        - bad input parameters should return an error in feedback['fetch']
        '''
        a = flows(self.data, 6, self.fb)
        b = flows([], 6, self.fb)
        c = flows(None, 6, self.fb)

        self.assertIsInstance(a, pd.DataFrame)
        self.assertEqual(len(a), 6)

        for df in [b, c]:
            self.assertIsNone(df)
            self.assertIn('flows', self.fb['fetch'].keys())

    def test_balance_now_checking_only(self):
        '''
        - check balance against expected value
        - output should be of type float or int
        - bad input data should return an error
        '''
        b = balance_now_checking_only(self.data, self.fb)
        expected_b = sum([a['balances']['current']
                         for a in self.data['accounts'] if a['subtype'] == 'checking'])

        self.assertEqual(b, expected_b)
        self.assertIsInstance(b, (float, int))

        balance_now_checking_only([], self.fb)
        self.assertIn('balance_now_checking_only', self.fb['fetch'].keys())


# -------------------------------------------------------------------------- #
#                            PARAMETRIZATION                                 #
#            - run same tests, passing different values each time -          #
#                    - and expecting the same result -                       #
# -------------------------------------------------------------------------- #

class TestParametrizePlaid(unittest.TestCase):
    '''
    The TestParametrizeOutput object checks that ALL functions 
    of our Coinbase algorithm ALWAYS return a tuple comprising of:
    - an int (i.e., the score)
    - a dict (i.e., the feedback)
    It also checks that the score is ALWAYS in the range [0, 1]
    Finally, it checks that even when all args are NoneTypes, th output is still a tuple
    '''

    def setUp(self):
        self.fb = create_feedback_plaid()

        with open('data/test_user_plaid.json') as my_file:
            self.data = str_to_datetime(json.load(my_file), self.fb)

        self.arg = {
            'good': {'data': self.data, 'feedback': self.fb},
            'empty': {'data': [], 'feedback': self.fb},
            'none': {'data': None, 'feedback': self.fb}
        }

        self.func = {
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
                diversity_profile]
        }

    def tearDown(self):
        self.fb = None
        self.data = None
        self.arg = None
        self.func = None

    def test_output_good(self):
        for f in self.func['fn_good']:
            z = f(**self.arg['good'])
            with self.subTest():
                self.assertIsInstance(z, tuple)
                self.assertLessEqual(z[0], 1)
                self.assertIsInstance(z[0], (float, int))
                self.assertIsInstance(z[1], dict)

    def test_output_empty(self):
        for f in self.func['fn_good']:
            z = f(**self.arg['empty'])
            with self.subTest():
                self.assertIsInstance(z, tuple)
                self.assertEqual(z[0], 0)
                self.assertIsInstance(z[0], (float, int))
                self.assertIsInstance(z[1], dict)

    def test_output_none(self):
        for f in self.func['fn_good']:
            z = f(**self.arg['none'])
            with self.subTest():
                self.assertIsInstance(z, tuple)
                self.assertIsNotNone(z[0])
                self.assertIsInstance(z[1], dict)


if __name__ == '__main__':
    unittest.main()

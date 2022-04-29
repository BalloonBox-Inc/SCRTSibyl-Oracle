import json
import unittest
from datetime import datetime
from ..metrics_coinbase import *  # import testing code


# -------------------------------------------------------------------------- #
#                               Helper Functions                             #
#                                                                            #
# -------------------------------------------------------------------------- #

def create_feedback_coinbase():
    return {'kyc': {}, 'history': {}, 'liquidity': {}, 'activity': {}}


def str_to_date(acc, feedback):
    """
    serialize a Python data structure converting string instances into datetime objects
            Parameters:
                tx (list): locally stored Coinbase data. Either account OR transactions data
            Returns:
                all_txn (list): serialized list containing user accounts OR transactions. String dates are converted to datetime objects
     """
    try:
        converted = []
        for x in acc:
            if x['created_at']:
                x['created_at'] = datetime.strptime(
                    x['created_at'], '%Y-%m-%dT%H:%M:%SZ').date()
                converted.append(x)

        return converted

    except Exception as e:
        feedback['kyc'][str_to_date.__name__] = str(e)


# -------------------------------------------------------------------------- #
#                                TEST CASES                                  #
#                - test core functions of Coinbase algorithm -               #
# -------------------------------------------------------------------------- #

class TestMetricsCoinbase(unittest.TestCase):

    # factor out set-up code implementing the setUp() method
    def setUp(self):
        self.fb = create_feedback_coinbase()
        with open('data/test_user_coinbase.json') as my_file:
            self.acc = str_to_date(json.load(my_file)['accounts'], self.fb)
        with open('data/test_user_coinbase.json') as my_file:
            self.tx = json.load(my_file)['transactions']

    # clean up code at the end of this test class
    def tearDown(self):
        self.fb = None
        self.acc = None
        self.tx = None

    def test_kyc(self):
        '''
        - ensure the output is always a tuple (int, dict)
        - ensure the output is never NoneType, even when parsing NoneTypes
        - ensure returns full score of 1 when good args are passed to the fn
        '''
        bad_fb = {'history': {}, 'liquidity': {}, 'activity': {}}
        badkyc = kyc(None, None, bad_fb)

        self.assertIsInstance(badkyc, tuple)
        self.assertIsInstance(badkyc[0], int)
        self.assertIsInstance(badkyc[1], dict)
        self.assertIsNotNone(kyc(None, None, None))
        self.assertEqual(kyc(self.acc, self.tx, self.fb)[0], 1)

    def test_history_acc_longevity(self):
        '''
        - variable 'age' should be a non-negative of type: int or float
        - if there's no account, the score should be 0
        '''
        history_acc_longevity(self.acc, self.fb)

        self.assertGreaterEqual(history_acc_longevity.age, 0)
        self.assertIsInstance(history_acc_longevity.age, (int, float))
        self.assertEqual(history_acc_longevity([], self.fb)[0], 0)

    def test_liquidity_tot_balance_now(self):
        '''
        - empty account should result in 'no balance' error
        '''
        self.assertRegex(liquidity_tot_balance_now([], self.fb)[
                         1]['liquidity']['error'], 'no balance')

    def test_liquidity_loan_duedate(self):
        '''
        - duedate should be at most 6 months
        - this is the only function that returns no score, but rather, it returns only the feedback dict
        '''
        self.assertLessEqual(liquidity_loan_duedate(self.tx, self.fb)[
                             'liquidity']['loan_duedate'], 6)
        self.assertIsInstance(liquidity_loan_duedate(self.tx, self.fb), dict)

    def test_liquidity_avg_running_balance(self):
        '''
        - no tx yields a 'no tx' error
        '''
        self.assertRegex(liquidity_avg_running_balance(self.acc, [], self.fb)[
                         1]['liquidity']['error'], 'no transaction history')

    def test_activity_tot_volume_tot_count(self):
        '''
        - tot_volume should be of type int or float
        - tot_volume should be non-negative
        - credit and debit checks share the same dictionary key
        - no tx returns 'no tx history' error
        '''
        fb = create_feedback_coinbase()
        cred, cred_fb = activity_tot_volume_tot_count(self.tx, 'credit', fb)
        deb, deb_fb = activity_tot_volume_tot_count(self.tx, 'debit', fb)

        for a in [cred, deb]:
            self.assertIsInstance(a, (float, int))
            self.assertGreaterEqual(a, 0)

        self.assertEqual(cred_fb['activity'].get(
            'credit').keys(), deb_fb['activity'].get('debit').keys())
        self.assertRegex(activity_tot_volume_tot_count([], 'credit', self.fb)[
                         1]['activity']['error'], 'no transaction history')

    def test_activity_consistency(self):
        '''
        - ensure you've accounted for all registered txns
        - ensure txn dates are of Type datetime (perform Type check on randomly chosen date)
        - avg volume should be a positive number
        - no tx returns 'no tx history' error
        '''
        a, b = activity_consistency(self.tx, 'credit', self.fb)
        i = list(activity_consistency.frame.index)
        d = [x[0] for x in activity_consistency.typed_txn]

        self.assertCountEqual(i, d)
        self.assertIsInstance(np.random.choice(d), datetime)
        self.assertGreater(a, 0)
        self.assertRegex(activity_consistency([], 'credit', self.fb)[
                         1]['activity']['error'], 'no transaction history')

    def test_activity_profit_since_inception(self):
        '''
        - 'profit' variable should be a float or int
        - 'profit' should be positive
        - if there's no profit, then should raise an exception
        '''
        activity_profit_since_inception(self.acc, self.tx, self.fb)

        self.assertIsInstance(
            activity_profit_since_inception.profit, (float, int))
        self.assertGreater(activity_profit_since_inception.profit, 0)
        self.assertRegex(activity_profit_since_inception([], [], self.fb)[
                         1]['activity']['error'], 'no net profit')

    def test_net_flow(self):
        '''
        - output should be of type tuple(DataFrame, dict)
        - bad input parameters should raise and exception       
        '''
        a = net_flow(self.tx, 12, self.fb)
        b = net_flow([], 6, self.fb)
        c = net_flow(None, 6, create_feedback_coinbase())

        # good inputs
        self.assertIsInstance(a, tuple)
        self.assertIsInstance(a[0], pd.core.frame.DataFrame)
        self.assertIsInstance(a[1], dict)

        # bad inputs
        self.assertEqual(len(b[0]), len(c[0]))
        self.assertRegex(b[1]['liquidity']['error'], 'no consistent net flow')
        self.assertRegex(c[1]['liquidity']['error'],
                         "'NoneType' object is not iterable")


# -------------------------------------------------------------------------- #
#                            PARAMETRIZATION                                 #
#            - run same tests, passing different values each time -          #
#                    - and expecting the same result -                       #
# -------------------------------------------------------------------------- #

class TestParametrizeCoinbase(unittest.TestCase):
    '''
    The TestParametrizeOutput object checks that ALL functions 
    of our Coinbase algorithm ALWAYS return a tuple comprising of:
    - an int (i.e., the score)
    - a dict (i.e., the feedback)
    It also checks that the score is ALWAYS in the range [0, 1]
    Finally, it checks that even when all args are NoneTypes, th output is still a tuple
    '''

    def setUp(self):
        self.fb = create_feedback_coinbase()
        with open('data/test_user_coinbase.json') as my_file:
            self.acc = str_to_date(json.load(my_file)['accounts'], self.fb)
        with open('data/test_user_coinbase.json') as my_file:
            self.tx = json.load(my_file)['transactions']

        self.param = {
            'fn_good': [
                kyc(self.acc, self.tx, self.fb),
                history_acc_longevity(self.acc, self.fb),
                liquidity_avg_running_balance(self.acc, self.tx, self.fb),
                liquidity_tot_balance_now(self.acc, self.fb),
                activity_consistency(self.tx, 'credit', self.fb),
                activity_consistency(self.tx, 'debit', self.fb),
                activity_tot_volume_tot_count(self.tx, 'credit', self.fb),
                activity_tot_volume_tot_count(self.tx, 'debit', self.fb),
                activity_profit_since_inception(self.acc, self.tx, self.fb)],
            'fn_empty': [
                kyc([], None, self.fb),
                history_acc_longevity(None, self.fb),
                liquidity_avg_running_balance([], [], self.fb),
                liquidity_tot_balance_now(None, self.fb),
                activity_consistency([], None, self.fb),
                activity_consistency([], [], self.fb),
                activity_tot_volume_tot_count([], None, self.fb),
                activity_tot_volume_tot_count(None, [], self.fb),
                activity_profit_since_inception(None, None, self.fb)
            ]}

    def tearDown(self):
        for y in [self.fb, self.acc, self.tx, self.param]:
            y = None

    def test_output_good(self):
        for x in self.param['fn_good']:
            with self.subTest():
                self.assertIsInstance(x, tuple)
                self.assertLessEqual(x[0], 1)
                self.assertIsInstance(x[0], (float, int))
                self.assertIsInstance(x[1], dict)

    def test_output_empty(self):
        for x in self.param['fn_empty']:
            with self.subTest():
                self.assertIsInstance(x, tuple)
                self.assertEqual(x[0], 0)
                self.assertIsInstance(x[0], (float, int))
                self.assertIsInstance(x[1], dict)


if __name__ == '__main__':
    unittest.main()

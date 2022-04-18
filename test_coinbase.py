import unittest
from app_route import *
from local.local_helper import str_to_date
from support.metrics_coinbase import *



# -------------------------------------------------------------------------- #
#                                  FIXTURES                                  #
# -------------------------------------------------------------------------- # 

# good data
good_fb = create_feedback_coinbase()
good_acc = str_to_date(json.load(open('test_user_coinbase.json'))['accounts'], good_fb)
good_tx = json.load(open('test_user_coinbase.json'))['transactions']

# -------------------------------------------------------------------------- #
#                                TEST CASES                                  #
# -------------------------------------------------------------------------- # 
class TestMetrics(unittest.TestCase):


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
        self.assertEqual(kyc(good_acc, good_tx, good_fb)[0], 1) 
        


    def test_history_acc_longevity(self):
        '''
        - variable 'age' should be a non-negative of type: int or float
        - if there's no account, the score should be 0
        '''
        history_acc_longevity(good_acc, good_fb)

        self.assertGreaterEqual(history_acc_longevity.age, 0) 
        self.assertIsInstance(history_acc_longevity.age, (int, float))
        self.assertEqual(history_acc_longevity([], good_fb)[0], 0) 


    def test_liquidity_tot_balance_now(self):
        '''
        - empty account should result in 'no balance' error
        '''
        self.assertRegex(liquidity_tot_balance_now([], good_fb)[1]['liquidity']['error'], 'no balance')


    def test_liquidity_loan_duedate(self):
        '''
        - duedate should be at most 6 months
        '''
        self.assertLessEqual(liquidity_loan_duedate(good_tx, good_fb)['liquidity']['loan_duedate'], 6)


    def test_liquidity_avg_running_balance(self):
        '''
        - no tx yields a 'no tx' error
        '''
        self.assertRegex(liquidity_avg_running_balance(good_acc, [], good_fb)[1]['liquidity']['error'], 'no transaction history')


    def test_activity_tot_volume_tot_count(self):
        '''
        - tot_volume should be of type int or float
        - tot_volume should be non-negative
        - credit and debit checks share the same dictionary key
        - no tx returns 'no tx history' error
        '''
        fb = create_feedback_coinbase()
        cred, cred_fb = activity_tot_volume_tot_count(good_tx, 'credit', fb)
        deb, deb_fb = activity_tot_volume_tot_count(good_tx, 'debit', fb)

        for a in [cred, deb]:
            self.assertIsInstance(a, (float, int))
            self.assertGreaterEqual(a, 0)

        self.assertEqual(cred_fb['activity'].get('credit').keys(), deb_fb['activity'].get('debit').keys())
        self.assertRegex(activity_tot_volume_tot_count([], 'credit', good_fb)[1]['activity']['error'], 'no transaction history')


    def test_activity_consistency(self):
        '''
        - ensure you've accounted for all registered txns
        - ensure txn dates are of Type datetime (perform Type check on randomly chosen date)
        - no tx returns 'no tx history' error
        '''
        activity_consistency(good_tx, 'credit', good_fb)
        i = list(activity_consistency.frame.index)
        d = [x[0] for x in activity_consistency.typed_txn]

        self.assertCountEqual(i, d)
        self.assertIsInstance(np.random.choice(d), datetime)
        self.assertRegex(activity_consistency([], 'credit', good_fb)[1]['activity']['error'], 'no transaction history')


    def test_activity_profit_since_inception(self):
        pass

    def test_helper_fn(self):
        '''
        - Ensure the output of flow() comprises of both positive and negative volumes
        '''
        pass


# -------------------------------------------------------------------------- #
#                            PARAMETRIZATION                                 #
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

    def test_output(self):
        pass
 

if __name__ == '__main__':
    unittest.main()

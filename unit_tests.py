import unittest
from support.tests.test_coinbase import TestMetricsCoinbase
from support.tests.test_plaid import *
from support.metrics_coinbase import *


# Run the actual tests bunding classes of test cases into test suites
def suite():
    suite = unittest.TestSuite()

    # Plaid
    suite.addTest(unittest.makeSuite(TestMetricCredit))
    suite.addTest(unittest.makeSuite(TestMetricVelocity))
    suite.addTest(unittest.makeSuite(TestMetricStability))
    suite.addTest(unittest.makeSuite(TestMetricDiversity))
    suite.addTest(unittest.makeSuite(TestHelperFunctions))
    suite.addTest(unittest.makeSuite(TestParametrizePlaid))

    #Coinbase
    suite.addTest(unittest.makeSuite(TestMetricsCoinbase))
    suite.addTest(unittest.makeSuite(TestParametrizeCoinbase))

    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())




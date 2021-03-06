""" Testing for the the call.py module

The module can be executed on its own or incorporated into a larger test suite.

"""
import _path
import _unittest as unittest
from _data import TestData

from acis import WebServicesCall
from acis import RequestError


# Define the TestCase classes for this module. Each public component of the
# module being tested has its own TestCase.

class WebServicesCallTest(unittest.TestCase):
    """ Unit testing for the WebServicesCall class.

    """
    _class = WebServicesCall
    
    @classmethod
    def setUpClass(cls):
        cls._DATA = TestData("data/StnData.xml")
        return
        
    def setUp(self):
        """ Set up the test fixture.

        This is called before each test is run so that they are isolated from
        any side effects. This is part of the unittest API.

        """
        self._call = WebServicesCall("StnData")
        return

    def test_url(self):
        """ Test the url attribute.

        """
        self.assertEqual("http://data.rcc-acis.org/StnData", self._call.url)
        return

    def test_call(self):
        """ Test a normal call.

        """    
        self.assertDictEqual(self._DATA.result, self._call(self._DATA.params))
        return

    def test_error(self):
        """ Test an invalid call.

        """
        with self.assertRaises(RequestError) as context:
            self._call({})  # empty parameters
        self.assertEqual("Need sId", str(context.exception))
        return


# Specify the test cases to run for this module. Private bases classes need
# to be explicitly excluded from automatic discovery.

_TEST_CASES = (WebServicesCallTest,)

def load_tests(loader, tests, pattern):
    """ Define a TestSuite for this module.

    This is part of the unittest API. The last two arguments are ignored. The
    _TEST_CASES global is used to determine which TestCase classes to load
    from this module.

    """
    suite = unittest.TestSuite()
    for test_case in _TEST_CASES:
        tests = loader.loadTestsFromTestCase(test_case)
        suite.addTests(tests)
    return suite


# Make the module executable.

if __name__ == "__main__":
    unittest.main()  # main() calls sys.exit()

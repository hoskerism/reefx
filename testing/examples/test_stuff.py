###
### the standard unittest-derived test
###

import unittest

class ExampleTest(unittest.TestCase):
    def test_a(self):
        self.assert_(1 == 1)

###
### an unparented test -- no encapsulating class, just any fn starting with
### 'test'.
###
        
def test_b():
    """
    Raw, unparented test.
    """
    assert 'b' == 'b'

###
### non-unittest derived test -- class is instantiated, then functions
### starting with 'test' are executed.
###

class TestExampleTwo:
    def test_c(self):
        assert 'c' == 'c'

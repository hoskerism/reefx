###
### a simple function, with test fixtures.
###

_b_is_setup = False

def b_setup_func():
    global _b_is_setup
    
    assert not _b_is_setup
    _b_is_setup = True

def b_teardown_func():
    global _b_is_setup

    assert _b_is_setup
    _b_is_setup = False

def test_b():
    global _b_is_setup
    
    assert _b_is_setup
    
test_b.setup = b_setup_func
test_b.teardown = b_teardown_func

###
### a class test case, with test fixtures.
###

class TestExampleTwo:
    def __init__(self):
        self.is_setup = False
        
    def setUp(self):
        assert not self.is_setup
        self.is_setup = True

    def tearDown(self):
        assert self.is_setup
        self.is_setup = False
        
    def test_c(self):
        assert self.is_setup

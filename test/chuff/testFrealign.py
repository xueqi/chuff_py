import unittest
from chuff.frealign import Frealign

class testFrealign(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
    def tearDown(self):
        unittest.TestCase.tearDown(self)

    def test_helper_functions(self):
        pass

    def test_default_parameter(self):
        FREALIGN_EXEC = Frealign()
        FREALIGN_EXEC.set({
                      "ILAST" : 10234,
                      "PSIZE" : 1.08714,
                      "RO" : 300,

                      })
        print "\n".join(FREALIGN_EXEC.get_card_str_list())
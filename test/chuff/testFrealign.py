import unittest
from chuff.frealign import FrealignV8, FrealignReconstructMP

class testFrealign(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
    def tearDown(self):
        unittest.TestCase.tearDown(self)

    def test_helper_functions(self):
        pass

    def test_default_parameter(self):
        FREALIGN_EXEC = FrealignV8()
        FREALIGN_EXEC.set({
                      "ILAST" : 10234,
                      "PSIZE" : 1.08714,
                      "RO" : 300,

                      })
        self.assertEqual("\n".join(FREALIGN_EXEC.get_card_str_list()), '''I,0,F,F,F,F,0,F,F,F,F,0,F,F,1
300,0,1.08714,-1,0.07000,0.00000,1000,0.00000,30,50,10
1,1,1,1,1,
1,10234
H
-1,-1,1,1,0.00010
1,14,90,90,2.00000,200,0.00000,0.00000
-1,200,15,1000,0
FINPART1
FINPART2
FINPAR
FOUTPAR
FOUTSH
0,0,0,0,0,0,0,0
F3D
FWEIGH
MAP1
MAP2
FPHA
FPOI''')

    def test_frealign_reconstruct_single(self):
        pass

    def test_frealign_reconstruct_mp(self):

        params = {

                  }
        frmp = FrealignReconstructMP("input_ptcls", "input_params", "output_root", params)
        print "\n".join(frmp.get_card_str_list())
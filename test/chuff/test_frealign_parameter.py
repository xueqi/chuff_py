from chuff.frealign import FrealignParameter as FP

import unittest

class TestFrealignParameter(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)

    def testIntParamter(self):
        fp = FP(value = 10, param_type=int)
        self.assertEqual('10', str(fp))
        fp = FP(value = 1, param_type=int, name = "mode", frealign_name="IFORM", int_format = "%2d")
        self.assertEqual(" 1", str(fp))
        self.assertEqual("mode", fp.name)
        self.assertEqual("IFORM", fp.frealign_name)
        self.assertEqual("%2d", fp.int_format)
        #self.failUnlessRaises(ValueError, FP, {"value" : 1.1, "param_type":int, "name" :"mode"})

    def testFloatParameter(self):
        fp = FP(value=10., param_type=float)
        self.assertEqual('10.0000', str(fp))
        fp = FP(value=10, param_type=float)
        self.assertEqual('10.0000', str(fp))
        fp = FP(value=-10, param_type=float)
        self.assertEqual('-10.0000', str(fp))
        fp = FP(value=-1000, param_type=float)
        self.assertEqual('-1000.0000', str(fp))
        fp = FP(value=10, param_type=float, float_format = "%7.3f")
        self.assertEqual(' 10.000', str(fp))

    def testBooleanParameter(self):
        fp = FP(value=True, param_type=bool)
        self.assertEqual("T", str(fp))
        fp = FP(value=False, param_type=bool)
        self.assertEqual("F", str(fp))
        fp = FP(value=10, param_type=bool)
        self.assertEqual("T", str(fp))
        fp = FP(value=[], param_type=bool)
        self.assertEqual("F", str(fp))


    def testListparameter(self):
        fp = FP(value = [1, 2, 3], param_type=list)
        self.assertEqual("1,2,3", str(fp))
        f1 = FP(value=1, param_type=int)
        f2 = FP(value=2, param_type=float, float_format="%.4f")
        f3 = FP(value=3, param_type=bool)
        fp = FP(value=[f1,f2,f3], param_type=list)
        self.assertEqual("1,2.0000,T", str(fp))
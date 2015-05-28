from chuff.frealign import FrealignCard

import unittest

class TestFrealignCard(unittest.TestCase):

    def testSimpleCard(self):
        fc = FrealignCard("testcard")
        fc.add_param(value = 'I', name = "file_format", frealign_name="CFORM", param_type=str)
        self.assertEqual("I", str(fc))
        self.assertEqual("testcard", fc.name)
        fc.add_param(value = "1", name = "mode", frealign_name = "IFLAG", param_type = int)
        self.assertEqual("I,1", str(fc))
        self.assertEqual("testcard", fc.name)
        fc.add_param(value = False, name = "refine_magnification", frealign_name = "FMAG", param_type = bool)
        self.assertEqual("I,1,F", str(fc))
        self.assertEqual("testcard", fc.name)
        fc.remove_param("mode")
        self.assertEqual("I,F", str(fc))
        self.assertEqual("testcard", fc.name)
        fc.add_param(value = "1", name = "mode", frealign_name = "IFLAG", param_type = int, after = "file_format")
        self.assertEqual("I,1,F", str(fc))
        self.assertEqual("testcard", fc.name)
        fc.newline = True
        self.assertEqual("I,1,F\n", str(fc))


from chuff.frealign import Frealign9, FrealignCard, FrealignActin, FrealignActoMyosinVirginia


import unittest

class TestFrealign9(unittest.TestCase):

    def setUp(self):
        self.fr9 = Frealign9()
        unittest.TestCase.setUp(self)

    def test_add_card(self):

        fr9 = Frealign9()
        card = FrealignCard("card1")

        fr9.add_card(card)
        card = fr9.get_card("card1")
        self.assertIsNotNone(card)

    def test_insert_card(self):
        fr9 = self.fr9
        fr9.add_card(FrealignCard("card1"))
        fr9.add_card(FrealignCard("card3"))
        fr9.insert_card(FrealignCard('card2'), 'card1')
        card2 = fr9.get_card('card2')
        self.assertEqual(1, fr9.cards.index(card2))


    def test_set_parameter(self):
        fr9 = self.fr9
        fr9.initCards()
        fr9.set_parameter("molecule_weight", 1000)
        mw = fr9.get_param("MW")
        self.assertEqual(1000., mw)

    def test_insertCards(self):
        fr9 = self.fr9
        fr9.initCards()

        card1 = fr9.get_card("card1")
        self.assertIsNotNone(card1)
        self.assertEqual("I,0,F,F,F,F,0,F,F,F,F,0,F,0,0", str(card1))
        card2 = fr9.get_card("card2")
        self.assertIsNotNone(card2)
        self.assertEqual("0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000,0,0", str(card2))
        fr9.set_parameter("molecule_weight", 1000)
        card2 = fr9.get_card("card2")
        self.assertEqual("0.0000, 0.0000, 0.0000,1000.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000,0,0", str(card2))
        card3 = fr9.get_card("card3")
        self.assertEqual("1 1 1 1 1", str(card3))
        card4 = fr9.get_card("card4")
        self.assertEqual("1,1", str(card4))
        card5 = fr9.get_card("card5")
        self.assertEqual("C1", str(card5))
        card6 = fr9.get_card("card6")
        self.assertEqual("0.0000,0.0000,0.0000,0.0000,0.0000,0.0000, 0.0000, 0.0000", str(card6))

        card13 = fr9.get_card("card13")
        self.assertEqual("f3d", str(card13))

    def test_add_dataset(self):
        fr9 = self.fr9
        fr9.initCards()
        magnification, dstep, target, thresh, cs, akv, tx, ty, rrec, rmax1, rmax2, dfstd, rbfact, finpat1, finpat2, finpar, foutpar, foutsh, mgs = (
               1000, 14, 90, 89, 2.0, 200, 0,0,2.0, 200, 15, 1000, -1000, "input_ptcls", "output_proj", "input_parameters", "output_parameters", "outputshifts", None
                                                                                                                                                    )
        fr9.add_dataset(magnification, dstep, target, thresh, cs, akv, tx, ty, rrec, rmax1, rmax2, dfstd, rbfact, finpat1, finpat2, finpar, foutpar, foutsh, mgs)
        self.assertEqual(magnification, fr9.get_param('magnification'))

    def test_set_symmetry(self):
        fr9 = self.fr9
        fr9.initCards()
        alpha = 167.1
        rise = 28.1
        self.assertIsNone(fr9.get_card("card5a"))
        self.assertIsNone(fr9.get_card("card5b"))
        fr9.set_symmetry("H", alpha, rise)
        self.assertIsNotNone(fr9.get_card("card5b"))
        self.assertIsNone(fr9.get_card("card5a"))
        self.assertEqual(alpha, fr9.get_param("helical_turn"))
        self.assertEqual(rise, fr9.get_param("helical_rise"))

    def test_parallel_run_local(self):
        fr9 = self.fr9
        fr9.initCards()
        fr9.set_parameter("last_particle", 1000)
        fr9.set_parameter("mode", 0)
        #fr9.run_parallel_local(4)

class TestFrealignActin(unittest.TestCase):
    def setUp(self):
        self.fr = FrealignActin()

    def testInit(self):
        self.fr.tag = "test"
        self.fr.setup_files()
        #print str(self.fr.frealign)

class TestFrealignActoMyosinVirginia(unittest.TestCase):
    def setUp(self):
        self.fr = FrealignActoMyosinVirginia()
    def testInit(self):
        self.fr.tag = "test"
        self.fr.setup_files()
        #self.fr.add_dataset("test_file_stack", "test_input_param", "test_output_param")
        #self.fr.run()

    def test_parallel_run_local(self):
        fr = self.fr
        magnification, dstep, target, thresh, cs, akv, tx, ty, rrec, rmax1, rmax2, dfstd, rbfact, finpat1, finpat2, finpar, foutpar, foutsh, mgs = (
               1000, 14, 90, 89, 2.0, 200, 0,0,2.0, 200, 15, 1000, -1000, "input_ptcls", "output_proj", "input_parameters", "output_parameters", "outputshifts", None
                                                                                                                                                    )
        fr.frealign.add_dataset(magnification, dstep, target, thresh, cs, akv, tx, ty, rrec, rmax1, rmax2, dfstd, rbfact, finpat1, finpat2, finpar, foutpar, foutsh, mgs)
        fr.set_parameter("mode", 0)
        fr.frealign.run_parallel_local(4)
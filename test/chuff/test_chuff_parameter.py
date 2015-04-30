import unittest
from chuff.chuff_parameter import ChuffParameter, parse_m_file_line, chuff_parameter_to_str

class TestChuffParameter(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    def testChuffParameterReadMFile(self):
        import os

        param_dir = os.path.dirname(__file__)
        param_dir = os.path.join(param_dir, 'test_data')
        param_file = os.path.join(param_dir, 'chuff_parameters.m')
        param = ChuffParameter.read_from_mfile(param_file)
        self.assertEqual(param.filament_outer_radius, 200, "filament out radius should be 200")
        self.assertEqual(param.wedge_offset, 8.5, "wedge offset is 8.5 in mfile")
        self.assertEqual(param.param_type('filament_outer_radius'), type(1), "type of filament outer radius should be int")
        self.assertEqual(param['wedge_offset'], 8.5, "wedge offset is 8.5 in mfile")
        self.assertRaises(KeyError, lambda:param['abc'])

    def testChuffParamerWriteMFile(self):
        import os

        param_dir = os.path.dirname(__file__)
        param_dir = os.path.join(param_dir, 'test_data')
        param_file = os.path.join(param_dir, 'chuff_parameters.m')
        param = ChuffParameter.read_from_mfile(param_file)

        self.assertEqual(chuff_parameter_to_str(param), "filament_outer_radius = 200\nhelical_repeat_distance = 81.7\ninvert_density = 1\nnum_repeat_residues = 1229\ntarget_magnification = 59562\nscanner_pixel_size = 16\nspherical_aberration_constant = 2.0\naccelerating_voltage = 200\namplitude_contrast_ratio = 0.07\nwedge_offset = 8.5")

    def test_parse_m_file_line(self):
        self.assertEqual(parse_m_file_line("key=value"), ("key", "value"))
        self.assertEqual(parse_m_file_line("key=value ; #ASDAA "), ("key", "value"))
        self.assertEqual(parse_m_file_line("key=1"), ("key", 1))
        self.assertEqual(parse_m_file_line("key=1."), ("key", 1.0))
        self.assertEqual(parse_m_file_line("key="), ("key", None))
        self.assertEqual(parse_m_file_line("key=1.e4"), ("key", 1.e4))
        self.assertEqual(parse_m_file_line("key=[1,2,3,4]"), ("key", [1,2,3,4]))
        #self.assertEqual(parse_m_file_line("key=[abc,d,e,f]"), ("key", ["abc","d","e","f"]))

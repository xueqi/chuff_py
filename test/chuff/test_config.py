from chuff.utils import config

import unittest
import os
class test1Config(unittest.TestCase):
    
    def test_config(self):
        config.SCRIPT_DIR = os.path.dirname(os.path.dirname(__file__))
        
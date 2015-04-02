import unittest

from chuff.server import get_server, Server

class testServer(unittest.TestCase):

    def setUp(self):
        pass
    def tearDown(self):

        unittest.TestCase.tearDown(self)

    def test_get_server(self):
        self.assertEqual(get_server().server_type, "localhost", "default should return localhost instead of return %s" % get_server())

    def test_load_from_config(self):
        '''
            test load config file according to server name.
        '''
        server = Server()
        server.load_from_config("test_server")
        self.assertEqual(server.name, "test_server", "load server config failure\nread server name is %s" % server.name)

        server = Server()
        server.load_from_config("test_no_exist_server")
        self.assertEqual(server.name, "localhost", "no exist server should have name localhost")
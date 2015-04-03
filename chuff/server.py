'''@package Server
    Server that handles multi process

    A server represent a machine that has certain configuration that will run
    program in different way than other. The server is mainly used in the
    manage running of script, read and write files.
'''

def get_server():
    '''
        get server to run at.

    default return local machine.
    if 'server_name' provided in config.py file, then server with server_name
    will be return if found in server_configs directory

    '''
    return Server()

class Server(object):
    '''
        server object handles the parallel jobs. if server_type is localhost,
         no parallel will be used.
        @param server_type default 'localhost'. If use ssh, server_type should be 'remote'
    '''
    def __init__(self, name = 'localhost', server_type = 'localhost'):
        self.name = name
        if self.name is not None:
            self.load_from_config(self.name)
        self.server_type = server_type

    def load_from_config(self, server_name):
        '''
            load config from file name. config file is a python script that contains global variable for
            @param server_name The name of the server.
            @return Server instance. if no server config with name server_name, load Nothing
        '''
        try:
            svr = __import__('chuff.includes.server_configs._global_', globals(), locals(), ['_global_'], -1)
            for key, value in svr.__dict__.items():
                self.__dict__[key] = value
            svr = __import__('chuff.includes.server_configs.%s' % server_name, globals(), locals(), [server_name], -1)
            for key, value in svr.__dict__.items():
                if not key.startswith("__"): # exclude built-in values
                    self.__dict__[key] = value
        except ImportError:
            pass
    def get_default(self, var_name, default_value = None):
        if var_name not in self.__dict__: return default_value
        return getattr(self, var_name)

    def get_options(self):
        options = {}
        for key, value in self.__dict__.items():
            if key.startswith("__"): continue
            options[key] = value
        return options

    def check_status(self, pid):
        '''
            check if the process with pid is running
            @param pid The process id that is checked.
                If on a cluster, the pid should be the job id returned by qsub
        '''
        if self.server_type == "localhost":
            try:
                import os
                os.kill(pid, 0)
            except OSError:
                return False
            else:
                return True
        elif self.server_type == "pbs":
            return False
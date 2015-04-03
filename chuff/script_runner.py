'''
    ScriptRunner is a class to run a script on a server.
    To run a script, create an instance of ScriptRunner initialized with server
    instance. if no server instance provided, script will run on local server
'''
class ScriptRunner(object):
    def __init__(self, server =  None):
        self.server = server

    def run_script(self, script, workdir = ".", daemon = False):
        '''
            run a script. Use a subprocess module to run the script
            @param script A script instance that the runner will run
            @param daemon If the script would run in background.
            @param workdir The workdir for the script to run.
        '''
        import os
        os.chdir(workdir)
        if daemon:
            pass

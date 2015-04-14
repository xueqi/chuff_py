'''
    ScriptRunner is a class to run a script on a server.
    To run a script, create an instance of ScriptRunner initialized with server
    instance. if no server instance provided, script will run on local server
'''
import logging
logging.basicConfig()
class ScriptRunner(object):
    def __init__(self, server =  None):
        self.server = server


class TcshScriptRunner(ScriptRunner):
    '''
        The runner object for run a tcsh script.
    '''
    def __init__(self, server = None):
        ScriptRunner.__init__(self, server)

    def run(self, script, workdir = ".", background = False, stdout = None, stderr = None):
        '''
            Run a script file with tcsh shell

            :param str script: the script file to run. Must exists
            :param str workdir: the  workdir
            :param bool background: If run in background or foreground
            :param file stdout: file like object for output result. Must be writtable
            :param file stderr: same as stdout, but for error output

            :return: if background is True, return the process object, else return the return code
        '''
        import subprocess

        p = subprocess.Popen(["/bin/csh", script], stdout = stdout,
                             stderr = stderr)
        if background:
            return p
        else:
            return p.wait()

class PBSScriptRunner(ScriptRunner):
    '''
        The PBS script runner. Run a qsub script to submit job.

        First implementation is basically works as single function to submit a
        single tcsh script, which is used in chuff_main
    '''
    def __init__(self, server = None):
        ScriptRunner.__init__(self, server)

    def run(self, script, workdir = ".", background = True, stdout = None, stderr = None,
            nodes = 1, ppn = 1, queue = None, job_name = None):
        '''
            submit a script using qsub
        '''
        if queue is None:
            if self.server: queue = self.server.get_default('queue_name', None)
        submit_script = "qsub -l nodes=%d:ppn=%d" % (nodes, ppn)
        if queue is not None:
            submit_script += " -q %s" % queue
        if job_name is not None:
            submit_script += " -N %s" % job_name

        submit_script += " %s" % script
        import subprocess
        p = subprocess.Popen(submit_script.split(), stdout = subprocess.PIPE,
                             stderr = subprocess.PIPE)
        rtn_code = p.wait()
        out = p.stdout.read()
        err = p.stderr.read()
        if rtn_code == 0:
            job_id = self.get_job_id(out)
        else:
            logging.error("Submit Error: %s" % err)
            job_id = -1
        return job_id

    def get_job_id(self, out):
        '''
            get job id from output from the qsub command
            :param str out: the qsub command output. eg. 778355.rocks.louise.hpc.yale.internal
        '''
        import re

        mt = re.findall("$\d+", out)
        if not mt:
            logging.error("Can not retrieve the job id from: %s" % out)
            return -1
        return int(mt[0])



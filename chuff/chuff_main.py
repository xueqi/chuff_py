'''
    Chuff Main script. Can be used as commands to submit jobs for chuff scripts, and also has Chuff class which can be called from other scripts
'''
import os
import shutil
from utils.config import *
from project import Project
from server import Server, get_server

class Chuff(object):
    '''
        Chuff class
        1. handles everything same as chuff command in chuff3/commands, which should be compatible with csh scripts.
        2. call functions that take optional parameter MPI=True to run on multiple CPUs

    '''
    def __init__(self, server = None, project = None, options = None):
        '''
            @param server The server where the script to run. Default None, to run on local machine.
            @param project The chuff project that the chuff command will run in. Default get current directory as project directory.
            @param options additional options that will pass to all the functions chuff will call
        '''
        self.server = get_server()
        self.project = project
        if self.project is None:
            self.project = Project.open()
        # options comes first from the server config, then project config, then options parameters.
        self.options = self.server.get_options()
        if self.project:
            self.options.update(self.project.get_options())
        if options is not None:
            self.options.update(options)
        self.script_dir = []
        if 'CHUFF_COMMAND_DIR' in globals():
            self.script_dir.append(globals()['CHUFF_COMMAND_DIR'])

    def get_script_type(self, script_name):
        '''
            get script type, csh or python or octave?
            TODO: more precise detection
        '''
        f = open(script_name)
        first_line = f.readline()
        if "python" in first_line:
            return "python"
        if "csh" in first_line:
            return 'csh'
        if 'bash' in first_line:
            return 'bash'
        if 'function' in first_line:
            return 'octave'
        return "unknown"

    def run(self, *script_args, **kwargs):
        '''
            run jobs as in chuff3/command/chuff.
            must run in project directory with chuff_parameters.m.
        '''

        if len(script_args) > 0:
            job_script = script_args[0]
        else:
            self.print_avaiable_commands()
        chuff_extra_args = ""
        for key, value in kwargs.items():
            chuff_extra_args += " %s=%s" % (key, value)
        from copy import deepcopy
        options = {}
        for key, value in self.options.items():
            options[key] = value
        if kwargs is not None:
            options.update(kwargs)

        job_type = options.get('job_type', 'by_filaments')
        qsub = options.get('qsub', 0)
        nodes = options.get('nodes', 1)
        if qsub == 0:
            nodes = 1
        max_cpus = options.get('max_cpu', 1)
        cores = options.get('cores', 1)
        parjob_nuke = options.get('parjob_nuke', 0)
        queue_name = options.get('queue_name', self.server.get_default('queue_name', None))
        background = options.get('background', 0)
        test = options.get('test', 0)
        q_debug = options.get('q_debug', 0) # if debug qsub?
        filesync_pause = options.get('filesync_pause', 120) # file sync for parallel jobs. Used with nodes > 1

        parameter_file = "chuff_parameters.m"

        if job_type in ["by_filaments", "by_micrograph"] and len(script_args) > 1:
            raise Exception("ERROR: please do not give a name list for 'job_type=by_filaments' or 'job_type=by_micrograph'\n%s" % ", ".join(script_args[1:]))

        chuff_params_copy = "%s_saved.%s" % os.path.splitext(parameter_file)

        # copy the current parameter file before this run,
        if not os.path.exists(chuff_params_copy) and os.path.exists(self.project.param_file()):
            shutil.copy(parameter_file, chuff_params_copy)

        new_num_nodes_cores = self._get_new_num_nodes_cores(nodes, cores, max_cpus)
        if new_num_nodes_cores[0] != nodes or new_num_nodes_cores[1] != cores:
            print 'Max number of CPUs exceeded; clipping to', new_num_nodes_cores[0],'nodes,', new_num_nodes_cores[1], 'cores.'
            print '(use max_cpus=n to override; you can do this in chuff_machine_parameters.m)'
            nodes, cores = new_num_nodes_cores

        if not os.path.exists('parallel_jobs'):
            os.mkdir('parallel_jobs')

        # parallel_task is the next unused task register
        parallel_task = 1
        task_dir = "parallel_jobs/parallel_%d" % parallel_task

        while os.path.exists(task_dir):
            parallel_task += 1
            task_dir = "parallel_jobs/parallel_%d" % parallel_task


        # used to reuse the parallel_task register. Not too useful, since we can always use new one
        if parjob_nuke == 1 and parallel_task > 1:
            parallel_task -= 1
            task_dir = "parallel_jobs/parallel_%d" % parallel_task
            if not os.path.exists("%s/status_files" % task_dir):
                os.mkdir("%s/status_files" % task_dir)
            status_files = []
            for status_file in os.listdir("%s/status_files" % task_dir):
                status_files.append(status_file)

            if len(status_files) > 0:
                raise Exception('ERROR: job was started already.  You must manually delete it.')
            print "Nuking task : %s" % task_dir

            os.system('rm -r %s' % task_dir)

        qsub_header = "%s/qsub" % task_dir
        list_header = "%s/list_files/qsub_list" % task_dir

        ##############
        # Make execution lists
        ##############
        dirs = {
                "status" : "status_files",
                "list" : "list_files",
                "proc" : "proc_log_files",
                }
        if not os.path.exists(task_dir):
            os.mkdir(task_dir)
        for name, d in dirs.items():
            if not os.path.exists(os.path.join(task_dir, d)):
                os.mkdir(os.path.join(task_dir, d))

        if job_type == "one_job":
            one_job = 1
        else:
            one_job = 0

        if job_type == "by_arg":
            if len(script_args) > 1:
                #TODO:
                pass
            else:
                one_job = 1
        elif job_type == "by_filament":
            pwd = os.getcwd()
            os.chdir("scans")
            #TODO:
            os.chdir(pwd)
        elif job_type == "by_micrograph":
            pwd = os.getcwd()
            os.chdir("scans")
            #TODO:
            os.chdir(pwd)
        elif job_type != "one_job":
            raise Exception("ERROR: unrecognized job type '%s'..." % job_type)

        os.chdir(self.project.workdir)

        qsub_cores = cores
        min_cores = options.get('min_cores', 1)
        if qsub_cores < min_cores and qsub != 0:
            qsub_cores = min_cores

        if one_job == 1:
            qsub_arg = "-lnodes=%d:ppn=%d" % (nodes, cores)
            qsub_nodes = 1
            open('%s/%s_1_1.txt' % (self.project.workdir, list_header), 'w')
        else:
            qsub_qrg = "-lnodes=1:ppn=%d" % qsub_cores
            qsub_nodes = nodes

            for list_file in os.listdir("%s_*.txt"):
                pass
                #TODO:
        #print "Task : %s/%s %s" % (task_dir, job_script, chuff_extra_args)

        if len(script_args) > 1:
            num_targets = len(script_args) - 1
            print "Number of parallel targets: %d" % num_targets
        else:
            print "No parallel targets; processing in single-job mode."

        #=======================================================================
        # Make job scripts
        #=======================================================================

        if not os.path.exists("%s/q_log_files" % task_dir):
            os.mkdir("%s/q_log_files" % task_dir)
        if not os.path.exists("%s/proc_log_files" % task_dir):
            os.mkdir("%s/proc_log_files")
        job_script_path = self.project.get_script_path(job_script)
        if job_script_path is None:
            raise Exception("Error: cannot find the script: %s" % os.path.basename(job_script))

        shutil.copy(job_script_path, os.path.join(task_dir, os.path.basename(job_script_path)))

        qnode = 1
        while qnode <= qsub_nodes:
            qscript = "%s_%d.csh" % (qsub_header, qnode)
            script_params = {
                "orig_dir" : self.project.workdir,
                "task_dir" : task_dir,
                "qscript"   : os.path.basename(os.path.splitext(qscript)[-1]),
                "qsub" : qsub,
                "background" : background,
                "qsub_cores" : qsub_cores,
                "list_header" : list_header,
                "qnode" : qnode,
                "job_script" : job_script_path,
                "chuff_extra_args" : chuff_extra_args,
            }
            script_tpl = '''#!/bin/csh
cd ${orig_dir}
if(-e ${task_dir}/status_files/${qscript}_finished) /bin/rm ${task_dir}/status_files/${qscript}_run

set output_interactive = 0
if($qsub == 1) set output_interactive = 1
if($qsub == 0 && $background == 0) set output_interactive = 1

@ qcore = 1

while($$qcore <= $qsub_cores)
    set q_status_file = ${task_dir}/status_files/qsub_${qnode}_$${qcore}_status

    if(-e ${list_header}_${qnode}_$${qcore}.txt) then
        set file_list = (\`cat ${list_header}_${qnode}_$${qcore}.txt\`)
    else
    if($$?file_list) unset file_list
    endif

    if($$output_interactive == 1 && $qnode == 1 && $$qcore == 1) then
    set run_in_background = 0
    else
    set run_in_background = 1
    endif

    if($$?file_list) then
        if($$run_in_background == 1) then
      ($job_script $$file_list $chuff_extra_args >>& \
       $task_dir/proc_log_files/qsub_${qnode}_$${qcore}.log; echo $$status > $$q_status_file) &
    endif
    else
    echo "Note: no work for core number $$qcore; skipping..."
    echo 0 > $$q_status_file
    endif
    @ qcore = $$qcore + 1
end

if($$output_interactive == 1 && ${qnode} == 1) then
  echo '#####################################'
  echo 'Output for node, core 1:'
  echo '#####################################'

  set file_list = (\`cat ${list_header}_1_1.txt\`)
  set q_status_file = ${task_dir}/status_files/qsub_1_1_status

  $job_script $$file_list $chuff_extra_args |& \
       tee $task_dir/proc_log_files/qsub_1_1.log;

  echo $$status > $$q_status_file
endif

wait

'''
            from string import Template
            open(qscript,'w').write(Template(script_tpl).substitute(script_params))
            #=== ====================================================================
            # Execute jobs
            #=======================================================================
            if test == 0:
                if qsub == 0:
                    if background == 0:
                        pass
                        #===========================================================
                        # (source $qscript)
                        #===========================================================
                    else:
                        pass
                            #===========================================================
                            # (source $qscript >& /dev/null &)
                            #===========================================================
                else:
                    print "Submitting: %s" % qscript
                    submit_script = '''/usr/bin/qsub %s -q %s -d %s \
-e %s/q_log_files -o %s/q_log_files \
-N %s:%d \
%s''' % (qsub_arg, queue_name, self.project.workdir, task_dir, task_dir, os.path.basename(task_dir), qnode, qscript)
                    if q_debug == 1:
                        print submit_script
                        os.system(submit_script)
            else:
                if qsub == 0:
                    print "source %s" % qscript
                else:
                    print submit_script

            qnode = qnode + 1
        #=======================================================================
        # END while qnode <= qsub_nodes:
        #=======================================================================

#===============================================================================
#         #   Check if queued jobs are done
#         #   Note that this method will fail to complete if the queued jobs
#         #   are deleted; in this case the status files will never be
#         #   created!
#===============================================================================

        #=======================================================================
        # Basic idea to check if job done is to check the status_file generated by the submit_script.
        # the return status will be written to the status_file called qsub_<node>_<core>_status.
        # So if the file exists, this would think the job is done. So carefully to check when the file should generate
        #=======================================================================
        print qsub, test, background
        if qsub != 0 and test == 0 and background == 0:
            print "Wating for job to finish"
            print "Status files: %s/status_files/qsub_<node>_<core>_status" % task_dir
            print "Number of  nodes: %d" % nodes
            print "Number of cores: %d" % qsub_cores

            q_done = 0
            print qsub_cores, qsub_nodes
            while q_done == 0:
                q_done = 1
                qnode = 1
                while qnode <= qsub_nodes:
                    qcore = 1
                    while qcore <= qsub_cores:
                        q_status_file = "%s/status_files/qsub_%d_%d_status" % (task_dir, qnode, qcore)
                        if not os.path.exists(q_status_file):
                            q_done = 0
                        qcore += 1
                    qnode += 1
                if not q_done:
                    from time import sleep
                    sleep(1)
            return_status = 0
            qnode = 1
            while qnode <= qsub_nodes:
                qcore = 1
                while qcore <= qsub_cores:
                    q_status_file = "%s/status_files/qsub_%d_%d_status" % (task_dir, qnode, qcore)
                    if os.path.exists(q_status_file):
                        current_return_status = int(open(q_status_file).read())
                    else:
                        current_return_status = 3
                    if current_return_status != 0:
                        print "Error detected: %s/proc_log_files/qsub_%d_%d.log" % (task_dir, qnode, qcore)
                        return_status = current_return_status
                    qcore += 1
                qnode += 1

            if return_status == 0:
                print "Job parallel%d executed cleanly; no errors detected" % parallel_task
                if qsub != 0 and filesync_pause != 0:
                    print "Sleeping for %s seconds so files can sync" % filesync_pause
                    print "(disable this behavior with filesync_pause=0 option)"
                    sleep(filesync_pause)
            else:
                print "ERROR: one or more jobs in parallel%d exited with n error" % parallel_task
            from datetime import datetime
            print datetime.now()
            return return_status
        if background != 0 and test == 0:
            print "job submitted in the background..."

    def _get_new_num_nodes_cores(self, nodes, cores, max_cpus):
        if nodes * cores > max_cpus:
            new_nodes = nodes // cores
            if new_nodes <= 0:
                new_nodes = 1
                new_cores = max_cpus
            else:
                new_cores = cores
            return new_nodes, new_cores
        else:
            return new_nodes, new_cores

    def print_available_commands(self):
        '''
            print available commands from script dir
        '''
        for script_dir in self.script_dirs():
            fnames = os.listdir(script_dir)
            for fname in fnames:
                if os.path.isfile(fname):
                    print fname
def main():
    '''
        main program to run chuff in command line
    '''

    import argparse
    parser = argparse.ArgumentParser('Tool for running "embarrassily parallel" jobs')
    parser.add_argument("job_script")
    parser.add_argument("input_files", nargs = "*")
    parser.add_argument("--cores", type=int, default=16, help="Number of cores for each node")
    parser.add_argument("--nodes", type=int, default=1, help="Number of nodes for MPI")
    parser.add_argument("--parjob_nuke", type=int, default=0, help="") #TODO: what is this?
    parser.add_argument("--queue_name", default="sindelar", help="The PBS queue the program will run")
    parser.add_argument("--max_cpus", type=int, default=1, help="max cpus used. default to 1")
    parser.add_argument("--min_cores", type=int, default=1, help="") #TODO: waht is min_cores?
    parser.add_argument("--qsub", type=int, default=0, help="If use qsub, put 1, else 0") #TODO: default is 0 or 1?
    parser.add_argument("--test", type=int, default=0, help="Test the program, not run")
    parser.add_argument("--group_mts", type=int, default=0, help="") #TODO: what does group_mts mean?
    parser.add_argument("--filesync_pause", type=int, default=120, help="how many seconds to wait for file sync?")
    parser.add_argument("--job_type", default="by_arg", help="how to distribute job? by_arg, by_filament, by_micrograph")
    parser.add_argument("--q_debug", type=int, default=0, help="") #TODO: waht is q_debug?
    parser.add_argument("--background", type=int, default=0, help="") #TODO: what is background?

    options = parser.parse_args()
    args = []
    kwargs = {}
    # adapts chuff's command line style
    args.append(options.job_script)
    for ag in options.input_files:
        args.append(ag)
    for key, value in vars(options).items():
        if key != "job_script" and key != "input_files":
            kwargs[key] = value
    Chuff().run(*args, **kwargs)



if __name__ == "__main__":
    Project.create()
    main()

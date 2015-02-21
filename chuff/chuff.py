'''
    Chuff Main script
'''

from utils.config import *
from project import Project

class Chuff(object):
    '''
        Chuff class, handles everything same as chuff command in chuff3/commands
    '''
    def __init__(self):
        pass
    
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
    
    @classmethod
    def run(cls, options):
        '''
            run jobs as in chuff3/command/chuff
        '''
        print options
        # check if we are in project
        project = Project.open()
        # check script type. currently should support chuff3's original script and new corresponding python script
        ch = Chuff()
        job_script = options.job_script
        
        
        if options.job_type in ["by_filaments", "by_micrograph"] and len(options.file_list) > 0:
            raise Exception("ERROR: please do not give a name list for 'job_type=by_filament' or 'job_type=by_micrograph'")
        import os
        chuff_params_copy = "%s_saved.%s" % os.path.splitext(project.param_file())
        print chuff_params_copy
        
def main():
    '''
        main program to run chuff in command line
    '''
    
    import argparse
    parser = argparse.ArgumentParser('Tool for running "embarrassily parallel" jobs')
    parser.add_argument("job_script")
    parser.add_argument("--cores", type=int, default=16, help="Number of cores for each node")
    parser.add_argument("--nodes", type=int, default=1, help="Number of nodes for MPI")
    parser.add_argument("--parjob_nuke", type=int, default=0, help="") #TODO: what is this?
    parser.add_argument("--queue_name", default="sindelar", help="The PBS queue the program will run")
    parser.add_argument("--max_cpus", type=int, default=0, help="") #TODO: default
    parser.add_argument("--min_cores", type=int, default=1, help="") #TODO: waht is min_cores?
    parser.add_argument("--qsub", type=int, default=0, help="If use qsub, put 1, else 0") #TODO: default is 0 or 1?
    parser.add_argument("--test", type=int, default=0, help="Test the program, not run")
    parser.add_argument("--group_mts", type=int, default=0, help="") #TODO: what does group_mts mean?
    parser.add_argument("--filesync_pause", type=int, default=120, help="how many seconds to wait for file sync?")
    parser.add_argument("--job_type", default="by_arg", help="how to distribute job? by_arg, by_filament, by_micrograph")
    parser.add_argument("--q_debug", type=int, default=0, help="") #TODO: waht is q_debug?
    parser.add_argument("--background", type=int, default=0, help="") #TODO: what is background?

    options = parser.parse_args()
    
    Chuff.run(options)



if __name__ == "__main__":
    main()
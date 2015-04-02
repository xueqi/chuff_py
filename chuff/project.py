import shutil
from utils.config import *
from utils.util import *
from collections import OrderedDict

class Project(object):

    def __init__(self):
        '''
            default construct. Not used directory. Use Project.create instead
        '''
        self.name = None
        self.workdir = None
        self.script_dirs = ["scripts",
                             os.path.join(CHUFF_PROGRAM_DIR, "commands"),
                             os.path.join(PROGRAM_DIR, "scripts"),
                             ]

    def read_chuff_parameters(self, parameter_file = None):
        '''
            read parameters from parameter_file, or from default parameter file
        '''

        if parameter_file is None:
            parameter_file = self.param_file()

        pfile = open(project.file_path(parameter_file))

        d = OrderedDict()
        for line in pfile:
            line = line.strip()

            if line.startswith('#'): continue

            p_idx = line.find("#")
            if p_idx > 0:
                line = line[:p_idx]

            if not line.strip(): continue # empty line
            line = line.strip().strip(";")
            line = line.split("=")
            if len(line) > 1:
                key = line[0]
                value = "=".join(line[1:]).strip()
            else:
                raise Exception("Could not parse parameter file")

            d[key] = value

        return d

    def get_script_path(self, script_name):
        '''
            get script path from self.script_dirs
        '''
        for script_dir in self.script_dirs:
            print os.path.join(script_dir, script_name)
            if os.path.exists(os.path.join(script_dir, script_name)):
                return os.path.join(script_dir, script_name)
        return None

    @classmethod
    def create(cls, workspace = None, name = None):
        project = Project()
        if workspace is None: # create project in current directory
            workspace = os.path.abspath("..")
            name = os.path.basename(os.getcwd())
        project.name = name
        project.workdir = os.path.join(workspace, project.name)

        if not os.path.exists(project.workdir):
            try:
                os.mkdir(project.workdir)
            except:
                raise Exception('Can not create dir')

        param_file = os.path.join(PROGRAM_DIR, 'includes', CHUFF_PARAMETERS_FILE)
        if not os.path.exists(param_file):
            program_corrupted()

        shutil.copy(param_file, os.path.join(project.workdir, CHUFF_PARAMETERS_FILE))

        # prepare dirs
        project.mkdir("scans")

        print "Project has been create in directory %s" % project.workdir
        return project


    def mkdir(self, directory):
        ''' wrap of os.mkdir, but relative to project workdir
        '''
        if directory.startswith('/'):
            raise Exception("Won't mkdir startswith '/'")
        full_path = os.path.join(self.workdir, directory)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        return full_path

    def is_valid(self):
        if not os.path.exists(self.param_file()):
            return False
        return True

    def param_file(self):
        return os.path.join(self.workdir, CHUFF_PARAMETERS_FILE)

    def file_path(self, filename, filetype=None):
        '''
            get file path for file name in current project
            @param filename The full path of which to get
            @param filetype The file type for the filename.
            TODO: options for filetype are:
        '''
        return os.path.join(self.workdir, filename)

    @classmethod
    def open(cls, project_name = None, workspace = "."):
        '''
            Open project from workspace with project name.
            if project_name is None, open project at current directory. which mains the workspace should be ".."
        '''
        if project_name is None: # default set current dir as project
            project_name = os.path.split(os.getcwd())[-1]
            workspace = os.path.split(os.getcwd())[0]
        project = Project()
        workdir = os.path.join(workspace, project_name)
        if not workdir:
            return None
        if not os.path.exists(os.path.join(workdir, CHUFF_PARAMETERS_FILE)):
            raise Exception("not a chuff project")
        project.name = project_name
        project.workdir = workdir
        return project

    def get_options(self):
        '''
            get options config for server
        '''
        options= {}
        for key, value in self.__dict__.items():
            options[key] = value
        return options

def first_run(workspace):
    '''
    workspace does not exists, first time run in the workspace
    '''
    if os.path.exists(workspace):
        ans = raw_input("%s already exists. overwrite?" % workspace)
        if ans.lower().startswith("y"):
            os.removedirs(workspace)

        return
    if not os.path.exists(workspace):
        ans = raw_input("Will create new dir at %s. Ok?Y/(N)")
        if ans.lower().startswith('y'):
            os.makedirs(workspace)


if __name__ == "__main__":
    import tempfile

    project = Project.create(workspace = tempfile.mkdtemp(), name = "testProject")
    d = project.read_chuff_parameters()

    for key, value in d.items():
        print key, value
from chuff.chuff_main import Chuff

import unittest
@unittest.skip
class testChuff(unittest.TestCase):
    def setUp(self):
        '''
            Create valid project, copy data
        '''
        import tempfile
        self.workdir = tempfile.mkdtemp()

    def tearDown(self):
        import os
        os.system('rm -rf %s' % self.workdir)
        unittest.TestCase.tearDown(self)


    def testChuffProgram(self):
        from chuff.project import Project
        project = Project.create(name = "testChuffProgram", workspace = self.workdir)
        import os
        os.chdir(project.workdir)
        import chuff.chuff_main
        program_file = chuff.chuff_main.__file__
        if program_file.endswith(".pyc"):
            program_file = program_file[:-1]
        import subprocess
        p = subprocess.Popen(['python', program_file], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        stdout = p.stdout.read()
        stderr = p.stderr.read()
        self.assertTrue("error: too few arguments" in stderr)
        p = subprocess.Popen(['python', program_file, 'test_script.py'], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        stdout = p.stdout.read()
        stderr = p.stderr.read()
        print stderr
        self.assertFalse("error: too few arguments" in stderr)
        p = subprocess.Popen(['python', program_file, 'test_script.py'], stdout = subprocess.PIPE, stderr = subprocess.PIPE)

        stdout = p.stdout.read()
        stderr = p.stderr.read()
        print stderr

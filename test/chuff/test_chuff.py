from chuff.chuff import Chuff

import unittest

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
        import chuff.chuff
        program_file = chuff.chuff.__file__[:-1]
        print program_file
        import subprocess
        p = subprocess.Popen(['python', program_file], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        stdout = p.stdout.read()
        stderr = p.stderr.read()
        print stderr
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

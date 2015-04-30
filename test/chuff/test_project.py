'''
    project test
'''

import unittest
from chuff.project import Project
@unittest.skip
class ProjectTest(unittest.TestCase):

    def setUp(self):
        import tempfile
        self.workdir = tempfile.mkdtemp()
    def tearDown(self):
        import os
        #os.system('rm -rf %s' % self.workdir)
        unittest.TestCase.tearDown(self)

    def testCreateProjectWithName(self):
        import os
        project_name = "testCreateProjectWithName"
        project = Project.create(workspace = self.workdir, name = project_name)
        self.assertEqual(project_name, project.name)
        self.assertTrue(os.path.exists(os.path.join(self.workdir, project_name)))
        self.assertTrue(project.is_valid())
        # check directory exists
        self.assertTrue(os.path.isdir(os.path.join(project.workdir, 'scans')), "scans dir must exists")

    def testCreateProjectWithConflictName(self):

        project_name = "testCreateProjectWithConflictName"
        Project.create(workspace = self.workdir, name = project_name)
        self.assertRaises(Exception, Project,
                           workspace = self.workdir,
                           name = project_name)

    def testCreateProjectInReadOnlyFileSystem(self):

        self.assertRaises(Exception, Project, '/', 'whatevername')

    def testFilePath(self):
        project_name = "testFilePath"
        import os
        project = Project.create(workspace = self.workdir, name = project_name)
        self.assertEqual(os.path.join(self.workdir, project_name, "abc.te"),
                          project.file_path('abc.te'))

    def testOpenProject(self):
        project_name = "testOpenProject"
        Project.create(workspace = self.workdir, name = project_name)
        project = Project.open(project_name, workspace = self.workdir)
        self.assertEqual(project_name, project.name)

    def testValidProject(self):
        project_name = "testValidProject"
        project = Project.create(workspace = self.workdir, name = project_name)
        self.assertTrue(project.is_valid(), "project is not valid")
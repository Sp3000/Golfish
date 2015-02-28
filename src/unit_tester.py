import os
import subprocess
import unittest

COMMAND = "py -3 golfish.py"
TEST_FOLDER = "tests"

class TestBlockStructure(unittest.TestCase):
    def run_test(self, test_name):            
        with open("{}/{}.expected".format(TEST_FOLDER, test_name)) as exfile:
            expected = exfile.read()


        test_file = "{}/{}.input".format(TEST_FOLDER, test_name)
        process = subprocess.Popen(COMMAND.split() + [test_file],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        
        output = process.communicate()
        
        if output[0].decode() != expected:
            print("Actual:", output[0].decode())
            print("Expected:", expected)
            raise AssertionError()

        process.terminate()


def create_test(testname):
    def run_testname(self):
        self.run_test(testname)

    return run_testname


if __name__ == '__main__':
    input_ = set()
    expected = set()

    for filename in os.listdir(TEST_FOLDER):
        if filename.endswith(".input"):
            input_.add(filename[:-6])

        if filename.endswith(".expected"):
            expected.add(filename[:-9])

    tests = input_ & expected

    for testname in tests:
        setattr(TestBlockStructure, "test_{}".format(testname), create_test(testname))

    ignored = input_ ^ expected

    if ignored:
        print("Ignored:", *ignored)
        
    unittest.main()
        

        
        

import os


PROGRAM_DIR = os.path.dirname(os.path.dirname(__file__))

CHUFF_PROGRAM_DIR = os.environ.get('chuff_dir', "")

CHUFF_PARAMETERS_FILE = "chuff_parameters.m"

SCRIPT_DIR = os.path.join(PROGRAM_DIR, "scripts")

COMMAND_DIR = os.path.join(CHUFF_PROGRAM_DIR)

DEFAULT_QUEUE = "sindelar"
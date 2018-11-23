
# This file contains utils for testing rather than tests designed for utils.py

import directory
import os
import importlib

def reload_in_advanced_mode():
    execute_reload('true')

def reload_in_simple_mode():
    execute_reload('false')

def execute_reload(val):
    os.environ['ADVANCED'] = val
    importlib.reload(directory)


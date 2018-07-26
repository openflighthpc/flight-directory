import datetime
import os
import csv
import re

import utils
from config import CONFIG 

def write_log(args):
    
    time = datetime.datetime.now().replace(microsecond=0)
    
    env_vars = {}
    #env_vars['USER'] = os.getenv("SUDO_USER")
    for var in os.environ:
        if var.startswith("FC_"):
            env_vars[var]=os.getenv(var)

    cmd = utils.original_command()
    # regex for replacing any passwords in the logs with asterisks
    if re.search(r'--password', cmd):
        if re.search(r'(?<= --password( |=)).*(?= \-\-)', cmd):
            cmd = re.sub(r'(?<= --password( |=)).*(?= \-\-)', '********', cmd)
        elif re.search(r'(?<= --password( |=)).*(?=$)', cmd):
            cmd = re.sub(r'(?<= --password( |=)).*(?=$)', '********', cmd)

    #some errors seem to come packaged with pesky newlines, .strip() wasn't working for whatever reason
    for num in range(len(args)): 
        args[num] = re.sub(r'\n','',args[num])

    row = [cmd, str(time), str(env_vars)] + args

    with open(CONFIG.DIRECTORY_LOG, mode='a', newline='') as csvfile:
        logwriter = csv.writer(csvfile, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
        #A row must be an iterable of strings or numbers for Writer objects
        logwriter.writerow(row)

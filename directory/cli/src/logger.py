import datetime
import os
import csv
import re

import utils
from config import CONFIG 

def log_cmd(args):
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

    row = [cmd] + args
    write_to_log(row)

def write_to_log(row):
    time = str(datetime.datetime.now().replace(microsecond=0))

    env_vars = {}
    for var in os.environ:
        if var.startswith("FC_"):
            env_vars[var]=os.getenv(var)

    row = [time, env_vars] + row

    with open(CONFIG.DIRECTORY_LOG, mode='a', newline='') as csvfile:
        logwriter = csv.writer(csvfile, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
        logwriter.writerow(row)

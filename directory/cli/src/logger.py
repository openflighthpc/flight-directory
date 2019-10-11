#==============================================================================
# Copyright (C) 2019-present Alces Flight Ltd.
#
# This file is part of Flight Directory.
#
# This program and the accompanying materials are made available under
# the terms of the Eclipse Public License 2.0 which is available at
# <https://www.eclipse.org/legal/epl-2.0>, or alternative license
# terms made available by Alces Flight Ltd - please direct inquiries
# about licensing to licensing@alces-flight.com.
#
# Flight Directory is distributed in the hope that it will be useful, but
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESS OR
# IMPLIED INCLUDING, WITHOUT LIMITATION, ANY WARRANTIES OR CONDITIONS
# OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A
# PARTICULAR PURPOSE. See the Eclipse Public License 2.0 for more
# details.
#
# You should have received a copy of the Eclipse Public License 2.0
# along with Flight Directory. If not, see:
#
#  https://opensource.org/licenses/EPL-2.0
#
# For more information on Flight Directory, please visit:
# https://github.com/openflighthpc/flight-directory
#==============================================================================
import datetime
import os
import csv
import re

import utils
from config import CONFIG

def log_cmd(args, error=None):
    if not error==None:
        # some click exceptions (e.g. MissingParameter) don't have human readable standard
        #   output so this is neccessary to log them fully
        if hasattr(error, 'format_message'):
            error_str = error.format_message()
        else:
            error_str = str(error)
        if error.__class__.__name__:
            args[0] = args[0] + ": " + error.__class__.__name__
        if (error_str and not error_str=="None"):
            # some errors came packaged with newlines & strip wasn't working for some reason
            error_str = re.sub(r'\n','',error_str)
            # Error strings have many uneccessary quotes. All those that are valid are duplicated
            #   deleting non consecutive quotes
            error_str = re.sub(r'(?<!\")\"(?!\")','',error_str)
            #   replacing consecutive quotes with single quotes
            error_str = re.sub(r'""','"',error_str)
            args[0] = args[0] + ": " + error_str

    cmd = utils.original_command()
    # regex for replacing any passwords in the logs with asterisks
    if re.search(r'--password', cmd):
        if re.search(r'(?<= --password( |=)).*(?= \-\-)', cmd):
            cmd = re.sub(r'(?<= --password( |=)).*(?= \-\-)', '********', cmd)
        elif re.search(r'(?<= --password( |=)).*(?=$)', cmd):
            cmd = re.sub(r'(?<= --password( |=)).*(?=$)', '********', cmd)

    row = [cmd] + args
    write_to_log(row)

def log_simple_cmd(params):
    cmd = utils.original_command()
    row = [cmd]

    for key, value in params.items():
        string = '{0}: {1}'.format(key, value)
        row.append(string)

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

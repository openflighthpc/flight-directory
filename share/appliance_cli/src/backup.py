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

import tempfile
import os
import shutil


# Class to manage backing up a file or directory. Backup file/directory is
# created from a path when this object is created; it can then later be removed
# or the original file restored from it, or it will be removed when this object
# is garbage collected (which may never happen, but that's OK).
class Backup():

    def __init__(self, original_path):
        self.original_path = original_path

        self.backup_dir = tempfile.mkdtemp()
        self.backup_path = os.path.join(self.backup_dir, 'backup')

        _force_copy_any_path(self.original_path, self.backup_path)

    def restore(self):
        _force_copy_any_path(self.backup_path, self.original_path)
        self.remove()

    def remove(self):
        if os.path.exists(self.backup_dir):
            shutil.rmtree(self.backup_dir)

    def __del__(self):
        self.remove()


# Copy a file or directory from any path to any other path, deleting any
# existing file at that location first.
def _force_copy_any_path(from_path, to_path):
    if os.path.isdir(from_path):
        if os.path.exists(to_path):
            shutil.rmtree(to_path)
        shutil.copytree(from_path, to_path)
    else:
        shutil.copy2(from_path, to_path)

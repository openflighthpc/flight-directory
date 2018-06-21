
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

import unittest
import os
import stat
import tempfile
import shutil
import logging
from unittest.mock import patch, MagicMock
from argparse import Namespace
from src.main import command_line_arguments_wrapper, md5_digest  

class TestSyncScript(unittest.TestCase):

    def setUp(self):
        # Create temporary directories for source and destination
        self.source_dir = tempfile.mkdtemp()
        self.destination_dir = tempfile.mkdtemp()
        self.log_path = os.path.join(tempfile.gettempdir(), 'test_log.log')

        # Define sample file paths
        self.file1 = os.path.join(self.source_dir, "file1.txt")
        self.hidden_file = os.path.join(self.source_dir, ".hidden_file")

        # Write content to files
        with open(self.file1, 'w') as f:
            f.write("Sample content")

        with open(self.hidden_file, 'w') as f:
            f.write("Hidden content")

        # Prepare args object to pass to the script
        self.args = Namespace(
            source_dir_path=self.source_dir,
            destination_dir_path=self.destination_dir,
            log_path=self.log_path,
            sync_period=1,  # Ensure this is an integer
            filter_hidden_dirs_files=True  # Ensure this is a boolean
        )

    def tearDown(self):
        # Remove all handlers from the logger to close the log file
        logger = logging.getLogger("sync_logger")
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()
        # Remove source and destination directories from the desktop
        shutil.rmtree(self.source_dir, ignore_errors=True)
        shutil.rmtree(self.destination_dir, ignore_errors=True)
        # Remove log file if it exists
        if os.path.exists(self.log_path):
            os.chmod(self.log_path, stat.S_IWRITE)
            os.remove(self.log_path)


    def test_initial_sync(self):
        # Run initial synchronization
        sync_func = command_line_arguments_wrapper(self.args)
        sync_func(self.source_dir, self.destination_dir)

        # Check if file is copied to destination
        self.assertTrue(os.path.exists(os.path.join(self.destination_dir, "file1.txt")))

    def test_hidden_file_filtering(self):
        # Run synchronization with hidden file filtering
        sync_func = command_line_arguments_wrapper(self.args)
        sync_func(self.source_dir, self.destination_dir)

        # Verify that the hidden file is not copied to destination
        self.assertFalse(os.path.exists(os.path.join(self.destination_dir, ".hidden_file")))

    def test_file_update_sync(self):
        # Initial sync to copy all files
        sync_func = command_line_arguments_wrapper(self.args)
        sync_func(self.source_dir, self.destination_dir)

        # Modify file1 in the source directory
        with open(self.file1, 'w') as f:
            f.write("Updated content")

        # Sync again to update destination with modified file
        sync_func(self.source_dir, self.destination_dir)

        # Verify the content in the destination file matches the updated source file
        with open(os.path.join(self.destination_dir, "file1.txt"), 'r') as f:
            content = f.read()
        self.assertEqual(content, "Updated content")

    def test_file_removal_sync(self):
        # Initial sync to copy all files
        sync_func = command_line_arguments_wrapper(self.args)
        sync_func(self.source_dir, self.destination_dir)

        # Remove file1 from source and resync
        os.remove(self.file1)
        sync_func(self.source_dir, self.destination_dir)

        # Check that file1 is removed from destination
        self.assertFalse(os.path.exists(os.path.join(self.destination_dir, "file1.txt")))

    def test_subdirectory_sync(self):
        # Create a subdirectory with a file in the source directory
        sub_dir = os.path.join(self.source_dir, "subdir")
        os.makedirs(sub_dir)
        file_in_subdir = os.path.join(sub_dir, "file_in_subdir.txt")
        with open(file_in_subdir, 'w') as f:
            f.write("Subdirectory file content")

        # Run synchronization
        sync_func = command_line_arguments_wrapper(self.args)
        sync_func(self.source_dir, self.destination_dir)

        # Verify that the subdirectory and its file are copied to the destination
        self.assertTrue(os.path.exists(os.path.join(self.destination_dir, "subdir", "file_in_subdir.txt")))

    def test_md5_digest_function(self):
        # Test md5 digest function for data integrity check
        md5_source = md5_digest(self.file1)
        # Create a duplicate file and check the hashes match
        duplicate_file = os.path.join(self.destination_dir, "duplicate_file.txt")
        shutil.copy2(self.file1, duplicate_file)
        md5_duplicate = md5_digest(duplicate_file)
        self.assertEqual(md5_source, md5_duplicate)

if __name__ == '__main__':
    unittest.main()

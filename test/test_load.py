noimport unittest
import os
import tempfile
import logging
import stat
import shutil
import time
from unittest.mock import MagicMock
from src.main import command_line_arguments_wrapper 

class TestSyncLoad(unittest.TestCase):

    def setUp(self):
        # Create temporary directories for source and destination
        self.source_dir = tempfile.mkdtemp()
        self.destination_dir = tempfile.mkdtemp()
        self.log_path = os.path.join(tempfile.gettempdir(), 'load_test_log.log')

        # Define args for command line arguments wrapper
        self.args = MagicMock()
        self.args.source_dir_path = self.source_dir
        self.args.destination_dir_path = self.destination_dir
        self.args.log_path = self.log_path
        self.args.sync_period = 1  # sync every second
        self.args.filter_hidden_dirs_files = False  # Include all files in the load test

    def tearDown(self):
        # Remove all handlers from the logger to close the log file
        logger = logging.getLogger("sync_logger")
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        # Remove source and destination directories
        shutil.rmtree(self.source_dir, ignore_errors=True)
        shutil.rmtree(self.destination_dir, ignore_errors=True)
        # Remove log file if it exists
        if os.path.exists(self.log_path):
            os.chmod(self.log_path, stat.S_IWRITE)
            os.remove(self.log_path)

    def create_large_number_of_files(self, num_files=1000, file_size_kb=10):
        """Helper function to create a large number of files in source directory."""
        for i in range(num_files):
            file_path = os.path.join(self.source_dir, f"file_{i}.txt")
            # Write random data to file to make it the desired size
            with open(file_path, 'wb') as f:
                f.write(os.urandom(file_size_kb * 1024))  # Generate a file with `file_size_kb` KB of random data

    def test_large_file_sync(self):
        # Create a large number of files for the load test
        num_files = 1000  # Number of files to create in the source directory
        file_size_kb = 10  # Size of each file in KB
        self.create_large_number_of_files(num_files=num_files, file_size_kb=file_size_kb)

        # Start the synchronization process
        sync_func = command_line_arguments_wrapper(self.args)

        # Measure the time taken for initial sync
        start_time = time.time()
        sync_func(self.source_dir, self.destination_dir)
        end_time = time.time()

        # Calculate the elapsed time
        elapsed_time = end_time - start_time
        print(f"Time taken to sync {num_files} files of {file_size_kb}KB each: {elapsed_time:.2f} seconds")

        # Assert that all files are synchronized to the destination
        for i in range(num_files):
            self.assertTrue(os.path.exists(os.path.join(self.destination_dir, f"file_{i}.txt")))

        # Assert elapsed time is within reasonable limits (customize based on environment)
        # Expected threshold can vary depending on system and file size
        threshold_time = num_files * 0.01  # Assume it should not take more than this time
        self.assertLess(elapsed_time, threshold_time, "Synchronization took longer than expected.")

    def test_repeated_syncs_under_load(self):
        """Test the script under repeated synchronization operations."""
        self.create_large_number_of_files(num_files=500, file_size_kb=10)

        # Start the synchronization process
        sync_func = command_line_arguments_wrapper(self.args)
        sync_count = 5  # Number of repeated syncs to test

        total_time = 0
        for _ in range(sync_count):
            start_time = time.time()
            sync_func(self.source_dir, self.destination_dir)
            sync_time = time.time() - start_time
            total_time += sync_time
            print(f"Sync operation took {sync_time:.2f} seconds")

        average_sync_time = total_time / sync_count
        print(f"Average time per sync under load: {average_sync_time:.2f} seconds")

        # Ensure that all files still exist in destination after multiple syncs
        for i in range(500):
            self.assertTrue(os.path.exists(os.path.join(self.destination_dir, f"file_{i}.txt")))

        # Ensure average sync time is within reasonable limit (customize based on environment)
        threshold_sync_time = 1.0  # Average sync time in seconds, adjust based on expectations
        self.assertLess(average_sync_time, threshold_sync_time, "Average sync time exceeded threshold")

if __name__ == '__main__':
    unittest.main()

# # To see test results after load testing, run: pytest -v test_load.py
# 
# =========================================================================== test session starts ===========================================================
# platform win32 -- Python 3.12.6, pytest-8.3.3, pluggy-1.5.0 -- C:\Users\Назар\Desktop\Folder_Sync_Project\venv\Scripts\python.exe
# cachedir: .pytest_cache
# rootdir: C:\Users\Назар\Desktop\Folder_Sync_Project
# collected 2 items
# 
# test_load.py::TestSyncLoad::test_large_file_sync PASSED                                                                                               [ 50%]
# test_load.py::TestSyncLoad::test_repeated_syncs_under_load PASSED                                                                                     [100%]
# 
# =========================================================================== 2 passed in 4.95s ==============================================================
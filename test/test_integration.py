import os
import tempfile
import shutil
import pytest
import time
from unittest import mock
from pathlib import Path
from src.main import command_line_arguments_wrapper 


@pytest.fixture
def setup_directories():
    # Setup temporary source and destination directories
    with tempfile.TemporaryDirectory() as source_dir, tempfile.TemporaryDirectory() as destination_dir:
        # Yield the source and destination paths for use in tests
        yield source_dir, destination_dir

@pytest.fixture
def create_sample_files(setup_directories):
    source_dir, destination_dir = setup_directories
    
    # Create some files and directories in the source directory for testing
    (Path(source_dir) / "file1.txt").write_text("Hello, World!")
    (Path(source_dir) / "file2.txt").write_text("Another file")
    
    # Create a nested directory with a hidden file inside
    os.makedirs(Path(source_dir) / "subdir")
    (Path(source_dir) / "subdir" / "file3.txt").write_text("Nested file")
    (Path(source_dir) / ".hidden_file").write_text("This is hidden")
    
    # Return source and destination directories
    return source_dir, destination_dir

@pytest.fixture
def setup_logger(tmp_path):
    # Setup temporary log file path
    log_path = tmp_path / "test_log.log"
    return str(log_path)

@pytest.fixture
def args(create_sample_files, setup_logger):
    source_dir, destination_dir = create_sample_files
    log_path_ = setup_logger
    
    # Define arguments to pass to the wrapper
    class Args:
        source_dir_path = source_dir
        destination_dir_path = destination_dir
        log_path = log_path_
        sync_period = 1  # Set low period for fast test iteration
        filter_hidden_dirs_files = False

    return Args()

def test_initial_sync(args):
    # Run initial sync
    sync_function = command_line_arguments_wrapper(args)
    sync_function(args.source_dir_path, args.destination_dir_path)

    # Check if files are copied
    assert os.path.exists(os.path.join(args.destination_dir_path, "file1.txt"))
    assert os.path.exists(os.path.join(args.destination_dir_path, "file2.txt"))
    assert os.path.exists(os.path.join(args.destination_dir_path, "subdir", "file3.txt"))

def test_sync_with_hidden_files(args):
    args.filter_hidden_dirs_files = True  # Enable hidden file filtering

    # Run sync
    sync_function = command_line_arguments_wrapper(args)
    sync_function(args.source_dir_path, args.destination_dir_path)

    # Verify that hidden file is not copied
    assert not os.path.exists(os.path.join(args.destination_dir_path, ".hidden_file"))

def test_file_update_sync(args):
    sync_function = command_line_arguments_wrapper(args)
    sync_function(args.source_dir_path, args.destination_dir_path)

    # Update a file in the source
    (Path(args.source_dir_path) / "file1.txt").write_text("Updated content")

    # Re-run sync
    sync_function(args.source_dir_path, args.destination_dir_path)

    # Check that the destination file was updated
    with open(os.path.join(args.destination_dir_path, "file1.txt"), "r") as f:
        assert f.read() == "Updated content"

def test_file_removal_sync(args):
    sync_function = command_line_arguments_wrapper(args)
    sync_function(args.source_dir_path, args.destination_dir_path)

    # Remove a file from source
    os.remove(os.path.join(args.source_dir_path, "file2.txt"))

    # Run sync again
    sync_function(args.source_dir_path, args.destination_dir_path)

    # Ensure file was removed from destination
    assert not os.path.exists(os.path.join(args.destination_dir_path, "file2.txt"))

def test_subdirectory_sync(args):
    sync_function = command_line_arguments_wrapper(args)

    # Initial sync
    sync_function(args.source_dir_path, args.destination_dir_path)

    # Verify the subdirectory and its content are synced
    assert os.path.exists(os.path.join(args.destination_dir_path, "subdir"))
    assert os.path.exists(os.path.join(args.destination_dir_path, "subdir", "file3.txt"))

def test_logging(args):
    sync_function = command_line_arguments_wrapper(args)

    # Run sync and check log output
    sync_function(args.source_dir_path, args.destination_dir_path)

    with open(args.log_path, "r") as log_file:
        log_content = log_file.read()
        
    # Check for expected log entries
    assert "File copied" in log_content
    assert "Directory copied" in log_content or "Directory created" in log_content
    

    

# To see test results of code integration, run: pytest -v test_integration.py
# 
# ============================================= test session starts ===============================================================================================
# platform win32 -- Python 3.12.6, pytest-8.3.3, pluggy-1.5.0 -- C:\Users\Назар\Desktop\Folder_Sync_Project\venv\Scripts\python.exe
# cachedir: .pytest_cache
# rootdir: C:\Users\Назар\Desktop\Folder_Sync_Project
# collected 6 items

# test_integration.py::test_initial_sync PASSED                                                                                                              [ 16%]
# test_integration.py::test_sync_with_hidden_files PASSED                                                                                                    [ 33%]
# test_integration.py::test_file_update_sync PASSED                                                                                                          [ 50%]
# test_integration.py::test_file_removal_sync PASSED                                                                                                         [ 66%]
# test_integration.py::test_subdirectory_sync PASSED                                                                                                         [ 83%]
# test_integration.py::test_logging PASSED                                                                                                                   [100%]

# ============================================== 6 passed in 0.54s =================================================================================================
import os
import filecmp
import shutil
import time
import argparse
import logging
import signal
import hashlib
import stat


# ------------------------------------------------------------------------------------
# Wrapper around filecmp.dircmp to ignore hidden and system files/folders
class DirComparisonNoHidden(filecmp.dircmp):
    def __init__(self, a, b, ignore=None, hide=None, *, shallow=True):
        # Initialize the parent class with hidden files/folders ignored
        super().__init__(a, b, ignore=ignore, hide=hide)
        # Filter out all hidden files and directories across all subdirectories
        self.left_list = [item for item in self.left_list if not is_hidden(os.path.join(a, item))]
        self.right_list = [item for item in self.right_list if not is_hidden(os.path.join(b, item))]
        # Update common sets to exclude hidden items
        self.common = [item for item in self.common if not is_hidden(os.path.join(a, item))]
        self.common_dirs = [item for item in self.common_dirs if not is_hidden(os.path.join(a, item))]
        self.common_files = [item for item in self.common_files if not is_hidden(os.path.join(a, item))]
        self.common_funny = [item for item in self.common_funny if not is_hidden(os.path.join(a, item))]
    def phase3(self):
        """
        Override to filter hidden files in subdirectories.
        """
        self.subdirs = {
            item: DirComparisonNoHidden(os.path.join(self.left, item),
            os.path.join(self.right, item), self.ignore, self.hide)
            for item in self.common_dirs if not is_hidden(os.path.join(self.left, item))
            }
        
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# Wrapper around filecmp.dircmp to include all hidden and system files/folders
class DirComparisonWithHidden(filecmp.dircmp):
    def __init__(self, a, b, ignore=None, hide=None, *, shallow=True):
        # Initialize the parent class without excluding hidden files or directories
        super().__init__(a, b, ignore=ignore, hide=[])
        # Include hidden files and directories by using the original left and right lists
        self.left_list = list(os.listdir(a))
        self.right_list = list(os.listdir(b))
        # Update common sets to include hidden items as well
        self.common = [item for item in self.left_list if item in self.right_list]
        self.common_dirs = [item for item in self.common if os.path.isdir(os.path.join(a, item))]
        self.common_files = [item for item in self.common if os.path.isfile(os.path.join(a, item))]
        self.common_funny = [item for item in self.common if item not in self.common_dirs and item not in self.common_files]
    def phase3(self):
        """
        Override to include hidden files in subdirectories.
        """
        # Perform recursive comparison, including all subdirectories (hidden and non-hidden)
        self.subdirs = {
            item: DirComparisonWithHidden(os.path.join(self.left, item),
            os.path.join(self.right, item), self.ignore, self.hide) for item in self.common_dirs
        }
        
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# Logger
def setup_logger(log_path):
    
    logger = logging.getLogger("sync_logger")
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.DEBUG)
    # create console handler to write messages into console 
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    # add the handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)
    
    return logger

    # 'APPLICATION CODE     
    # logger.debug('debug message'),
    # logger.info('info message'),
    # logger.warning('warning message'), 
    # logger.error('error message'),
    # logger.critical('critical message'),
    
# ------------------------------------------------------------------------------------ 
# ------------------------------------------------------------------------------------
# Digest generator function 
def md5_digest(file_paths, chunk_size=4096):
    md5_hash = hashlib.md5()
    with open(file_paths, 'rb') as bin_files:
        while chunk := bin_files.read(chunk_size):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# Function to check if a file or directory is hidden
def is_hidden(path):
    return os.path.basename(path).startswith('.')

# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# Function for changing mode of hidden files and directories
def remove_readonly(func, path, _):
    """Clear read-only or hidden attributes and retry deletion."""
    os.chmod(path, stat.S_IWRITE)  # Change file to writable
    func(path)  # Retry the deletion
    
# ------------------------------------------------------------------------------------ 

""" Wrapper function over all functionality of program.
    Convinient way for testing porpuses by excluding argparse objects from testing module."""

def command_line_arguments_wrapper(args):
    
    SOURCE_DIR_PATH = args.source_dir_path
    DESTINATION_DIR_PATH = args.destination_dir_path
    OPTIONAL_FILTERING_IS_ON = args.filter_hidden_dirs_files
    LOG_PATH = args.log_path
    logger = setup_logger(LOG_PATH)

    """ Optional conditions for destination directory DELETION in case it exists.
        Writing all volume of sorce folder without hidden files into absolute new folder."""

    if OPTIONAL_FILTERING_IS_ON:
        if os.path.exists(DESTINATION_DIR_PATH):
            try:
                shutil.rmtree(DESTINATION_DIR_PATH, onexc=remove_readonly)
                logger.warning(f"Directory removed: <-- {DESTINATION_DIR_PATH}")
            except Exception as e:
                logger.error(f"Error deleting: {e} --> {DESTINATION_DIR_PATH}")  
                     
    # ------------------------------------------------------------------------------------ 
    # ------------------------------------------------------------------------------------
    # Directory synchronization function
    def one_way_synchronization(source_dir, destination_dir):

        # Ensure both source and destination directory exists
        if not os.path.exists(source_dir):
            logger.error(f"Source directory: {source_dir} does not exist. Enter a valid path and run the script again.")
            os.kill(os.getpid(), signal.SIGINT)
        if not os.path.exists(destination_dir):
            logger.warning(f"Destination directory: {destination_dir} does not exit.")
            os.makedirs(destination_dir)
            logger.info(f"Created directory in --> {destination_dir}.")


        """ Create objects for storing and comparing source and destination folder.
            Also optional for excluding all HIDDEN files and folders from comparison object."""

        comparison = None

        if OPTIONAL_FILTERING_IS_ON:
            comparison = DirComparisonNoHidden(source_dir, destination_dir)
        else:
            comparison = DirComparisonWithHidden(source_dir, destination_dir)

        # Sync files that are presented only in source folder
        for file_name in comparison.left_only:
            sorce_file = os.path.join(source_dir, file_name)
            destination_file = os.path.join(destination_dir, file_name)
            if os.path.isdir(sorce_file):
                shutil.copytree(sorce_file, destination_file)
                logger.info(f"Directory copied: {file_name} to --> {destination_file}.")
            else:
                shutil.copy2(sorce_file, destination_file)
                logger.info(f"File copied: {file_name} to --> {destination_file}.")


        # Sync files that are presented in both directories but differ, based on file Meta Data 
        for file_name in comparison.diff_files:
            sorce_file = os.path.join(source_dir, file_name)
            destination_file = os.path.join(destination_dir, file_name)

            """ For large datasets also enshure data integrity by comparing hashes of the files.
                Hash comparison is efficient for detecting changes in large files,
                as it can detect changes even when file metadata (such as modification time or size) might not reflect a difference."""

            source_hash = md5_digest(sorce_file)
            destination_hash = md5_digest(destination_file)
            if source_hash != destination_hash:
                shutil.copy2(sorce_file, destination_file)
                logger.info(f"File copied: {file_name} to --> {destination_file}.")


        # Recursive sync all subdirectories in source and destination folders
        for sub_dir in comparison.common_dirs:
            one_way_synchronization(os.path.join(source_dir, sub_dir), os.path.join(destination_dir, sub_dir))


        # Delete files and folders that are in destination folder only
        for file_name in comparison.right_only:
            destination_file = os.path.join(destination_dir, file_name)
            if os.path.isdir(destination_file):
                os.chmod(destination_file, stat.S_IWRITE)
                shutil.rmtree(destination_file)
                logger.warning(f"Directory removed: {file_name} from <-- {destination_file}.")
            else:
                os.chmod(destination_file, stat.S_IWRITE)
                os.remove(destination_file)
                logger.warning(f"File removed: {file_name} from <-- {destination_file}.")
                        
    command_line_arguments_wrapper.one_way_synchronization_ = one_way_synchronization
    
    return one_way_synchronization


    
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# Script is running with the infinit loop to keep destination folder up to date every time
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(prog="One_Way_Folder_Sync", description="......")
    parser.add_argument("source_dir_path", help="Enter a valid path to your source directory.", type=str)
    parser.add_argument("destination_dir_path", help="Enter a path where you want to store your destination folder.", type=str)
    parser.add_argument("log_path", help="Enter a path where you want to store your log file.", type=str)
    parser.add_argument("sync_period", help="Time for delaying and setting up a period of synchronization. Enter only int() type.", type=int)
    parser.add_argument("--filter_hidden_dirs_files", help= "Optional argument for filtering out hidden files and directories.", action="store_true")
    args = parser.parse_args()
    one_way_synchronization = command_line_arguments_wrapper(args)
    
    try:
        while True:
            # Delaying between periods of rerunning the script 
            time.sleep(args.sync_period)
            one_way_synchronization(args.source_dir_path, args.destination_dir_path)
    except KeyboardInterrupt:
        pass
    
# ------------------------------------------------------------------------------------
# Examples and explanation command line arguments for convinience.
# Enter in the next format:
#   1 - "C:\Users\your_name\Desktop\your_source_directory"
#   2 - "C:\Users\your_name\Desktop\your_destination_directory"
#   3 - "C:\Users\your_name\Desktop\logfile.log" or just "your_logfile.log" to genearate log into current directory
#   4 - delay: for example 5 seconds
#   5 - optional argument for filteriing hidden files
# For more information type | python main.py -h |....
# ------------------------------------------------------------------------------------     
                                # END
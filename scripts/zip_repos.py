import glob
import tarfile
import sys
import os
import time
import logging
from datetime import date, datetime


class ZipRepositories:
    def __init__(self, file_name, gen_zip, zip_path, zip_storage_count, backup_dir, parent_path):
        self.file_name = file_name
        self.generate_zip = gen_zip
        self.zip_path = zip_path
        self.zip_storage_count = (zip_storage_count, 0)[zip_storage_count is None]
        self.backup_dir = backup_dir
        self.parent_path = parent_path

    def remove_files_past_days(self, path_in, tarfile_list, file_extension='.tgz'):
        # Removes files past user_args.period number, removes older to newest
        # Files are removed based on the date in the file name
        try:
            file_list = [[], []]
            file_list_modified = []
            
            for file in tarfile_list:
                file_list[0].append(file)
                file_date = os.path.splitext(file.split("backup_")[1])[0]
                file_date_datetime = datetime.strptime(file_date, '%d%m%Y')
                file_list[1].append(file_date_datetime)

            oldest_date = min(file_list[1])
            oldest_backup = file_list[0][file_list[1].index(oldest_date)]

            if len(file_list[0]) > self.zip_storage_count:
                os.remove(os.path.abspath(oldest_backup))

            for files in os.listdir(path_in):
                if files.lower().startswith(f"{self.file_name}_backup_") and files.lower().endswith(file_extension.lower()):
                    file_list_modified.append(files)
                    
            if len(file_list_modified) > self.zip_storage_count:
                ZipRepositories.remove_files_past_days(self, path_in, file_list_modified, file_extension)

        except OSError as e:
            logging.error(f"Error occured deleting zip files past limit {self.zip_storage_count}, error: {e}")

    def backup_group_projects_to_tar(self):
        # Adds all repositories to tar file
        try:
            if self.generate_zip:
                os.chdir(self.zip_path)
                date_today = date.today()
                zip_filename = f'{self.file_name}_backup_{date_today.strftime("%d%m%Y")}.tgz'
                zip_file_extension = os.path.splitext(zip_filename)[1]
                zip_file_path = os.path.join(self.zip_path, zip_filename)
                zip_file_glob = glob.glob(f'{self.file_name}_backup*{zip_file_extension}')
                zip_file_exists = os.path.exists(os.path.abspath(zip_file_path))

                if zip_file_exists and len(zip_file_glob) <= self.zip_storage_count:
                    logging.warning(f"backup file {zip_filename} exists, exiting...")
                elif len(zip_file_glob) > 0 and self.zip_storage_count > 0:
                    tar_backup = tarfile.open(zip_filename, 'w|gz')
                    tarfile_list = []

                    if zip_file_exists:
                        logging.info(f"backup file {zip_filename} exists")
                    else:
                        tar_backup.add(self.backup_dir, recursive=True, arcname=self.parent_path)
                        tar_backup.close()
                        logging.info(f"Created tar backup file of repositories at: {zip_file_path}")

                    for file in os.listdir(self.zip_path):
                        if file.lower().startswith(f"{self.file_name}_backup_") and file.lower().endswith(zip_file_extension.lower()):
                            tarfile_list.append(file)

                    if len(tarfile_list) > self.zip_storage_count:
                        logging.info(f"Removing backup tarfiles over file limit of {self.zip_storage_count} tarfiles")
                        logging.info(f"Removing tarfiles based on oldest timestamp in backup tarfile to newest")
                        ZipRepositories.remove_files_past_days(self, self.zip_path, tarfile_list, zip_file_extension)

        except OSError as e:
            logging.error(f"Error has occured adding backups to tar file, error: {e}")
            sys.exit(1)

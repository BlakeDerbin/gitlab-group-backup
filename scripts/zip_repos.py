import glob
import tarfile
import sys
import os
import time
import logging
from datetime import date, datetime


class ZipRepositories:
    def __init__(self, file_name, gen_zip, zip_path, storage_days_zip, backup_dir, parent_path):
        self.generate_zip = gen_zip
        self.zip_path = zip_path
        self.zip_storage_days = (storage_days_zip, 0)[storage_days_zip is None]
        self.file_name = file_name
        self.backup_dir = backup_dir
        self.parent_path = parent_path

    def remove_files_past_days(self, path_in, file_type):
        # Removes files past user_args.period number, removes older to newest
        # Files are removed based on the date in the file name
        try:
            file_list = [[], []]
            file_list_modified = []

            for file in os.listdir(path_in):
                if file.lower().endswith(file_type.lower()):
                    file_list[0].append(file)
                    file_date = os.path.splitext(file.split("backup_")[1])[0]
                    file_date_datetime = datetime.strptime(file_date, '%d%m%Y')
                    file_list[1].append(file_date_datetime)

            oldest_date = min(file_list[1])
            oldest_backup = file_list[0][file_list[1].index(oldest_date)]

            if len(file_list[0]) > self.zip_storage_days:
                os.remove(os.path.abspath(oldest_backup))

            for files in os.listdir(path_in):
                if files.lower().endswith(file_type.lower()):
                    file_list_modified.append(files)
                    
            if len(file_list_modified) > self.zip_storage_days:
                ZipRepositories.remove_files_past_days(self, path_in, file_type)

        except OSError as e:
            logging.error(f"Error occured deleting zip files past limit {self.zip_storage_days}, error: {e}")

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

                if zip_file_exists and len(zip_file_glob) <= self.zip_storage_days:
                    logging.warning(f"backup file {zip_filename} exists, exiting...")
                elif len(zip_file_glob) > 0 and self.zip_storage_days > 0:
                    tar_backup = tarfile.open(zip_filename, 'w|gz')
                    tar_backup.add(self.backup_dir, recursive=True, arcname=self.parent_path)
                    tar_backup.close()
                    logging.info(f"Created tar backup file of repositories at: {zip_file_path}")
                    tarfile_list = []

                    for file in os.listdir(self.zip_path):
                        if file.lower().endswith(zip_file_extension.lower()):
                            tarfile_list.append(file)

                    if len(tarfile_list) > self.zip_storage_days:
                        logging.info(f"Removing backup tarfiles older than {self.zip_storage_days} days")
                        ZipRepositories.remove_files_past_days(self, self.zip_path, zip_file_extension)
                elif not zip_file_exists:
                    tar_backup = tarfile.open(zip_filename, 'w|gz')
                    logging.info(f"Created tar backup file of repositories at: {zip_file_path}")
                    tar_backup.add(self.backup_dir, recursive=True, arcname=self.parent_path)
                    tar_backup.close()
                else:
                    logging.info(f"backup file {zip_filename} exists, exiting...")

        except OSError as e:
            logging.error(f"Error has occured adding backups to tar file, error: {e}")
            sys.exit(1)

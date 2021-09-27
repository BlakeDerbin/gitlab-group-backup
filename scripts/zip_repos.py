import glob
import tarfile
import sys
import os
import time
from datetime import date


class ZipRepositories:
    def __init__(self, file_name, gen_zip, path_zip, storage_days_zip, log_file_path, dir_path, backup_path):
        self.generate_zip = gen_zip
        self.zip_path = path_zip
        self.zip_storage_days = storage_days_zip
        self.file_name = file_name
        self.log_file_path = log_file_path
        self.directory_path = dir_path
        self.backup_path = backup_path

    def remove_files_past_days(self, path_in, file_type):
        # Removes files past user_args.period number, removes older to newest
        try:
            file_list = []
            file_list_modified = []

            for file in os.listdir(path_in):
                if file.lower().endswith(file_type.lower()):
                    file_list.append(file)
            oldest_backup = min(file_list, key=os.path.getctime)
            if len(file_list) > self.zip_storage_days:
                os.remove(os.path.abspath(oldest_backup))
                time.sleep(0.1)

            for files in os.listdir(path_in):
                if files.lower().endswith(file_type.lower()):
                    file_list_modified.append(files)
            if len(file_list_modified) > self.zip_storage_days:
                ZipRepositories.remove_files_past_days(path_in, file_type)

        except OSError as e:
            log_file = open(self.log_file_path, 'a+')
            log_file.write(f"Error occured deleting zip file past {self.zip_storage_days} days\nError: {e}\n")
            log_file.close()

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
                log_file = open(self.log_file_path, 'a+')

                if zip_file_exists and len(zip_file_glob) <= self.zip_storage_days:
                    log_file.write(f"backup file {zip_filename} exists, exiting...\n")
                    log_file.close()
                elif len(zip_file_glob) > 0 and self.zip_storage_days > 0:
                    tar_backup = tarfile.open(zip_filename, 'w|gz')
                    tar_backup.add(self.directory_path, recursive=True, arcname=self.backup_path)
                    tar_backup.close()
                    log_file.write(f"Created tar backup file of repositories at: {zip_file_path}\n")
                    tarfile_list = []

                    for file in os.listdir(self.zip_path):
                        if file.lower().endswith(zip_file_extension.lower()):
                            tarfile_list.append(file)

                    if len(tarfile_list) > self.zip_storage_days:
                        log_file.write(f"Removing backup tarfiles older than {zip_storage_days} days\n")
                        ZipRepositories.remove_files_past_days(self.zip_path, zip_file_extension)
                    log_file.close()
                else:
                    tar_backup = tarfile.open(zip_filename, 'w|gz')
                    tar_backup.add(self.directory_path, recursive=True, arcname=self.backup_path)
                    tar_backup.close()
                    log_file.write(f"Created tar backup file of repositories at: {zip_file_path}\n")
                    log_file.close()

        except OSError as e:
            print(e)
            log_file = open(self.log_file_path, 'a+')
            log_file.write(f"Error has occured adding backups to tar file, exiting...\nError: {e}\n")
            log_file.close()
            sys.exit(1)

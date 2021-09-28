import sys
import errno
import stat
import os
import shutil
import argparse
from pathlib import Path
from scripts import gitlab, config, zip_repos

parser = argparse.ArgumentParser(description="This script will clone projects from a group and its subgroups from Gitlab")
parser.add_argument('-t', '--token', type=str, help='Gitlab API token')
parser.add_argument('-g', '--group', type=int, help='Gitlab group ID')
parser.add_argument('-d', '--directory', type=str, help='Backup directory path for the Gitlab group (OPTIONAL)')
parser.add_argument('-v', '--apiversion', type=str, help='Change the api version used for Gitlab API')
parser.add_argument('-e', '--export', type=str, help="Path to export gitlab backup tarfile to")
parser.add_argument('-r', '--remove', action='store_true', help="Removes backup directory")
parser.add_argument('-p', '--period', type=int, help='Sets the time period to keep log files, i.e. 30 days')
user_args = parser.parse_args()

if __name__ == '__main__':
    config = config.config_yaml()

    auth_token = (user_args.token, config['gitlab']['auth_token'])[user_args.token is None]
    group_ids = (user_args.group, config['gitlab']['group_ids'])[user_args.group is None].split(',')
    api_version = (user_args.apiversion, config['gitlab']['api_version'])[user_args.apiversion is None]
    api_url = config['gitlab']['api_url']
    log_file_path = (config['backup']['logfile_directory'], f'{Path.cwd}/backup_log.txt')[config['backup']['logfile_directory'] is None]
    remove_repo_dir = (user_args.remove, config['backup']['remove_directory'])[user_args.remove is False]
    test = config['backup']['remove_directory']

    parent_path = (user_args.directory,
                   (config['backup']['directory'], Path.cwd())
                   [config['backup']['directory'] is None]
                   )[user_args.directory is None]
    generate_zip = config['backup']['generate_zip_export']
    zip_path = (user_args.export,
                (config['backup']['zip_export_directory'], parent_path)
                [config['backup']['zip_export_directory'] is None]
                )[user_args.export is None]
    zip_storage_days = (user_args.period, config['backup']['zip_storage_days'])[user_args.period is None]

    def create_backup_directory(dir_in):
        # Creates backup directory
        try:
            path_exists = os.path.exists(dir_in)

            if not path_exists:
                os.makedirs(dir_in)
                log_file = open(log_file_path, 'a+')
                log_file.write(f"\nCreated backup directory: {dir_in}\n")
                log_file.close()

        except OSError as e:
            log_file = open(log_file_path, 'a+')
            log_file.write(f"Unable to create directory: {dir_in}\nError: {e}\n")
            log_file.close()
            sys.exit(1)

    def remove_backup_directory(backup_path_in, logfile_path_in, remove_dir=False):
        # Removes backup directory when the flag -r is used
        try:
            if remove_dir:
                shutil.rmtree(backup_path_in, ignore_errors=False, onerror=handle_remove_readonly)
                log_file = open(logfile_path_in, 'a+')
                log_file.write(f"Removed backup directory: {backup_path_in}\n")
        except OSError as e:
            log_file = open(logfile_path_in, 'a+')
            log_file.write(f"Unable to remove backup directory: {backup_path_in}\nError: {e}\n")
            log_file.close()

    def handle_remove_readonly(func, path, exc):
        # Handles removing directory if errors occur
        excvalue = exc[1]
        if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
            os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
            func(path)
        else:
            raise

    for group in group_ids:
        gitlab_backup = gitlab.GitlabBackup(auth_token, group.strip(), api_version, api_url, log_file_path)
        group_projects, group_name = gitlab_backup.fetch_group_projects()

        zip_filename = f'gitlab_{group_name.lower()}'
        backup_dir_name = f'gitlab_{group_name.lower()}_backups'
        backup_path = os.path.join(parent_path, backup_dir_name)

        create_backup_directory(backup_path)

        gitlab_backup.backup_group_repositories(backup_path, group_projects)

        # handles zipping gitlab projects
        gitlab_zip = zip_repos.ZipRepositories(
            zip_filename,
            generate_zip,
            zip_path,
            zip_storage_days,
            log_file_path,
            backup_path,
            parent_path
        )
        gitlab_zip.backup_group_projects_to_tar()

        remove_backup_directory(backup_path, log_file_path, remove_repo_dir)

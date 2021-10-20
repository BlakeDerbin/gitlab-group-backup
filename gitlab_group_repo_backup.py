import sys
import errno
import stat
import os
import shutil
import argparse
import logging
from datetime import datetime
from pathlib import Path
from scripts import gitlab, config, zip_repos

parser = argparse.ArgumentParser(
    description="This script will clone projects from a group and its subgroups from Gitlab")
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

    # gitlab clone group projects
    enable_gitlab_backup = (config['gitlab']['enable'], False)[config['gitlab']['enable'] is None]
    auth_token = (user_args.token, config['gitlab']['auth_token'])[user_args.token is None]
    group_ids = (user_args.group, config['gitlab']['group_ids'])[user_args.group is None].split(',')
    api_version = (user_args.apiversion, config['gitlab']['api_version'])[user_args.apiversion is None]
    api_url = config['gitlab']['api_url']
    log_file_path = (config['backup']['logfile_directory'], f'{Path.cwd}/gitlab_backup.log')[
        config['backup']['logfile_directory'] is None]
    remove_repo_dir = (user_args.remove, config['backup']['remove_directory'])[user_args.remove is False]

    parent_path = (user_args.directory,
                   (config['backup']['directory'], Path.cwd())
                   [config['backup']['directory'] is None]
                   )[user_args.directory is None]
    generate_zip = config['backup']['generate_zip_export']
    zip_path = (user_args.export,
                (config['backup']['zip_export_directory'], parent_path)
                [config['backup']['zip_export_directory'] is None]
                )[user_args.export is None]
    zip_storage_count = (user_args.period, config['backup']['zip_storage'])[user_args.period is None]

    # gitlab group project export
    enable_gitlab_export = (config['gitlab_export']['enable'], False)[config['gitlab_export']['enable'] is None]
    gitlab_export_dir = config['gitlab_export']['export_directory']
    gitlab_export_tar = config['gitlab_export']['export_tarfile_path']
    
    try:
        # Makes logfile directory if it doesn't exist
        if os.path.exists(log_file_path):
            logging.basicConfig(filename=log_file_path, level=logging.INFO)
        else:
            logfile_dir = log_file_path.rsplit("/", 1)
            os.makedirs(logfile_dir[0])
            logging.basicConfig(filename=log_file_path, level=logging.INFO)
    except OSError as e:
        print(f"Error: {e}")
        sys.exit(1)

    def create_directory(dir_in):
        # Creates directory
        try:
            path_exists = os.path.exists(dir_in)

            if not path_exists:
                os.makedirs(dir_in)
                logging.info(f"Created directory: {dir_in}")

        except OSError as e:
            logging.error(f"Unable to create directory: {dir_in}, error: {e}")
            sys.exit(1)


    def remove_directory(backup_path_in, remove_dir=False):
        # Removes backup directory when the flag -r is used
        try:
            if remove_dir:
                shutil.rmtree(backup_path_in, ignore_errors=False, onerror=handle_remove_readonly)
                logging.warning(f"Removed directory: {backup_path_in}")

        except OSError as e:
            logging.info(f"Unable to remove backup directory: {backup_path_in} error: {e}")


    def handle_remove_readonly(func, path, exc):
        # Handles removing directory if errors occur
        excvalue = exc[1]
        if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
            os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
            func(path)
        else:
            raise


    # Handles gitlab backups from group_id
    if enable_gitlab_backup:
        for group in group_ids:
            gitlab_backup = gitlab.GitlabBackup(auth_token, group.strip(), api_version, api_url)
            group_projects, group_name = gitlab_backup.fetch_group_projects()

            zip_filename = f'gitlab_{group_name.lower()}'
            backup_dir_name = f'gitlab_{group_name.lower()}_backups'
            backup_path = os.path.join(parent_path, backup_dir_name)

            create_directory(backup_path)

            gitlab_backup.backup_group_repositories(backup_path, group_projects)

            # handles zipping gitlab projects
            gitlab_zip = zip_repos.ZipRepositories(
                zip_filename,
                generate_zip,
                zip_path,
                zip_storage_count,
                backup_path,
                parent_path
            )
            gitlab_zip.backup_group_projects_to_tar()

            remove_directory(backup_path, remove_repo_dir)

            logging.info(f"Gitlab backup for group: {group_name} SUCESSFUL\n")
            print(f"Gitlab backup for group: {group_name} SUCESSFUL\n")

    # Handles group backups from gitlab group export of projects
    if enable_gitlab_export:
        gitlab_export = gitlab.GitlabExport(gitlab_export_dir, gitlab_export_tar)
        gitlab_export.backup_group_export()

        logging.info(f"Gitlab group project export from tarfile: {gitlab_export_tar} SUCCESFUL\n")
        print(f"Gitlab group project export from tarfile: {gitlab_export_tar} SUCCESFUL\n")

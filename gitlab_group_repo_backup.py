import sys
import errno
import stat
import os
import shutil
import argparse
from pathlib import Path
from scripts import gitlab, gitlab_config, zip_repos

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
    config = gitlab_config.config_yaml()

    auth_token = (user_args.token, config['gitlab']['auth_token'])[user_args.token is None]
    group_id = (user_args.group, config['gitlab']['group_id'])[user_args.group is None]
    api_version = (user_args.apiversion, config['gitlab']['api_version'])[user_args.apiversion is None]
    api_url = config['gitlab']['api_url']
    log_file_path = (config['backup']['logfile_directory'], f'{Path.cwd}/backup_log.txt')[
        config['backup']['logfile_directory'] is None]
    remove_repo_dir = (user_args.remove, config['backup']['remove_directory'])[user_args.remove is False]
    test = config['backup']['remove_directory']

    backup_path = f'gitlab_{group_id}_backups'
    parent_path = (user_args.directory,
                   (config['backup']['directory'], Path.cwd())
                   [config['backup']['directory'] is None]
                   )[user_args.directory is None]
    directory_path = os.path.join(parent_path, backup_path)
    generate_zip = config['backup']['generate_zip_export']
    zip_path = (user_args.export,
                (config['backup']['zip_export_directory'], parent_path)
                [config['backup']['zip_export_directory'] is None]
                )[user_args.export is None]
    zip_storage_days = (user_args.period, config['backup']['zip_storage_days'])[user_args.period is None]
    zip_filename = f'gitlab_{group_id}'

    gitlab_backup = gitlab.GitlabBackup(auth_token, group_id, api_version, api_url, log_file_path)
    group_projects = gitlab_backup.fetch_group_projects()

    # Creates backup directory
    try:
        path_exists = os.path.exists(directory_path)

        if not path_exists:
            os.makedirs(directory_path)
            log_file = open(log_file_path, 'a+')
            log_file.write(f"\ndirectory created: {directory_path}\n")
            log_file.close()

    except OSError as e:
        log_file = open(log_file_path, 'a+')
        log_file.write(f"Unable to create {directory_path}, exiting script...\nError: {e}\n")
        log_file.close()
        sys.exit(1)

    gitlab_backup.backup_group_repositories(directory_path, group_projects)

    # handles zipping gitlab projects
    gitlab_zip = zip_repos.ZipRepositories(
        zip_filename,
        generate_zip,
        zip_path,
        zip_storage_days,
        log_file_path,
        directory_path,
        parent_path
    )
    gitlab_zip.backup_group_projects_to_tar()

    def remove_backup_directory():
        # Removes backup directory when the flag -r is used
        try:
            if remove_repo_dir:
                shutil.rmtree(directory_path, ignore_errors=False, onerror=handle_remove_readonly)
                log_file = open(log_file_path, 'a+')
                log_file.write(f"{directory_path} directory deleted\n")
        except OSError as e:
            log_file = open(log_file_path, 'a+')
            log_file.write(f"Can't delete backup directory\nError: {e}\n")
            log_file.close()

    def handle_remove_readonly(func, path, exc):
        # Handles removing directory if errors occur
        excvalue = exc[1]
        if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
            os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
            func(path)
        else:
            raise

    try:
        remove_backup_directory()
    except OSError as e:
        print(f"OS error has occured: \n\n{e}")

import requests, json, git, sys, tarfile, time
import errno, stat, os, shutil, argparse, glob, random
from pathlib import Path
from datetime import date

### For this script to work you will need the folowing ###
# 1. A Gitlab token with both api_read & read_repository access
# 2. Your group_id from your gitlab group
# 3. Pip modules: requests, gitpython, pathlib

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

auth_token = user_args.token
group_id = user_args.group
api_version = (user_args.apiversion, 'v4')[user_args.apiversion is None]
clone_base_url = f'https://oauth2:{user_args.token}@gitlab.com/'
api_url = f'https://gitlab.com/api/{api_version}'
api_group_projects = f'{api_url}/groups/{group_id}/projects?private_token={auth_token}&include_subgroups=true'

backup_path = f'gitlab_{group_id}_backups'
parent_path = (user_args.directory, Path.cwd())[user_args.directory is None]
directory_path = os.path.join(parent_path, backup_path)
tarfile_path = (user_args.export, parent_path)[user_args.export is None]
log_file = open("backup_log.txt", "w+")
tarfile_storage_days = user_args.period

gitlab_group_project_link = []
gitlab_group_path_namespace = []


def fetch_group_projects():
    # Fetches a list of gitlab projects for the group id
    try:
        request = requests.get(api_group_projects)
        data = json.loads(request.text)

        for index in range(len(data)):
            for key in data[index]:
                if key == 'http_url_to_repo':
                    gitlab_group_project_link.append(data[index]['http_url_to_repo'])
                if key == 'path_with_namespace':
                    gitlab_group_path_namespace.append(data[index]['path_with_namespace'].split('/', 1))

        log_file.write(f"Successfully fetched projects for group ID: {group_id}\n")

    except OSError as e:
        log_file.write(f"Unable to fetch group ID: {group_id} projects, exiting script...\nError: {e}\n")
        log_file.close()
        sys.exit(1)


def make_backup_directory():
    # Creates backup directory
    try:
        path_exists = os.path.exists(directory_path)

        if not path_exists:
            os.makedirs(directory_path)
            log_file.write(f"directory created: {directory_path}\n")

    except OSError as e:
        log_file.write(f"Unable to create {directory_path}, exiting script...\nError: {e}\n")
        log_file.close()
        sys.exit(1)


def remove_backup_directory():
    # Removes backup directory when the flag -r is used
    try:
        if user_args.remove:
            shutil.rmtree(directory_path, ignore_errors=False, onerror=handle_remove_readonly)
            log_file.write(f"{directory_path} directory deleted\n")
    except OSError as e:
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


def backup_group_projects():
    # Handles cloning and pulling repositories to backup directory
    try:
        count = 0
        log_file.write("Starting backup for project repositories\n\n")

        for p in gitlab_group_project_link:
            repository_name = gitlab_group_path_namespace[count][1]
            file_path = os.path.join(directory_path, repository_name)
            path_exists = os.path.exists(os.path.abspath(file_path))

            # handles repository updating
            if path_exists:
                os.chdir(file_path)
                git.Git().remote('update')
                git_status = git.Git().status("-uno")

                if "up to date" not in git_status:
                    git.Git().pull("-r", "--autostash")
                    log_file.write(f"Pulled repository changes: {repository_name}\n")
                    os.chdir(directory_path)
                else:
                    log_file.write(f"repository up to date: {repository_name}\n")
                    os.chdir(directory_path)
                    continue

            # handles repository cloning
            if not path_exists:
                os.chdir(directory_path)
                git.Git().clone(clone_base_url + p.split("https://gitlab.com/")[1],
                                os.path.join(directory_path, gitlab_group_path_namespace[count][1]))
                log_file.write(f"cloned repository: {repository_name}\n")

            count += 1

        log_file.write(f"\nAll repositories for group ID: {group_id} have been backed up\n\n")

    except OSError as e:
        log_file.write(f"Unable to backup projects for group ID: {group_id}, exiting script...\nError: {e}\n")
        log_file.close()
        sys.exit(1)


def remove_files_past_days(path_in, file_type):
    # Removes files past user_args.period number, removes older to newest
    try:
        file_list = []
        file_list_modified = []

        for file in os.listdir(path_in):
            if file.lower().endswith(file_type.lower()):
                file_list.append(file)
        oldest_backup = min(file_list, key=os.path.getctime)
        if len(file_list) > tarfile_storage_days:
            os.remove(os.path.abspath(oldest_backup))
            time.sleep(0.1)

        for files in os.listdir(path_in):
            if files.lower().endswith(file_type.lower()):
                file_list_modified.append(files)
        if len(file_list_modified) > tarfile_storage_days:
            remove_files_past_days(path_in, file_type)

    except OSError as e:
        log_file.write(f"Error occured deleting log file past {tarfile_storage_days} days\nError: {e}\n")
        log_file.close()


def backup_group_projects_to_tar():
    # Adds all repositories to tar file
    try:
        os.chdir(tarfile_path)
        date_today = date.today()
        tar_filename = f'gitlab_{group_id}_backup_{date_today.strftime("%d%m%Y")}.tgz'
        tar_file = os.path.join(tarfile_path, tar_filename)
        tar_file_glob = glob.glob(f'gitlab_{group_id}_backup*.tgz')
        tar_file_exists = os.path.exists(os.path.abspath(tar_file))

        if tar_file_exists:
            log_file.write(f"backup file {tar_filename} exists, exiting...")
        elif len(tar_file_glob) > 0 and tarfile_storage_days > 0:
            tar_backup = tarfile.open(tar_filename, 'w|gz')
            tar_backup.add(directory_path, recursive=True, arcname=backup_path)
            tar_backup.close()
            log_file.write(f"Created tar backup file of repositories at: {tar_file}\n")
            tarfile_list = []

            for file in os.listdir(tarfile_path):
                if file.lower().endswith('.tgz'.lower()):
                    tarfile_list.append(file)

            if len(tarfile_list) > tarfile_storage_days:
                log_file.write(f"Removing backup tarfiles older than {tarfile_storage_days} days")
                remove_files_past_days(tarfile_path, '.tgz')
        else:
            tar_backup = tarfile.open(tar_filename, 'w|gz')
            tar_backup.add(directory_path, recursive=True, arcname=backup_path)
            tar_backup.close()
            log_file.write(f"Created tar backup file of repositories at: {tar_file}\n")

    except OSError as e:
        log_file.write(f"Error has occured adding backups to tar file, exiting...\nError: {e}\n")
        log_file.close()
        sys.exit(1)


try:
    fetch_group_projects()
    make_backup_directory()
    backup_group_projects()
    backup_group_projects_to_tar()
    remove_backup_directory()
    log_file.close()

except OSError as e:
    log_file.write(f"OS error has occured: \n\n{e}")

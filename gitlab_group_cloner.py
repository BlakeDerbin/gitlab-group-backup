import requests, json, git, sys, tarfile
import errno, stat, os, shutil, argparse
from pathlib import Path
from datetime import date

### For this script to work you will need the folowing ###
# 1. A Gitlab token with both api_read & read_repository access
# 2. Your group_id from your gitlab group
# 3. Pip modules: requests, gitpython, pathlib

parser = argparse.ArgumentParser(description="This script will clone projects from a group and its subgroups from Gitlab")
parser.add_argument('-t', '--token', type=str, help='Gitlab API token')
parser.add_argument('-g', '--group', type=int, help='Gitlab group ID')
parser.add_argument('-d', '--directory', type=str, help='Backup directory path for the gitlab group (OPTIONAL)')
user_args = parser.parse_args()

auth_token = user_args.token
group_id = user_args.group

clone_base_url = f'https://oauth2:{user_args.token}@gitlab.com/'
api_version = 'v4'
api_url = f'https://gitlab.com/api/{api_version}' 
api_group_projects = f'{api_url}/groups/{group_id}/projects?private_token={auth_token}&include_subgroups=true'

backup_path = f'gitlab_{group_id}_backups'
parent_path = (user_args.directory, Path.cwd())[user_args.directory is None]
directory_path = os.path.join(parent_path, backup_path)
log_file = open("backup_log.txt", "w+")

gitlab_group_project_link = []
gitlab_group_path_namespace = []


def handle_remove_readonly(func, path, exc):
    # Use the command below with this function if you want to remove the repo instead of pull --rebase
    # shutil.rmtree(filePath, ignore_errors=False, onerror=handle_remove_readonly)
    excvalue = exc[1]
    if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO) # 0777
        func(path)
    else:
        raise


def fetch_group_projects():
    request = requests.get(api_group_projects)
    data = json.loads(request.text)
    try:
        for index in range(len(data)):
            for key in data[index]:
                if key == 'http_url_to_repo':
                    gitlab_group_project_link.append(data[index]['http_url_to_repo'])
                if key == 'path_with_namespace':
                    gitlab_group_path_namespace.append(data[index]['path_with_namespace'].split('/',1))
        log_file.write(f"Successfully fetched projects for group ID: {group_id}\n")
    except:
        log_file.write(f"Unable to fetch group ID: {group_id} projects, exiting script...\n")
        log_file.close()
        sys.exit(1)


def make_backup_directory():
    path_exists = os.path.exists(directory_path)
    try:
        if not path_exists:
            os.makedirs(directory_path)
            log_file.write(f"directory created: {directory_path}\n")
    except:
        log_file.write(f"Unable to create {directory_path}, exiting script...\n")
        log_file.close()
        sys.exit(1)


def backup_group_projects():
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
                                os.path.join(directory_path,gitlab_group_path_namespace[count][1]))
                log_file.write(f"cloned repository: {repo_name}\n")

            count += 1

        log_file.write(f"\nAll repositories for group ID: {group_id} have been backed up\n\n")
    except:
        log_file.write(f"Unable to backup projects for group ID: {group_id}, exiting script...\n")
        log_file.close()
        sys.exit(1)


# add all repositories to tar file
def backup_group_projects_to_tar():
    try:
        os.chdir(parent_path)
        date_today = date.today()
        tar_filename = f'gitlab_{group_id}_backup_{date_today.strftime("%d%m%Y")}.tgz'
        tar_filepath = os.path.join(parent_path, tar_filename)

        tar_file_exists = os.path.exists(os.path.abspath(tar_filepath))
        directory_path_exists = os.path.exists(os.path.abspath(directory_path))

        if directory_path_exists:
            if tar_file_exists:
                log_file.write(f"{tar_filename} exists, no new tarfile will be generated\n")
            else:
                tar_backup = tarfile.open(tar_filename, 'w:gz')
                tar_backup.add(f"{directory_path}", recursive=True)
                log_file.write(f"Created tar backup file of repositories: {tar_filename}\n")
        else:
            log_file.write("backup directory doesn't exist, exiting script...\n")
            log_file.close()
            sys.exit(1)
    except:
        log_file.write(f"Error has occured adding backups to tar file: {tar_filename}, exiting...")
        log_file.close()
        sys.exit(1)


fetch_group_projects()
make_backup_directory()
backup_group_projects()
backup_group_projects_to_tar()
log_file.close()
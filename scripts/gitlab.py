import requests
import json
import git
import sys
import os
import tarfile
import shutil
from datetime import datetime
from pathlib import Path
import logging


class GitlabBackup:
    def __init__(self, auth_token, group_id, api_version, api_url):
        self.auth_token = auth_token
        self.group_id = group_id
        self.api_version = api_version
        self.api_url = api_url + self.api_version
        self.clone_base_url = f'https://oauth2:{self.auth_token}@gitlab.com/'
        self.api_group_projects = f'{self.api_url}/groups/{self.group_id}/projects?private_token={self.auth_token}&include_subgroups=true'

    def fetch_group_projects(self):
        # Fetches a list of gitlab projects for the group id
        try:
            date_now = datetime.now().strftime("%d/%m/%Y - %I:%M %p")
            request = requests.get(self.api_group_projects)
            data = json.loads(request.text)
            group_projects = [[], []]
            logging.info(f"[{date_now}] Starting backup for group ID: {self.group_id} repositories")

            for index in range(len(data)):
                for key in data[index]:
                    if key == 'http_url_to_repo':
                        group_projects[0].append(data[index]['http_url_to_repo'])
                    if key == 'path_with_namespace':
                        group_projects[1].append(data[index]['path_with_namespace'].split('/', 1))

            group_name = data[0]['name_with_namespace'].split('/', 1)
            logging.info(f"Successfully fetched projects for group ID: {self.group_id}")
            return group_projects, group_name[0].replace(" ", "")
        except OSError as e:
            logging.error(f"Unable to fetch group ID: {self.group_id} projects, error: {e}")
            sys.exit(1)

    def backup_group_repositories(self, directory_path, group_projects_arr):
        # Handles cloning and pulling repositories to backup directory
        try:
            count = 0

            for p in group_projects_arr[0]:
                repository_name = group_projects_arr[1][count][1]
                file_path = os.path.join(directory_path, repository_name)
                path_exists = os.path.exists(os.path.abspath(file_path))

                # handles repository updating
                if path_exists:
                    os.chdir(file_path)
                    git.Git().remote('update')
                    git_status = git.Git().status("-uno")

                    if "up to date" in git_status:
                        logging.info(f"Repository up to date: {repository_name}")
                        os.chdir(directory_path)
                    elif "No commits yet" in git_status:
                        logging.info(f"No commits in repository: {repository_name}")
                        os.chdir(directory_path)
                    else:
                        git.Git().pull("-r", "--autostash")
                        logging.info(f" Pulled repository changes: {repository_name}")
                        os.chdir(directory_path)

                # handles repository cloning
                if not path_exists:
                    os.chdir(directory_path)
                    git.Git().clone(self.clone_base_url + p.split("https://gitlab.com/")[1],
                                    os.path.join(directory_path, repository_name))
                    logging.info(f"Cloned repository: {repository_name}")

                count += 1
            logging.info(f"All repositories for group ID: {self.group_id} have been backed up")

        except OSError as e:
            logging.error(f"Unable to backup projects for group ID: {self.group_id}, error: {e}")
            sys.exit(1)
    

class GitlabExport():
    def __init__(self, group_export_dir, group_export_tarfile):
        self.group_export_dir = group_export_dir
        self.group_export_tarfile = group_export_tarfile

    def extract_zip(file_path, dir_name, output_path):
        # Used to export each project export out of group export tarfile
        try:
            with tarfile.open(file_path) as project_tar:
                subdir_with_files = [
                    tarinfo for tarinfo in project_tar.getmembers()
                    if tarinfo.name.startswith(dir_name)
                ]
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(project_tar, members=subdir_with_files)
        except OSError as e:
            print(f"project export for tarfile: {file_path} FAILED\nERROR: {e}")
            logging.info()
            sys.exit(1)

    def backup_group_export(self):
        # handles exporting project exports out of gitlab group export tarfile
        try:
            os.chdir(self.group_export_dir)
            tar = tarfile.open(self.group_export_tarfile)
            date_now = datetime.now().strftime("%d/%m/%Y - %I:%M %p")

            # gets a list of tarfiles in the group export zip
            export_list = [tar_dir for tar_dir in tar.getnames() if 'tar.gz' in tar_dir]

            for export in export_list:
                export_path = (export.rsplit("/", 1))[0]
                export_file = (export.rsplit("/", 1))[1]
                full_path = f"{self.group_export_dir}/{export_path}"
                path_exists = os.path.exists(os.path.abspath(full_path))

                repository_name = (export.rsplit("/", 2))[1]
                repository_path = os.path.join(full_path, "repository")
                repository_exists = os.path.exists(os.path.abspath(repository_path))

                bundle_file = Path(f"{full_path}/project.bundle")
                export_file = Path(f"{full_path}/export.tar.gz")
                bundle_exists = bundle_file.is_file()
                export_exists = export_file.is_file()

                if path_exists:
                    os.chdir(full_path)      

                    if repository_exists and bundle_exists:
                        # handles repository updates
                        os.chdir(repository_path)
                        git.Git().remote('update')
                        git_status = git.Git().status("-uno")

                        if "up to date" in git_status:
                            logging.info(f"Repository up to date: {repository_name}")
                        elif "No commits yet" in git_status:
                            logging.info(f"No commits in repository: {repository_name}")
                        else:
                            git.Git().pull("-r", "--autostash")
                            logging.info(f"Pulled repository changes: {repository_name}")

                    else:
                        # extracts and clones the project.bundle from a project export
                        if bundle_exists:
                            git.Git().clone(f"project.bundle", f"repository")
                            logging.info(f"Repository cloned: {repository_name}")
                        elif not bundle_exists and not repository_exists and export_exists:
                            GitlabExport.extract_zip(export_file, "./project", self.group_export_dir)
                            git.Git().clone(f"project.bundle", f"repository")
                            logging.info(f"Repository cloned: {repository_name}")
                        else:
                            os.chdir(self.group_export_dir)
                            GitlabExport.extract_zip(self.group_export_tarfile, export_path, self.group_export_dir)
                            os.chdir(full_path)
                            GitlabExport.extract_zip(export_file, "./project", self.group_export_dir)
                            if os.path.isdir("repository"):
                                shutil.rmtree("repository")

                            git.Git().clone(f"project.bundle", f"repository")
                            logging.info(f"Repository cloned: {repository_name}")

                if not path_exists:
                    # When exports don't exist
                    logging.info(f"Extracting project export: {export} from tarfile: {self.group_export_tarfile}")
                    os.chdir(self.group_export_dir)
                    GitlabExport.extract_zip(self.group_export_tarfile, export_path, self.group_export_dir)
                    os.chdir(full_path)
                    GitlabExport.extract_zip(export_file, "./project", self.group_export_dir)
                    git.Git().clone(f"project.bundle", f"repository")
                    logging.info(f"Repository cloned: {repository_name}")
            
        except OSError as e:
            logging.error(f"Gitlab group project export from tarfile: {self.group_export_tarfile} FAILED - ERROR: {e}")
            print(f"Gitlab group project export from tarfile: {self.group_export_tarfile} FAILED\nERROR: {e}")
            sys.exit(1)

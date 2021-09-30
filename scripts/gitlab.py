import requests
import json
import git
import sys
import os
import tarfile
import shutil
from datetime import datetime
from pathlib import Path


class GitlabBackup:
    def __init__(self, auth_token, group_id, api_version, api_url, logfile_directory):
        self.auth_token = auth_token
        self.group_id = group_id
        self.api_version = api_version
        self.api_url = api_url + self.api_version
        self.clone_base_url = f'https://oauth2:{self.auth_token}@gitlab.com/'
        self.api_group_projects = f'{self.api_url}/groups/{self.group_id}/projects?private_token={self.auth_token}&include_subgroups=true'
        self.log_file = open(logfile_directory, 'a+')

    def fetch_group_projects(self):
        # Fetches a list of gitlab projects for the group id
        try:
            date_now = datetime.now().strftime("%d/%m/%Y - %I:%M %p")
            request = requests.get(self.api_group_projects)
            data = json.loads(request.text)
            group_projects = [[], []]
            self.log_file.write(f"\n[{date_now}] Starting backup for group ID: {self.group_id} repositories\n\n")

            for index in range(len(data)):
                for key in data[index]:
                    if key == 'http_url_to_repo':
                        group_projects[0].append(data[index]['http_url_to_repo'])
                    if key == 'path_with_namespace':
                        group_projects[1].append(data[index]['path_with_namespace'].split('/', 1))

            group_name = data[0]['name_with_namespace'].split('/', 1)
            self.log_file.write(f"Successfully fetched projects for group ID: {self.group_id}\n\n")
            return group_projects, group_name[0].replace(" ", "")
        except OSError as e:
            self.log_file.write(f"\nUnable to fetch group ID: {self.group_id} projects, exiting script...\nError: {e}\n")
            self.log_file.close()
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
                        self.log_file.write(f"Repository up to date: {repository_name}\n")
                        os.chdir(directory_path)
                    elif "No commits yet" in git_status:
                        self.log_file.write(f"No commits in repository: {repository_name}\n")
                        os.chdir(directory_path)
                    else:
                        git.Git().pull("-r", "--autostash")
                        self.log_file.write(f"Pulled repository changes: {repository_name}\n")
                        os.chdir(directory_path)

                # handles repository cloning
                if not path_exists:
                    os.chdir(directory_path)
                    git.Git().clone(self.clone_base_url + p.split("https://gitlab.com/")[1],
                                    os.path.join(directory_path, repository_name))
                    self.log_file.write(f"Cloned repository: {repository_name}\n")

                count += 1

            self.log_file.write(f"\nAll repositories for group ID: {self.group_id} have been backed up\n\n")
            self.log_file.close()

        except OSError as e:
            self.log_file.write(f"\nUnable to backup projects for group ID: {self.group_id}, exiting script...\nError: {e}\n")
            self.log_file.close()
            sys.exit(1)
    

class GitlabExport():
    def __init__(self, group_export_dir, group_export_tarfile, logfile_dir):
        self.group_export_dir = group_export_dir
        self.group_export_tarfile = group_export_tarfile
        self.log_file = open(logfile_dir, 'a+')

    def extract_zip(file_path, dir_name, output_path):
        # Used to export each project export out of group export tarfile
        try:
            with tarfile.open(file_path) as project_tar:
                subdir_with_files = [
                    tarinfo for tarinfo in project_tar.getmembers()
                    if tarinfo.name.startswith(dir_name)
                ]
                project_tar.extractall(members=subdir_with_files)
        except OSError as e:
            print(f"project export for tarfile: {file_path} FAILED\nERROR: {e}")
            self.log_file.write(f"\nUnable to extract gitlab export tarfile\nError: {e}\n\n")
            self.log_file.close()
            sys.exit(1)

    def backup_group_export(self):
        # handles exporting project exports out of gitlab group export tarfile
        try:
            os.chdir(self.group_export_dir)
            tar = tarfile.open(self.group_export_tarfile)
            date_now = datetime.now().strftime("%d/%m/%Y - %I:%M %p")
            self.log_file.write(f"\n[{date_now}] Starting gitlab group export from tarfile: {self.group_export_tarfile}\n\n")

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
                            self.log_file.write(f"Repository up to date: {repository_name}\n")
                        elif "No commits yet" in git_status:
                            self.log_file.write(f"No commits in repository: {repository_name}\n")
                        else:
                            git.Git().pull("-r", "--autostash")
                            self.log_file.write(f"Pulled repository changes: {repository_name}\n")

                    else:
                        # extracts and clones the project.bundle from a project export
                        if bundle_exists:
                            git.Git().clone(f"project.bundle", f"repository")
                            self.log_file.write(f"Repository cloned: {repository_name}\n")
                        elif not bundle_exists and not repository_exists and export_exists:
                            GitlabExport.extract_zip(export_file, "./project", self.group_export_dir)
                            git.Git().clone(f"project.bundle", f"repository")
                            self.log_file.write(f"Repository cloned: {repository_name}\n")
                        else:
                            os.chdir(self.group_export_dir)
                            GitlabExport.extract_zip(self.group_export_tarfile, export_path, self.group_export_dir)
                            os.chdir(full_path)
                            GitlabExport.extract_zip(export_file, "./project", self.group_export_dir)
                            if os.path.isdir("repository"):
                                shutil.rmtree("repository")

                            git.Git().clone(f"project.bundle", f"repository")
                            self.log_file.write(f"Repository cloned: {repository_name}\n")

                if not path_exists:
                    # When exports don't exist
                    self.log_file.write(f"Extracting project export: {export} from tarfile: {self.group_export_tarfile}\n")
                    os.chdir(self.group_export_dir)
                    GitlabExport.extract_zip(self.group_export_tarfile, export_path, self.group_export_dir)
                    os.chdir(full_path)
                    GitlabExport.extract_zip(export_file, "./project", self.group_export_dir)
                    git.Git().clone(f"project.bundle", f"repository")
                    self.log_file.write(f"Repository cloned: {repository_name}\n")
            
            self.log_file.close()
        except OSError as e:
            print(f"Gitlab group project export from tarfile: {self.group_export_tarfile} FAILED\nERROR: {e}")
            self.log_file.write(f"\nUnable to backup Gitlab export\nError: {e}\n\n")
            self.log_file.close()
            sys.exit(1)

import requests
import json
import git
import sys
import os
from datetime import datetime


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
            self.log_file.write(f"\n[{date_now}] Starting backup for group ID: {self.group_id} repositories!\n\n")

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
            self.log_file.write(f"Unable to fetch group ID: {self.group_id} projects, exiting script...\nError: {e}\n")
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

                    if "up to date" not in git_status:
                        git.Git().pull("-r", "--autostash")
                        self.log_file.write(f"Pulled repository changes: {repository_name}\n")
                        os.chdir(directory_path)
                    else:
                        self.log_file.write(f"repository up to date: {repository_name}\n")
                        os.chdir(directory_path)

                # handles repository cloning
                if not path_exists:
                    os.chdir(directory_path)
                    git.Git().clone(self.clone_base_url + p.split("https://gitlab.com/")[1],
                                    os.path.join(directory_path, repository_name))
                    self.log_file.write(f"cloned repository: {repository_name}\n")

                count += 1

            self.log_file.write(f"\nAll repositories for group ID: {self.group_id} have been backed up\n\n")
            self.log_file.close()

        except OSError as e:
            self.log_file.write(f"Unable to backup projects for group ID: {self.group_id}, exiting script...\nError: {e}\n")
            self.log_file.close()
            sys.exit(1)

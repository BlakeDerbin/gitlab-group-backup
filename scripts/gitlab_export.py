import sys
import os
import git
import requests
import glob
import tarfile
import re
import time
from datetime import datetime
from pathlib import Path

class export_project_bundle():
    def __init__(self, export_dir):
        self.export_dir = export_dir

    def zip_projects(dir_to_zip):
        os.chdir(dir_to_zip)
        tar_zip = tarfile.open("tar_backup.tgz", "w|gz")
        tar_zip.add(dir_to_zip, arcname="backups")
        return True

    def extract_zip(file_path, dir_name):
        print(f"file-path: {file_path}")
        print(f"name: {dir_name}")
        with tarfile.open(file_path) as project_tar:
            subdir_with_files = [
                tarinfo for tarinfo in project_tar.getmembers()
                if tarinfo.name.startswith(dir_name)
            ]
            project_tar.extractall(members=subdir_with_files)

    
    def backup_group_export(export_dir, group_zip):
        os.chdir(export_dir)
        export_list = []
        group_export_tar = group_zip

        if group_zip:
            tar = tarfile.open(group_zip)
            for member in tar.getnames():
                if 'tar.gz' in member:
                    export_list.append(member)
                    print(member)

            for export in export_list:
                export_file_path = export.rsplit("/", 1)
                export_path = export_file_path[0]
                export_file = export_file_path[1]
                full_path = f"{export_dir}/{export_file_path[0]}"
                path_exists = os.path.exists(os.path.abspath(full_path))

                repo = export.rsplit("/", 2)
                print(repo)
                repository_name = repo[1]
                repository_path = os.path.join(full_path, "repository")
                print(repository_path)
                repository_exists = os.path.exists(os.path.abspath(repository_path))
                bundle = Path(f"{full_path}/project.bundle")
                bundle_exists = bundle.is_file()
                export_file = Path(f"{full_path}/export.tar.gz")
                export_exists = export_file.is_file()
                print(f"full path: {full_path}\n")
                print(f"path exists: {path_exists}\nrepo dir exists: {repository_exists}\nbundle exists: {bundle_exists}\nexport exists: {export_exists}\n")

                if path_exists:
                    os.chdir(full_path)      
                                  
                    if repository_exists and bundle_exists:
                        # handles repository updates
                        os.chdir(repository_path)
                        
                        git.Git().remote('update')
                        git_status = git.Git().status("-uno")

                        if "up to date" in git_status:
                            print(f"Repository up to date: {repository_name}\n")
                            #os.chdir(export_dir)
                        elif "No commits yet" in git_status:
                            print(f"No commits in repository: {repository_name}\n")
                            #os.chdir(directory_path)
                        else:
                            git.Git().pull("-r", "--autostash")
                            print(f"Pulled repository changes: {repository_name}\n")
                            #os.chdir(directory_path)

                    else:
                        # extracts and clones the project.bundle from a project export
                        os.chdir(full_path)
                        if bundle_exists:
                            print("project.bundle exists\n")
                            git.Git().clone(f"project.bundle", f"repository")
                            print(f"Repository cloned: {repository_name}\n")
                        elif not bundle_exists and not repository_exists and export_exists:
                            export_project_bundle.extract_zip(export_file, "./project")
                            git.Git().clone(f"project.bundle", f"repository")
                            print(f"Repository cloned: {repository_name}\n")
                        else:
                            print("in final else")
                            os.chdir(export_dir)
                            print(export_path)
                            export_project_bundle.extract_zip(group_export_tar, export_path)
                            os.chdir(full_path)
                            export_project_bundle.extract_zip(export_file, "./project")
                            export_project_bundle.export_backup_projects(export_dir, group_zip)

                if not path_exists:
                    print(f"Extracting project export {export} from {group_export_tar}")
                    print(full_path)
                    os.chdir(export_dir)
                    export_project_bundle.extract_zip(group_export_tar, export_path)
                    export_project_bundle.backup_group_export(export_dir, group_zip)


#export_project_bundle(dir_in)
#export_project_bundle.zip_projects(export_dir)
export_project_bundle.backup_group_export(
    '/mnt/c/Users/derbinb/source/gitlab-group-backup', 
    'tar_backup.tgz')
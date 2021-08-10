import requests, json, git, sys
import errno, stat, os, shutil
from pathlib import Path

### For this script to work you will need the folowing ###
# 1. A Gitlab token with both api_read & read_repository access
# 2. Your group_id from your gitlab group
# 3. Pip modules: requests, gitpython, pathlib

token = sys.argv[1]
groupID = sys.argv[2]

cloneBaseURL = f'https://oauth2:{token}@gitlab.com/'
apiBaseURL = f'http://gitlab.com/api/v4/groups/{groupID}/projects?private_token={token}&include_subgroups=true'

backupPath = f'gitlab_{groupID}_backups'
parentPath = Path.cwd()
directoryPath = os.path.join(parentPath, backupPath)

gitlabGroupProjectName = []
gitlabGroupProjectLink = []

def handleRemoveReadonly(func, path, exc):
  # Use the command below with this function if you want to remove the repo instead of pull --rebase
  # shutil.rmtree(filePath, ignore_errors=False, onerror=handleRemoveReadonly)
  excvalue = exc[1]
  if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
      os.chmod(path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO) # 0777
      func(path)
  else:
      raise


def makeDir(path_in):
    pathExists = os.path.exists(path_in)
    if not pathExists:
        os.mkdir(path_in)
        print(f"directory created: {path_in}")


def fetchGroupProjects():
    request = requests.get(apiBaseURL)
    data = json.loads(request.text)
    count = 0

    while count < len(data):
        gitlabGroupProjectName.append(data[count]['name'])
        gitlabGroupProjectLink.append(data[count]['http_url_to_repo'])
        count += 1
    

def cloneGroupProjects():
    count = 0

    for p in gitlabGroupProjectLink:
        currentRepoName = gitlabGroupProjectName[count]
        filePath = parentPath / backupPath / currentRepoName.lower()
        pathExists = os.path.exists(os.path.abspath(filePath))
        
        # handles repository updating
        if pathExists:
            os.chdir(filePath)
            git.Git().remote('update')
            gitStatus = git.Git().status("-uno")

            if "up to date" not in gitStatus:
                git.Git().pull("-r", "--autostash")
                print(f"pulled repo: {currentRepoName}")
                os.chdir(directoryPath)
            else:
                print(f"repo up to date: {currentRepoName}\nno new changes pulled")
                os.chdir(directoryPath)

        # handles repository cloning
        if not pathExists:
            os.chdir(directoryPath)
            git.Git().clone(cloneBaseURL + p.split("https://gitlab.com/")[1])
            print(f"cloned repo: {currentRepoName}")

        count += 1


try:
    # check backup directory exists
    makeDir(directoryPath)
    fetchGroupProjects()
    cloneGroupProjects()
except:
    print("ERROR: Ensure that you're running the script with the right arguments \n")
    print("gitlab_group_cloner.py <API_TOKEN> <GROUP_ID> \n")
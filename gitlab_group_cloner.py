import requests, json, git, sys
import errno, stat, os, shutil
from pathlib import Path

### For this script to you will need the folowing ###
# 1. A Gitlab token with both api_read & read_repository access
# 2. Your group_id from your gitlab group
# 3. Pip modules: requests, gitpython

token = sys.argv[1]
groupID = sys.argv[2]

cloneBaseURL = f'https://oauth2:{token}@gitlab.com/'
apiBaseURL = f'http://gitlab.com/api/v4/groups/{groupID}/projects?private_token={token}'

gitlabGroupProjectName = []
gitlabGroupProjectLink = []

def handleRemoveReadonly(func, path, exc):
  # Use the command below with this function if you want to remove the repo instead of pull --rebase
  # shutil.rmtree(file_path, ignore_errors=False, onerror=handleRemoveReadonly)
  excvalue = exc[1]
  if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
      os.chmod(path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO) # 0777
      func(path)
  else:
      raise

def fetchGroupProjects():
    request = requests.get(apiBaseURL)
    data = json.loads(request.text)
    count = 0

    while count < len(data):
        gitlabGroupProjectName.append(data[count]['name'])
        gitlabGroupProjectLink.append(data[count]['http_url_to_repo'])
        count += 1
    
    cloneGroupProjects()

def cloneGroupProjects():
    count = 0
    directoryPath = Path.cwd()

    for p in gitlabGroupProjectLink:
        file_path = directoryPath / gitlabGroupProjectName[count]

        # handles repository updating
        if(file_path.exists()):
            os.chdir(file_path)
            gitStatus = git.Git().status("-uno")

            if("up to date" not in gitStatus):
                git.Git().pull("-r", "--autostash")
                print(f"pulled repo: {gitlabGroupProjectName[count]}")
            else:
                print(f"repo up to date: {gitlabGroupProjectName[count]}\nno new changes pulled")

        # handles repository cloning
        if(file_path.exists() == False):
            p.split("https://gitlab.com/")
            git.Git().clone(cloneBaseURL + p.split("https://gitlab.com/")[1])
            print(f"cloned repo: {gitlabGroupProjectName[count]}")

        count += 1


try:
    fetchGroupProjects()
except:
    print("Ensure that you're running the script with the right arguments \n")
    print("gitlab_group_cloner.py <API_TOKEN> <GROUP_ID> \n")
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
        if(file_path.exists()):
            shutil.rmtree(file_path, ignore_errors=False, onerror=handleRemoveReadonly)
            print(f"removed repo: {gitlabGroupProjectName[count]}")
        if(file_path.exists() == False):
            p.split("https://gitlab.com/")
            print(p)
            git.Git().clone(cloneBaseURL + p.split("https://gitlab.com/")[1])
            print(f"cloned repo: {gitlabGroupProjectName[count]}")
        count += 1


fetchGroupProjects()
#!/bin/bash -l

# BD: 9/8/21
# This bash script will load the modules and install pip packages to run the python script
# You will need to run the bash script how you would the python script:
#
# bash gitlab_group_repo_backup.sh <TOKEN_ID> <GROUP_ID> <DIRECTORY> (OPTIONAL)

module load aarnetproxy python36
python -m pip --disable-pip-version-check install requests gitpython > /dev/null

if [ -z "$3" ]
then
    echo -e "Executing gitlab_group_repo_backup.py\n"
    python3 gitlab_group_repo_backup.py -t $1 -g $2
else
    echo -e "Executing gitlab_group_repo_backup.py\n"
    python3 gitlab_group_repo_backup.py -t $1 -g $2 -d $3
fi

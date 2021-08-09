#!/bin/bash

# BD: 9/8/21
# This bash script will load the modules and install pip packages to run the python script
# You will need to run the bash script how you would the python script:
#
# bash gitlab_cloner_bash.sh <TOKEN_ID> <GROUP_ID>

DIR=/export/home/$USER/gitlab-group-cloner/
module load aarnetproxy python36
python -m pip install requests gitpython > /dev/null

if [ -d "$DIR" ]
then
    cd ~/gitlab-group-cloner
    echo "Checking script for changes"
    git pull -r --autostash
else
    echo "gitlab-group-cloner repo not cloned, cloning repo to home directory"
    git clone https://github.com/BlakeDerbin/gitlab-group-cloner.git
    cd ~/gitlab-group-cloner
fi

echo -e "Executing gitlab_group_cloner.py\n"
python3 gitlab_group_cloner.py $1 $2
# gitlab-group-cloner

This script is used to fetch projects under a group in gitlab and clone all the projects into either the working directory of the script or a specified directory.

To use this script you will need the following:

* A Gitlab token with both api_read & read_repository access
* Your group_id from your gitlab group
* Pip modules: requests, gitpython

## Running the script

You can modify the script to inculde your token and group_id if you don't want to provide it as an argument, the script uses the following arguments:

* -t or --token = the api token from your Gitlab group with api_read & read_repository access.
* -g or --group = the id for your Gitlab group.
* -d or --directory = the directory where you wish to store the backups, if no directory is specified the directory will backup directory will be created in the working directory of the script

An example of how you would execute this script:

* python gitlab_group_cloner.py -t <API_TOKEN> -g <GROUP_ID> -d <BACKUP_DIRECTORY> (OPTIONAL)

## Using the BASH script

This was created mainly to load modules before executing the script and is used in a simlar way to the python script, you will also need the python script in the same directory as the bash script:

* bash gitlab_group_cloner.sh <API_TOKEN> <GROUP_ID> <BACKUP_DIRECTORY> (OPTIONAL)

# gitlab-group-cloner

This script is used to fetch projects under a group in gitlab and clone all the projects into the working directory of the script.

To use this script you will need the following:

* 1. A Gitlab token with both api_read & read_repository access
* 2. Your group_id from your gitlab group
* 3. Pip modules: requests, gitpython

## Running the script

You can modify the script to hardcode your token and group_id but if you don't need to do this you can execute the script in the following way:

* python gitlab_group_cloner.py <TOKEN> <GROUD_ID>
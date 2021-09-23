# Gitlab Group Backup Script

Gitlab Group Backup Script is used to backup all project repositories from within a specified Gitlab group.

This script will generate 2 outputs, the first will be the backup directory where the repositories are stored, this directory is also used to pull in changes for the repositories. The second output is a tarfile of the backup directory. Both of these outputs can have their own paths using the scripts flags below.

To use get started using this script you will need the following:

* A Gitlab token with both api_read & read_repository access
* Your group_id from your gitlab group
* Pip modules: requests, gitpython

## Running the script

You can modify the script to inculde your token and group_id if you don't want to provide it as an argument, if you want to use the script as is these are the following arguments:

Argument | Use
---------|---------
-t or --token | The api token from your Gitlab group with api_read & read_repository access.
-g or --group | The group id from your Gitlab group.
-d or --directory | the directory where you wish to store the backups, if not specified the directory will be the scripts working directory
-e or --export | Sets the directory where the tarfile exports, if not specified will be the scripts working directory 
-v or --apiversion | Sets the Gitlab API version to use, v4 is set if not specififed
-r or --remove | Removes the backup directory created by the script

An example of how you would execute this script:
```
python3 gitlab_group_repo_backup.py -t <API_TOKEN> -g <GROUP_ID> -d <BACKUP_DIRECTORY> -e <TARFILE_DIRECTORY> -v <API_VERSION>
```

## Using the BASH script

This was created mainly to load modules before executing the script and is used in a simlar way to the python script, you will also need the python script in the same directory as the bash script:

```
bash gitlab_group_repo_backup.sh <API_TOKEN> <GROUP_ID> <BACKUP_DIRECTORY> (OPTIONAL)
```
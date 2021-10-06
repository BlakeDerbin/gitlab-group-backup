# Gitlab Group Backup Script

Gitlab Group Backup Script is used as a solution to backing up Gitlab repositories in a group with 2FA enabled. Gitlab's API by default will ask for a 2FA code when getting an archive of a repository, it is also limited to 5 requests per minute for Gitlab.com users. This script uses the module gitpython to clone in new repositories and pull in changes for existing repositories. 

This script also support exporting repositories from a Gitlab export, currently the format that works with this is a single tarfile of any gitlab exports you wish to extract the gitlab repositories from. If you want to use this you will need to toggle this on in the config.yaml.

By default the script will generate 2 outputs when backing up a group:
* backup directory ( stores repositories and pulls in changes to them from remote )
* tarfile of the backup directory ( only generated once per day )

Both of these outputs can have their own directories by either specifying them in the config.yaml or when running the script using the user args.

## Requirements
To use get started using this script you will need the following:

* A Gitlab token with both api_read & read_repository access
* Your group_id from your gitlab group
* Pip modules: requests, gitpython

If you have Singularity installed you can also build the python_with_modules.def file for a container with everything needed to use the script.

## Running the script
There a 2 options for running this script, you can either use the arguments below when running the script or modify the config.yaml file to run the script without using arguments.

Argument | Use
---------|---------
-t or --token | The api token from your Gitlab group with api_read & read_repository access.
-g or --group | The group id from your Gitlab group.
-d or --directory | the directory where you wish to store the backups, if not specified the directory will be the scripts working directory
-e or --export | Sets the directory where the tarfile exports, if not specified will be the scripts working directory 
-v or --apiversion | Sets the Gitlab API version to use, v4 is set if not specififed
-r or --remove | Removes the backup directory created by the script
-p or --period | Specifies the amount of days to keep tarfiles backups for (default is 182 days)

An example of how you would execute this script with arguments:
```
python3 gitlab_group_repo_backup.py -t <API_TOKEN> -g <GROUP_ID> -d <BACKUP_DIRECTORY> -e <TARFILE_DIRECTORY> -v <API_VERSION>
```

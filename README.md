# couchdb-backup-s3

## Tripwell use case

## How it works
`couchdb-backup-3` is a program that can be run manually or as crontab to
automatically backup couchdb db files into s3

In Summary
* Check if redis in install and running
* Compresses the couchdb db files in to tar.gz format based on the given path
* It gets the backup rotation number from redis which is in the range (0-7) and the rotation number can be set to any other range.
* Check if the s3 bucket exists if not it creates one based on the given bucket name
* Upload the compressed couchdb db files to s3 in the format `00-Wednesday-couchdb-2016-05-11.tar.gz`

## How to run it

```python
   python couchdb-s3-backup.py couchdb_backup config.json
```

But before you can run it, you need to have the config.json file i.e:
```json
{
    "rotation_max": 7,
    "s3-bucket-name": "couch-backup-bucket",
    "file_path": "/opt/tripwell/data/couchdb",
    "redis": {
      "rotation_key": "rotation_redis_key",
      "host": "localhost",
      "port": 6379,
      "db": 0
    }
}
```

You will also need to install the python required packages, I will suggest to created a python virtualenv
* Install pip if it is not installed
* Install virtualenv if it is not installed i.e `sudo pip install virtualenv`
* Clone this project
* Create the virtualenv `virtualenv path_to_this_project`
* Inside the project `source bin/activate`
* And run pip install -r requirements.txt



# Setup aws credential
Since we are using aws api via python package boto3, you will need to setup the aws credentials and config under the user home directory

* Create credentials file under ~/.aws/credentials
`
[default]
aws_access_key_id = Your-aws-access-key-id
aws_secret_access_key = Your-aws-secret-access-key
`

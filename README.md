# couchdb-backup-s3


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

# couchdb-backup-s3


## How it works
`couchdb-backup-3` is a program that can be run manually or as crontab to
automatically backup couchdb db files into s3


It gets the backup rotation number from redis which is in the range (0-7) and the rotation number can be set to any other range.

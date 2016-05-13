# -*- coding: utf-8 -*-
"""
    couchdb-backup-s3
    ~~~~~

    couchdb-backup-s3 is a simple python code for a couchdb rotational backup to s3

    :copyright: (c) 2016 by Kalilou Diaby.
    :license: Not decided  yet
"""

import sys
import json
import click
import redis
import boto3
import logging
import tarfile
import calendar
import botocore
from datetime import date

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

log = logging.getLogger(u'Couchdb::backup')


class CouchUtilWrapper(object):
    """ Class wrapper for setting the basic properties from the config
        Basic properties:
            :param rotation_max: Maximum backup rotation
            :param bucket_name: AWS s3 bucket name which stores the backups
            :param couchdb_file_path: Location to the couchdb db files
            :param redis_db: Redis db number (default to 0)
            :param redis_port: Redis port number (default to 6379)
            :param redis_host: Redis host address (default to localhost)
            :param redis_key: Redis key used for the rotation

        Basic usage (assuming you have the config file setup and the aws credential and config files)
            >>> python couchdb-backup-s3 couchdb_backup config.json
            >>> python couchdb-s3-backup.py restore_backup 00-Wednesday-couchdb-2016-05-11.tar.gz

        Important note: 00-Wednesday-couchdb-2016-05-11.tar.gz should be taken from the s3
    """

    def __init__(self, config=None):
        config = config or {}
        self.rotation_max = config.get('rotation_max', 7)
        self.bucket_name = config.get('s3-bucket-name', 'couch-backup-bucket')
        self.couchdb_file_path = config.get('file_path', '/var/lib/couchdb')

        redis_config = config.get('redis', {})
        self.redis_db = redis_config.get('db', 0)
        self.redis_port = redis_config.get('port', 6379)
        self.redis_host = redis_config.get('host', 'localhost')
        self.redis_key = redis_config.get('key', 'rotation_num')

        self.redis_cli = redis.StrictRedis(db=self.redis_db,
                                           host=self.redis_host,
                                           port=self.redis_port)

        today = date.today()
        self.date_iso = today.isoformat()
        self.day = calendar.day_name[today.weekday()]

        self.s3_client = boto3.resource('s3')
        self.bucket_config = {'LocationConstraint': 'eu-west-1'}
        self.bucket = self.s3_client.Bucket(self.bucket_name)

        self.couchdb_tarfile = None

    def check_redis_running(self):
        try:
            self.redis_cli.ping()
        except redis.exceptions.ConnectionError:
            log.info('\t-----------------------------------------------------------')
            log.info('\t--- Redis is not running please make sure to fix redis  ---')
            log.info('\t---     1. Install redis: sudo yum install redis        ---')
            log.info('\t---     2. Start Redis                                  ---')
            log.info('\t-----------------------------------------------------------')
            return False
        return True

    def check_bucket_exists(self):
        try:
            self.s3_client.meta.client.head_bucket(Bucket=self.bucket_name)
        except botocore.exceptions.ClientError as e:
            error_code = int(e.response['Error']['Code'])
            return False if error_code == 404 else True

        return True

    def create_bucket(self):
        self.s3_client.create_bucket(Bucket=self.bucket_name,
                                     GrantFullControl='WRITE_ACP',
                                     CreateBucketConfiguration=self.bucket_config)

    def upload_file(self):
        log.info('Uploading {} to s3'.format(self.couchdb_tarfile))
        obj = self.bucket.Object(self.couchdb_tarfile)
        obj.upload_file(self.couchdb_tarfile)

    def download_backup(self, backup_name):
        s3_client = boto3.client('s3')
        log.info('Download {} from s3'.format(backup_name))
        s3_client.download_file(self.bucket_name, backup_name, "{}/couchdb.tar.gz".format(self.couchdb_file_path))

    def negociate_rotation_num(self):
        if not self.redis_cli.exists(self.redis_key):
            self.redis_cli.set(self.redis_key, 0)
            return 0

        rotation_num = self.redis_cli.get(self.redis_key)

        if int(rotation_num) > self.rotation_max:
            self.redis_cli.set(self.redis_key, 0)
            return 0

        return rotation_num

    def compressed_couchdb_files(self):
        log.info('Compressing the files from {}'.format(self.couchdb_file_path))

        rotation_num = self.negociate_rotation_num()
        couchdb_tarfile = '0{}-{}-couchdb-{}.tar.gz'.format(rotation_num, self.day, self.date_iso)
        tar = tarfile.open(couchdb_tarfile, 'w:gz')
        tar.add(self.couchdb_file_path, recursive=True)
        tar.close()

        self.couchdb_tarfile = couchdb_tarfile

    def increment_rotation_num(self):
        self.redis_cli.incr(self.redis_key, amount=1)


@click.group()
def cli():
    pass


@cli.command()
@click.argument('backup_file')
def restore_backup(backup_file):
    couch_wrapper = CouchUtilWrapper()
    couch_wrapper.download_backup(backup_file)


@cli.command()
@click.argument('config')
def couchdb_backup(config):
    log.info('Starting the backup')
    with open(config) as fd:
        config = json.load(fd)

    if not config:
        config = {}

    couch_wrapper = CouchUtilWrapper(config=config)

    if not couch_wrapper.check_redis_running():
        return

    couch_wrapper.compressed_couchdb_files()
    if not couch_wrapper.check_bucket_exists():
        couch_wrapper.create_bucket()

    couch_wrapper.upload_file()
    couch_wrapper.increment_rotation_num()

if __name__ == '__main__':
    cli()

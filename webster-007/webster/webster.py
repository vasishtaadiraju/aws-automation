# -*- coding: utf-8 -*-

"""Webster automates the process of deploying static websites to Amazon Web Services using AWS S3
Key Features
    -Create S3 buckets
    -Manage S3 Buckets
    -Deploy files from local system

"""

import boto3
from botocore.exceptions import ClientError
import click
from pathlib import Path
import mimetypes

session = boto3.Session(profile_name='pythonAutomation')
s3 = session.resource('s3')

@click.group()
def cli():

    """Webster deploys websites to AWS."""
    pass


@cli.command('list-buckets')
def list_buckets():

    """List all S3 Buckets"""
    for bucket in s3.buckets.all():
        print(bucket)
@cli.command('list-bucket-objects')
@click.argument('bucket')
def list_bucket_objects(bucket):
    """List objects of S3 bucket"""
    for obj in s3.Bucket(bucket).objects.all():
        print(obj)

@cli.command('setup-bucket')
@click.argument('bucket')
def setup_bucket(bucket):
    """Create and Configure S3 bucket"""
    s3_bucket = None

    try:

        s3_bucket = s3.create_bucket(Bucket = bucket)

    except ClientError as e:

        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            s3_bucket = s3.Bucket(bucket)
        else:
            raise e

    policy = """
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": "arn:aws:s3:::%s/*"
            }
        ]
    }

    """ % s3_bucket.name
    policy = policy.strip()
    pol = s3_bucket.Policy()

    pol.put(Policy=policy)

    ws = s3_bucket.Website()
    ws.put(WebsiteConfiguration={
        'ErrorDocument' : {
            'Key': 'error.html'
        },
        'IndexDocument' : {
            'Suffix': 'index.html'
        }
    })

    return

def upload_file(s3_bucket, path, key):
    content_type = mimetypes.guess_type(key)[0] or 'text/plain'
    s3_bucket.upload_file(
        path,
        key,
        ExtraArgs={
            'ContentType': 'text/html'
        })

@cli.command('sync')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket')


def sync(pathname, bucket):
    """Sync contents to S3 Bucket"""
    s3_bucket=s3.Bucket(bucket)
    root = Path(pathname).expanduser().resolve()


    def handle_directory(target):
        for p in target.iterdir():
            if p.is_dir():
                handle_directory(p)
            if p.is_file():
                key = p.relative_to(root)
                key = key.as_posix()
                windowskey = '/'.join(key.split(' \ '))
                upload_file(s3_bucket, str(p.as_posix()), str(windowskey))

    handle_directory(root)
if __name__== '__main__':
    cli()

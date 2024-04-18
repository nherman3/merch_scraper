"""Need this
https://aws.amazon.com/blogs/compute/upcoming-changes-to-the-python-sdk-in-aws-lambda/
"""
import json
import time
import boto3
from botocore.vendored import requests


BUCKET = 'scraping-example'
URL = 'https://www.google.com/search?q='

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}


def lambda_handler(event, context):
    query = event['query']
    start = event['start']
    num = event['num']

    q = '+'.join(query.split())
    url = URL + q + f'&start={start}&num={num}&ie=utf-8&oe=utf-8'
    response = requests.get(url, headers=HEADERS)

    s3 = boto3.client('s3')
    timestamp = time.time()
    key = f'{timestamp}.html'

    s3.put_object(Bucket=BUCKET, Key=key, Body=response.text.encode('utf-8'))

    return {
        'statusCode': 200,
        'body': json.dumps('success')
    }

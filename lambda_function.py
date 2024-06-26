"""Need this
https://aws.amazon.com/blogs/compute/upcoming-changes-to-the-python-sdk-in-aws-lambda/
"""
import json
import time
from datetime import datetime
import boto3
from botocore.vendored import requests


BUCKET = 'scraping-example'
URLS = ['https://www.toddland.com/collections/american-dad',
        'https://www.toddland.com/collections/family-guy-x-toddland']

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatable: CronSearchExample/1.0; +https://public-info-example.s3.us-east-2.amazonaws.com/bot.html)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}


def lambda_handler(event, context):
    s3 = boto3.client('s3')
    timestamp = time.time()
    dt_object = datetime.fromtimestamp(timestamp)
    formatted_date = dt_object.strftime('%Y.%m.%d')

    url = event['url']

    if url == "https://www.toddland.com/collections/american-dad":
        key = f'AD - {formatted_date}.html'
    elif url == "https://www.toddland.com/collections/family-guy-x-toddland":
        key = f'FG - {formatted_date}.html'

    response = requests.get(url, headers=HEADERS)
    s3.put_object(Bucket=BUCKET, Key=key, Body=response.text.encode('utf-8'))

    return {
        'statusCode': 200,
        'body': json.dumps('success'),
        'file': key
    }

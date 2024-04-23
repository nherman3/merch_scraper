import json
import boto3
from bs4 import BeautifulSoup

BUCKET = 'scraping-example'
OUTPUT_TABLE = 'extracted-urls'

def process_url(url):
    """clean google urls"""
    try:
        tmp = url.split('url=')[1]
        if tmp.find('&'):
            tmp = tmp.split('&')[0]
        if tmp.find('%'):
            tmp = tmp.split('%')[0]
        if tmp.find('google') >= 0 or tmp[0] == '/':
            return
        return tmp
    except Exception as e:
        print(e, url)

def lambda_handler(event,context):
    key = event['file']
    s3 = boto3.resource('s3')

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(OUTPUT_TABLE)

    # get object from s3 bucket
    obj = s3.Object(BUCKET, key)

    # read contents
    file_content = obj.get()['Body'].read().decode('utf-8')

    soup = BeautifulSoup(file_content, 'html.parser')

    for link in soup.find_all('a'):
        url = process_url(link.get('href'))
        if url:
            table.put_item(Item={'id': url, 'text': link.get_text()})

    return {
        'statusCode': 200,
        'body': json.dumps('success')
    }

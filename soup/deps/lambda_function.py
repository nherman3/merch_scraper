# NSH 2024
import json
import boto3
from bs4 import BeautifulSoup
import re

BUCKET = 'scraping-example'
OUTPUT_TABLE = 'extracted-urls'

def remove_keywords(s, keywords):
    for keyword in keywords:
        # Find the index of the keyword in the string
        index = s.lower().find(keyword.lower())
        # If the keyword is found, slice the string up to the keyword
        if index != -1:
            s = s[:index]
    return s

def lambda_handler(event,context):
    key = event['file']

    if key[0:2] == 'AD':
        product_show = 'American Dad!'
    else:
        product_show = 'Family Guy'
    strip_len = len(product_show)

    s3 = boto3.resource('s3')

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(OUTPUT_TABLE)

    # get object from s3 bucket
    obj = s3.Object(BUCKET, key)

    # read contents
    file_content = obj.get()['Body'].read().decode('utf-8')

    soup = BeautifulSoup(file_content, 'html.parser')

    # Find all product divs within the section
    product_divs = soup.select('section.product-grid div[class^="four columns"]')

    # Iterate over each product div
    for product in product_divs:
        # Get product name
        product_name_full = product.find('h3').text.strip()[strip_len:].strip()
        product_name = remove_keywords(product_name_full,
                                       ["hard enamel pin", "enamel pin", "pin le", "Tee",
                                        "sticker", "Clear Die Cut", "(limited"])
        product_name = re.sub(r'^\s*-\s*', '', product_name).strip()

        # Get product category
        if re.findall('pin', product_name_full, re.IGNORECASE):
            product_type = 'Enamel Pin'
        elif re.findall('tee', product_name_full, re.IGNORECASE):
            product_type = 'T-Shirt'
        elif re.findall('sticker', product_name_full, re.IGNORECASE):
            product_type = 'Sticker'
        else:
            product_type = 'T-Shirt?'
        # Get product price
        product_price = product.find('h4').text.strip()
        # second_index = product_price.find('$', product_price.find('$') + 1)
        second_index = product_price.find('$', product_price.find('$') + 1)
        if second_index != -1:
            product_price = product_price[:second_index]

        # Get Sold Out Status
        if product.find('div'):
            templist = [status.text.strip() for status in product.find_all('div')]
            product_avail = ' - '.join(templist)
        else:
            product_avail = 'Available'
        # <div class="sold-out">Sold Out</div>

        # Get product URL
        product_url = 'https://www.toddland.com' + product.find('a')['href']

        # Get product image URL
        product_image = product.find('img')['src']
        product_image = 'https:' + re.sub('_large', '', product_image)
        product_id = re.sub('_large', '', product_image)[-10:]

        # Check if the item exists
        existing_item = table.get_item(Key={'id': product_id})

        if 'Item' in existing_item:
            # If item exists, update it
            update_response = table.update_item(
                Key={'id': product_id},
                UpdateExpression="set #P = :p, #A = :a",
                ExpressionAttributeNames={
                    '#P': 'Price',
                    '#A': 'Availability'  # Using an expression attribute name for special character handling
                },
                ExpressionAttributeValues={
                    ':p': product_price,
                    ':a': product_avail
                },
                ReturnValues="UPDATED_NEW"
            )
        else:
            # If the item does not exist, add it and send a notification
            try:
                response = table.put_item(
                    Item={
                        'id': product_id,
                        '_Name': product_name,
                        'Category': product_type,
                        'Price': product_price,
                        'Availability': product_avail,
                        'URL': product_url,
                        'Image': product_image,
                        '_Show': product_show
                    },
                    ConditionExpression='attribute_not_exists(id)'
                )
                # Send notification for new item depending on show or item type

                if product_type == 'Enamel Pin':
                    send_notification(f'Toddland {product_show} Inventory Notification',
                                      f'New {product_type}: {product_name} has been posted\n\n{product_url} ')
                elif product_show == 'American Dad!':
                    send_notification(f'Toddland {product_show} Inventory Notification',
                                      f'New {product_type}: {product_name} has been posted\n\n{product_url} ')

            except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
                # This exception means the item already exists
                # Normally this shouldn't occur due to the earlier check
                pass

    return {
        'statusCode': 200,
        'body': json.dumps('success')
    }

def send_notification(subject, message):
    sns = boto3.client('sns')
    sns.publish(
        TopicArn='arn:aws:sns:us-east-2:992382680174:Toddland_Update',
        Message=message,
        Subject=subject
    )

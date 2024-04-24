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
        product_name_full = product.find('h3').text.strip()[13:].strip()
        product_name = remove_keywords(product_name_full,
                                       ["hard enamel pin", "enamel pin", "pin le", "Tee", "sticker", "Clear Die Cut"])
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
        # product_sold_out.append(product_avail)
        # <div class="sold-out">Sold Out</div>

        # Get product URL
        product_url = 'https://www.toddland.com' + product.find('a')['href']

        # Get product image URL
        product_image = product.find('img')['src']
        product_image = 'https:' + re.sub('_large', '', product_image)

        # response = table.put_item(Item={'id': product_name,
        #                      'Category': product_type,
        #                      'Price': product_price,
        #                      'SoldOut?': product_avail,
        #                      'URL': product_url,
        #                      'Image': product_image
        #                      })

        new_items_added = False
        try:
            response = table.put_item(
                Item={
                    'id': product_name,
                    'Category': product_type,
                    'Price': product_price,
                    'SoldOut?': product_avail,
                    'URL': product_url,
                    'Image': product_image
                },
                ConditionExpression='attribute_not_exists(id)'
            )
            new_items_added = True
        except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            # This exception means the item already exists and wasn't added
            print(f"{product_name_full} already exists and was not added.")

        if new_items_added:
            send_notification(f'{product_type} {product_name} is now {product_avail}')

    return {
        'statusCode': 200,
        'body': json.dumps('success')
    }

def send_notification(message):
    sns = boto3.client('sns')
    sns.publish(
        TopicArn='arn:aws:sns:us-east-2:992382680174:Toddland_Update',
        Message=message,
        Subject='Toddland American Dad Inventory Update Notification'
    )

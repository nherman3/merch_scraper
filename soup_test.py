import json
from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
# pd.options.display.max_colwidth=200

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) \
AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'}

URL = 'https://www.toddland.com/collections/american-dad'
test_url = 'https://www.google.com/search?q=american+dad+episodes&oq=american+dad+episodes&gs_lcrp=EgZjaHJvbWUyDAgAEEUYORixAxiABDIGCAEQRRg8MgcIAhAAGIAEMgcIAxAAGIAEMgcIBBAAGIAEMgcIBRAAGIAEMgcIBhAAGIAEMgcIBxAAGIAEqAIAsAIA&sourceid=chrome&ie=UTF-8'

def remove_keywords(strings, keywords):
    # Iterate over each string in the list
    for i, s in enumerate(strings):
        # Check each keyword
        for keyword in keywords:
            # Find the index of the keyword in the string
            index = s.lower().find(keyword.lower())
            # If the keyword is found, slice the string up to the keyword and stop looking for more keywords
            if index != -1:
                strings[i] = s[:index]
                break
    return strings

def gogo(insert_url):
    response = requests.get(insert_url, headers=headers)
    with open('test.html', 'w') as f:
        f.write(response.text)


def go(fn):
    with open(fn, 'r') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    # out = []
    # for link in soup.find_all('a'):
    #     url = link.get('href')
    #     if url:
    #         out.append({'url':url,
    #                     'text': link.get_text()})
    #
    # print(json.dumps(out, indent=4))

    # Find all product divs within the section
    product_divs = soup.select('section.product-grid div[class^="four columns"]')

    # Initialize lists to store data
    product_names = []
    product_types = []
    product_prices = []
    product_sold_out = []
    product_urls = []
    product_images = []

    # Iterate over each product div
    for product in product_divs:
        # Get product name
        product_name = product.find('h3').text.strip()[13:].strip()

        product_names.append(re.sub(r'^\s*-\s*', '', product_name))

        # Get product category
        if re.findall('pin', product_name, re.IGNORECASE):
            product_types.append('Enamel Pin')
        elif re.findall('tee', product_name, re.IGNORECASE):
            product_types.append('T-Shirt')
        elif re.findall('sticker', product_name, re.IGNORECASE):
            product_types.append('Sticker')
        else:
            product_types.append('T-Shirt?')

        # Get product price
        product_price = product.find('h4').text.strip()
        product_prices.append(product_price)

        # Get product URL
        product_url = product.find('a')['href']
        product_urls.append('https://www.toddland.com' + product_url)

        # Get product image URL
        product_image = product.find('img')['src']
        product_images.append('https:' + re.sub('_large', '', product_image))

        # Get Sold Out Status
        if product.find('div'):
            product_avail = [status.text.strip() for status in product.find_all('div')]
        else:
            product_avail = 'Available'
        product_sold_out.append(product_avail)
        # <div class="sold-out">Sold Out</div>

    product_names = remove_keywords(product_names,
                                    ["hard enamel pin", "enamel pin", "pin le", "Tee", "sticker", "Clear Die Cut"])

    # Create DataFrame
    df = pd.DataFrame({
        'Name': product_names,
        'Category': product_types,
        'Price': product_prices,
        'SoldOut?': product_sold_out,
        'URL': product_urls,
        'Image': product_images
    })
    df.sort_values(by=['Category','Name'],inplace=True)
    df.to_csv('test.csv', index=False)

    # Display DataFrame
    # print(df.sort_values('Name'))


if __name__ == '__main__':
    gogo(URL)
    go('test.html')
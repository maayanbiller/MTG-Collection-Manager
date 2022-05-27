import urllib.request
import urllib.parse
import re

card_name = input('enter a card name: ')

webUrl = 'https://scryfall.com/search?q=doomskar'
# webUrl = 'https://scryfall.com/search?q=!%22{}%22'.format(card_name)
# webUrl = 'https://scryfall.com/search?q=!%22sakashima%20of%20a%20thousand%20faces%22'
# webUrl = 'https://scryfall.com/card/cmr/89/sakashima-of-a-thousand-faces'
HTML = urllib.request.urlopen(webUrl).read()
print(HTML)

# img_url = re.search(r"img.*?src=\"(?P<img_url>[^\"]*)\"", HTML.decode("utf-8"), re.DOTALL)['img_url']
# # price = re.search(r"<a title=\"Nonfoil: \$(?P<price>[^,]*)[^>]*>", HTML.decode("utf-8"), re.DOTALL)['price']
# # prices = re.search(r"<a title=\"Nonfoil: \$(?P<nonfoil>[^,]*), Foil: \$(?P<foil>[^\"]*)\"[^>]*>", HTML.decode("utf-8"), re.DOTALL)
# price = re.search(r"<span class=\"price currency-usd\">\$(?P<price>[^<]*)</span>", HTML.decode("utf-8"), re.DOTALL)['price']
# print(f'img url : {img_url}\nnonfoil price : {price}')

# print(HTML)
# content = re.search(r"<div id=\"mw-content-text.*id=\"catlinks", HTML.decode("utf-8"), re.DOTALL)
# print(content)
import sqlite3
import urllib.request
import urllib.parse
import re


class Card():
    def __init__(self, name, edition, card_url, img_url, price, color_identity):
        self.name = name
        self.edition = edition
        self.img_url = img_url
        self.card_url = card_url
        self.price = price
        self.color_identity = color_identity

conn = sqlite3.connect('cards database.db')

c = conn.cursor()

# c.execute("""CREATE TABLE cards (
#             name text,
#             edition text,
#             card_url text,
#             img_url text,
#             price real,
#             color_identity text
#             )""")


def insert_card(card):
    with conn:
        c.execute("INSERT INTO cards VALUES (:name, :edition, :card_url, :img_url, :price, :color_identity)",
                  {'name': card.name, 'edition': card.edition, 'card_url':card.card_url, 'img_url': card.img_url, 'price': card.price, 'color_identity': card.color_identity})


def remove_card_by_name(card_name):
    with conn:
        c.execute("DELETE from cards WHERE name = :name", {'name': card_name})


def get_cards_by_price(min_price, max_price):
    with conn:
        c.execute("SELECT * FROM cards WHERE price <= :max_price AND :min_price <= price", {'min_price': min_price, 'max_price': max_price})
        return c.fetchall()


def get_cards_by_edition(edition):
    with conn:
        c.execute("SELECT * FROM cards WHERE edition=:edition", {'edition': edition})
        return c.fetchall()


def get_card_names_in_database_by_partial_name(name):
    with conn:
        c.execute("SELECT name FROM cards WHERE name=:name", {'name': name})
        return c.fetchall()


def search_card_urls_in_database(name):
    with conn:
        c.execute("SELECT card_url FROM cards WHERE name LIKE :name", {'name': '%{}%'.format(name)})
        return c.fetchall()


def get_color_identity_from_HTML(HTML):
    card_colors = {'"one white mana">{W}': False, '"one blue mana">{U}': False, '"one black mana">{B}': False, '"one red mana">{R}': False, '"one green mana">{G}': False}
    for color in card_colors:
        if color in HTML:
            card_colors[color] = True
    color_identity = ''
    for color in card_colors:
        if card_colors[color]:
            color_identity += color[-2]
    if color_identity == '':
        color_identity = 'C'
    if len(color_identity) > 1:
        color_identity = f'M{color_identity}'
    return color_identity


def search_in_browser_by_name(name):
    webUrl = 'https://scryfall.com/search?q={}'.format(name)
    try:
        HTML = urllib.request.urlopen(webUrl).read()
        s = re.search(r"<a title=\".*?\".*?href=\"(?P<url>https://scryfall.com/card/(?P<edition>.*?)/(?P<collector_num>.*?)/(?P<card_name>.*?))\"/*?>en</a>", HTML.decode("utf-8"), re.DOTALL)
        if s is not None:
            # if the search sends you directly to the only card that in this search
            results = [(s['url'], s['edition'], s['collector_num'], s['card_name'])]
        else:
            results = re.findall(r"<a class=\"card-grid-item-card\" href=\"(?P<url>https://scryfall.com/card/(?P<edition>[^/]*)/(?P<collector_num>[^/]*)/(?P<card_name>[^\"]*))\">", HTML.decode("utf-8"), re.DOTALL)
        for card_details in results:
            url, edition, collector_num, name = card_details
            try:
                HTML2 = urllib.request.urlopen(url).read()
                img_url = re.search(r"img.*?src=\"(?P<img_url>[^\"]*)\"", HTML.decode("utf-8"), re.DOTALL)['img_url']
                prices = re.search(r"""href=\"/card/{}/{}/{}\".*?<a title=\"Nonfoil: \$(?P<nonfoil>.*?)(, Foil: \$(?P<foil>[^\"]*))?\" class=\"currency-usd\"[^<]*</a>"""
                                   .format(edition, collector_num, name),HTML2.decode("utf-8"), re.DOTALL)
                color_identity = get_color_identity_from_HTML(HTML2.decode("utf-8"))
                print(name, edition, url, img_url, prices['nonfoil'], color_identity)
                card = Card(name, edition, url, img_url, prices['nonfoil'], color_identity)
                insert_card(card)
                print('    card added to database successfully!')
            except:
                print('an error occurred while loading the card')
    except:
        print('invalid card name')


def find_cards_by_partial_name(name):
    # find all cards that contain the partial name in the database and in the browser
    card_urls_in_database = search_card_urls_in_database(name)
    print(card_urls_in_database)
    webUrl = 'https://scryfall.com/search?q={}'.format(name)
    try:
        HTML = urllib.request.urlopen(webUrl).read()
        results = re.findall(r"<a class=\"card-grid-item-card\" href=\"(?P<url>https://scryfall.com/card/(?P<edition>[^/]*)/(?P<collector_num>[^/]*)/(?P<card_name>[^\"]*))\">", HTML.decode("utf-8"), re.DOTALL)
        if len(results) == 0:
            # if the search sends you directly to the only card that in this search
            s = re.search(r"<a title=\".*?\".*?href=\"(?P<url>https://scryfall.com/card/(?P<edition>.*?)/(?P<collector_num>.*?)/(?P<card_name>.*?))\"/*?>en</a>",
                HTML.decode("utf-8"), re.DOTALL)
            results = [(s['url'], s['edition'], s['collector_num'], s['card_name'])]

        for card_details in results:
            url, edition, collector_num, name = card_details
            if (url,) in card_urls_in_database:
                with conn:
                    c.execute("SELECT edition,img_url,price FROM cards WHERE name = :name", {'name': name})
                    edition, img_url, price = c.fetchall()[0]
                    print(name, edition, url, img_url, price)
                    print('{} already in database'.format(name))
                    continue
            try:
                HTML2 = urllib.request.urlopen(url).read()
                img_url = re.search(r"img.*?src=\"(?P<img_url>[^\"]*)\"", HTML2.decode("utf-8"), re.DOTALL)['img_url']
                prices = re.search(r"""href=\"/card/{}/{}/{}\".*?<a title=\"Nonfoil: \$(?P<nonfoil>.*?)(, Foil: \$(?P<foil>[^\"]*))?\" class=\"currency-usd\"[^<]*</a>"""
                                   .format(edition, collector_num, name),HTML2.decode("utf-8"), re.DOTALL)
                color_identity = get_color_identity_from_HTML(HTML2.decode("utf-8"))
                print(name, edition, url, img_url, prices['nonfoil'], color_identity)
                card = Card(name, edition, url, img_url, prices['nonfoil'], color_identity)
                insert_card(card)
                print('    card added to database successfully!')
            except:
                print('an error occurred while loading the card')
    except:
        print('invalid card name')



def get_all_cards():
    with conn:
        c.execute("SELECT * FROM cards")
        return c.fetchall()


# card_name = card_name = input('insert a card name: ')
# webUrl = 'https://scryfall.com/search?q=!%22{}%22'.format(card_name)
# try:
#     HTML = urllib.request.urlopen(webUrl).read()
#     img_url = re.search(r"img.*?src=\"(?P<img_url>[^\"]*)\"", HTML.decode("utf-8"), re.DOTALL)['img_url']
#     prices = re.search(r"<a title=\"Nonfoil: \$(?P<nonfoil_price>[^,]*), Foil: \$(?P<foil_price>[^\"]*)\" class=\"currency-usd\"[^<]*</a>", HTML.decode("utf-8"), re.DOTALL)
#     card = Card(card_name, None, img_url, prices['nonfoil_price'])
#     print(card_name, None, img_url, prices['nonfoil_price'])
#     # insert_card(card)
# except:
#     print('invalid card name')
# price = re.search(r"<span class=\"price currency-usd\">\$(?P<price>[^<]*)</span>", HTML.decode("utf-8"), re.DOTALL)['price']


find_cards_by_partial_name('pixie')
# print(get_all_cards())
# find_cards_by_partial_name('sakashima')
# print(get_cards_by_price(5, 10000))

conn.close()

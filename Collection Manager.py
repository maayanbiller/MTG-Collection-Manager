import sqlite3
import urllib.request
import urllib.parse
import re
from flask import Flask, render_template


class Card():
    def __init__(self, name, edition, collector_num, card_url, img_url, price, color_identity):
        self.name = name
        self.edition = edition
        self.collector_num = collector_num
        self.img_url = img_url
        self.card_url = card_url
        self.price = price
        self.color_identity = color_identity


app = Flask(__name__)
app.config['SECRET_KEY'] = '7ad953930b59971b4fded5852a023868'

conn = sqlite3.connect('cards database.db')

c = conn.cursor()

# c.execute("""CREATE TABLE cards (
#             name text,
#             edition text,
#             collector_num text,
#             card_url text,
#             img_url text,
#             price real,
#             color_identity text,
#             CONSTRAINT card PRIMARY KEY (collector_num, edition)
#             )""")


def insert_card(card):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("INSERT INTO cards VALUES (:name, :edition, :collector_num, :card_url, :img_url, :price, :color_identity)",
                  {'name': card.name, 'edition': card.edition, 'collector_num': card.collector_num,
                   'card_url':card.card_url, 'img_url': card.img_url, 'price': card.price,'color_identity': card.color_identity})


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


def get_cards_details_in_db_by_name(name):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM cards WHERE name LIKE :name ORDER by price desc", {'name': '%{}%'.format(name)})
        return c.fetchall()


def get_cards_in_db_by_name(name):
    cards = []
    for card in get_cards_details_in_db_by_name(name):
        cards.append(Card(card[0], card[1], card[2], card[3], card[4], card[5], card[6]))
    return cards


def search_card_urls_in_database(name):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
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


def add_cards_by_partial_name(name):
    # find all cards that contain the partial name in the database and in the browser
    card_urls_in_database = search_card_urls_in_database(name)
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
                with sqlite3.connect('cards database.db') as conn:
                    c = conn.cursor()
                    c.execute("SELECT edition,img_url,price FROM cards WHERE name = :name", {'name': name})
                    edition, img_url, price = c.fetchall()[0]
                    print(name, edition, url, img_url, price)
                    print('{} already in database'.format(name))
                    continue
            try:
                HTML2 = urllib.request.urlopen(url).read()
                img_url = re.search(r"img.*?src=\"(?P<img_url>[^\"]*)\"", HTML2.decode("utf-8"), re.DOTALL)['img_url']
                img_url = img_url.replace("large", "normal")
                prices = re.search(r"""href=\"/card/{}/{}/{}\".*?<a title=\"Nonfoil: \$(?P<nonfoil>.*?)(, Foil: \$(?P<foil>[^\"]*))?\" class=\"currency-usd\"[^<]*</a>"""
                                   .format(edition, collector_num, name),HTML2.decode("utf-8"), re.DOTALL)
                color_identity = get_color_identity_from_HTML(HTML2.decode("utf-8"))
                print(name, edition, url, img_url, prices['nonfoil'], color_identity)
                card = Card(name, edition, collector_num, url, img_url, prices['nonfoil'], color_identity)
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



# @app.route('/')
@app.route('/search/<keyword>')
def display_cards(keyword):
    add_cards_by_partial_name(keyword)
    cards = get_cards_in_db_by_name(keyword)
    return render_template('home.html', cards=cards)



app.run(debug=True)


# add_cards_by_partial_name('apex')
# display_cards('apex')
# get_card_names_in_database_by_partial_name()

conn.close()

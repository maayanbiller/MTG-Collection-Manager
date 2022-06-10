import sqlite3
import urllib.request
import urllib.parse
import re
from flask import Flask, render_template, request


class Card():
    def __init__(self, name, type, oracle_text, edition, collector_num, card_url, img_url, price, color_identity, mana_cost, mana_value, url_name):
        self.name = name
        self.type = type
        self.oracle_text = oracle_text
        self.edition = edition
        self.collector_num = collector_num
        self.card_url = card_url
        self.img_url = img_url
        self.price = price
        self.color_identity = color_identity
        self.mana_cost = mana_cost
        self.mana_value = mana_value
        self.url_name = url_name


app = Flask(__name__)
app.config['SECRET_KEY'] = '7ad953930b59971b4fded5852a023868'

conn = sqlite3.connect('cards database.db')

c = conn.cursor()

# c.execute("""CREATE TABLE cards (
#             name text,
#             type text,
#             oracle_text text,
#             edition text,
#             collector_num text,
#             card_url text,
#             img_url text,
#             price real,
#             color_identity text,
#             mana_cost text,
#             mana_value int,
#             url_name text,
#             CONSTRAINT card PRIMARY KEY (collector_num, edition)
#             )""")


# c.execute("""CREATE TABLE collection (
#             edition text,
#             collector_num text,
#             place text,
#             CONSTRAINT card PRIMARY KEY (collector_num, edition)
#             )""")


def decode_card_name(name):
    name = name.replace('&#39;', "'")
    name = name.replace('&#x27;', "'")
    name = name.replace('&amp;', '&')
    name = name.replace('&#x3A;', ':')
    name = name.replace('&#x3F;', '?')
    name = name.replace('&#x2D;', '-')
    name = name.replace('&quot;', '"')
    name = name.replace('&#x2B;', '+')
    return name



def insert_card(card):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("INSERT INTO cards VALUES (:name, :type, :oracle_text, :edition, :collector_num, :card_url, :img_url,"
                  ":price, :color_identity, :mana_cost, :mana_value, :url_name)",
                  {'name': card.name, 'type':card.type, 'oracle_text':card.oracle_text,  'edition': card.edition,
                   'collector_num': card.collector_num, 'card_url':card.card_url, 'img_url': card.img_url,
                   'price': card.price,'color_identity': card.color_identity, 'mana_cost': card.mana_cost,
                   'mana_value': card.mana_value, 'url_name': card.url_name})


def remove_card_by_primary_key(collector_num, edition):
    with conn:
        c.execute("DELETE from cards WHERE collector_num = :collector_num AND edition = :edition",
                  {'collector_num': collector_num, 'edition': edition})


def get_cards_by_price(min_price, max_price):
    with conn:
        c.execute("SELECT * FROM cards WHERE price <= :max_price AND :min_price <= price", {'min_price': min_price, 'max_price': max_price})
        return c.fetchall()


def get_cards_by_edition(edition):
    with conn:
        c.execute("SELECT * FROM cards WHERE edition=:edition", {'edition': edition})
        return c.fetchall()


def get_cards_details_in_db_by_name(name, is_exact_match=False):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        if is_exact_match:
            c.execute("SELECT * FROM cards WHERE name = :name ORDER by price desc", {'name': name})
        else:
            c.execute("SELECT * FROM cards WHERE name LIKE :name ORDER by price desc", {'name': '%{}%'.format(name)})
        return c.fetchall()


def get_card_in_db_by_primary_key(collector_num, edition):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM cards WHERE collector_num = :collector_num AND edition = :edition",
                  {'collector_num': collector_num, 'edition': edition})
        card = c.fetchone()
        if card is None:
            return None
        return Card(card[0], card[1], card[2], card[3], card[4], card[5], card[6], card[7], card[8], card[9], card[10], card[11])


def get_cards_in_db_by_name(name, get_duplicates=False, is_exact_match=False):
    cards = []
    for card in get_cards_details_in_db_by_name(name, is_exact_match=is_exact_match):
        if not get_duplicates:
            # check if another card with the same name is already in the list
            if any(c.name == card[0] for c in cards):
                continue
        cards.append(Card(card[0], card[1], card[2], card[3], card[4], card[5], card[6], card[7], card[8], card[9], card[10], card[11]))
    return cards


def get_card_in_db_by_url_name(url_name):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM cards WHERE url_name = :url_name", {'url_name': url_name})
        card = c.fetchone()
        if card is None:
            return None
        return Card(card[0], card[1], card[2], card[3], card[4], card[5], card[6], card[7], card[8], card[9], card[10], card[11])


def search_card_urls_in_database(name):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT card_url FROM cards WHERE name LIKE :name", {'name': '%{}%'.format(name)})
        return c.fetchall()


def get_color_identity_from_HTML(HTML):
    # TODO: fix hybrid mana
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


def add_card_from_details(url, edition, collector_num, card_name, is_editions_check=False):
    card = get_card_in_db_by_primary_key(collector_num, edition)
    if card:
        print(card_name, edition)
        print('{} already in database'.format(card_name))
        return False  # card isn't added to database
    try:
        HTML2 = urllib.request.urlopen(url).read()
        name_fixed = re.search(r"<span class=\"card-text-card-name\">\n *(?P<name>.*?)\n", HTML2.decode("utf-8"), re.DOTALL)['name']
        name_fixed = decode_card_name(name_fixed)
        url_name = convert_name_to_url_name(name_fixed)
        card_type = re.search(
            r"<p class=\"card-text-type-line\".*?>\n *(?P<type>[a-zA-Z ]*) ?.*? ?(?P<subtype>[a-z&A-Z ,]*)?\n</p>",
            HTML2.decode("utf-8"), re.DOTALL)
        type = f'{card_type["type"]} - {card_type["subtype"]}' if card_type["subtype"] else card_type["type"]
        card_text = re.search(r"<div class=\"card-text-oracle\">\n *(?P<text>.*?)\n *</div>", HTML2.decode("utf-8"), re.DOTALL)['text']
        text = card_text.replace('<p>', ' ').replace('</p>', '').replace('\n\n', '\n')
        img_url = re.search(r"img.*?src=\"(?P<img_url>[^\"]*)\"", HTML2.decode("utf-8"), re.DOTALL)['img_url']
        img_url = img_url.replace("large", "normal")
        # prices = re.search(r"href=\"/card/{}/{}/{}\".*?<a title=\"(Nonfoil: \$(?P<nonfoil>.*?))?(, Foil: \$(?P<foil>[^\"]*))?\" class=\"currency-usd\"[^<]*</a>".format(edition, collector_num, card_name), HTML2.decode("utf-8"), re.DOTALL)
        nonfoil_price = re.search(r"<span class=\"price currency-usd\">\$(?P<price>.*?)</span>", HTML2.decode("utf-8"),
                                  re.DOTALL)
        foil_price = re.search(r"<span class=\"price currency-usd\">✶\xa0\$(?P<price>.*?)</span>",
                               HTML2.decode("utf-8"), re.DOTALL)
        price = None
        if nonfoil_price:
            price = nonfoil_price['price']
        elif foil_price:
            price = foil_price['price']
        else:
            if not is_editions_check:
                for card_details in re.findall(r"<a data-component=\"card-tooltip\".*?href=\"(?P<url>/card/(?P<edition>.*?)/(?P<collector_num>.*?)/(?P<name>.*?))\".*?</a>",
                                               HTML2.decode("utf-8"), re.DOTALL):
                    url, edition, collector_num, card_name = card_details
                    url = f'https://scryfall.com/{url}'
                    if card_name.find('/') != -1:
                        continue
                    if add_card_from_details(url, edition, collector_num, card_name, is_editions_check=True):
                        return True
            print(name_fixed, edition)
            print('    upload failed, card has no price!')
            return False  # card isn't added to database
        color_identity = get_color_identity_from_HTML(HTML2.decode("utf-8"))
        mana_cost_html = re.search(r"<span class=\"card-text-mana-cost\">.*?</span>", HTML2.decode("utf-8"), re.DOTALL)
        mana_value = 0
        mana_cost = ''
        if mana_cost_html:
            mana_cost_list = re.findall(r"<abbr.*?{(?P<mana>.*?)}.*?</abbr>", mana_cost_html[0], re.DOTALL)
            for i, m in enumerate(mana_cost_list):
                if m.isdecimal():
                    mana_value += int(m)
                else:
                    mana_value += 1
                mana_cost += f'{m}' if i == 0 else f' {m}'
        print(name_fixed, edition, url, img_url, price, color_identity, mana_value)
        card = Card(name_fixed, type, text, edition, collector_num, url, img_url, price, color_identity, mana_cost,
                    mana_value, url_name)
        insert_card(card)
        print('    card added to database successfully!')
        return True  # card added to database
    except:
        print('an error occurred while loading the card')


def add_all_versions_of_card(card_url):
    is_added = False
    HTML = urllib.request.urlopen(card_url).read()
    # find "next 60" button if exists
    for card_details in re.findall(
            r"<a data-component=\"card-tooltip\".*?href=\"(?P<url>/card/(?P<edition>.*?)/(?P<collector_num>.*?)/(?P<name>.*?))\".*?</a>",
            HTML.decode("utf-8"), re.DOTALL):
        url, edition, collector_num, card_name = card_details
        url = f'https://scryfall.com/{url}'
        if card_name.find('/') != -1:
            continue
        if add_card_from_details(url, edition, collector_num, card_name):
            is_added = True
    return is_added


def add_cards_by_partial_name(name):
    # find all cards that contain the partial name in the database and in the browser
    # card_urls_in_database = search_card_urls_in_database(name)
    name = name.replace(' ', '-').replace("'", "")
    is_db_changed = False
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
            url, edition, collector_num, card_name = card_details
            is_db_changed = add_card_from_details(url, edition, collector_num, card_name) or is_db_changed
    except:
        print('invalid card name')
    return is_db_changed


def get_all_cards():
    with conn:
        c.execute("SELECT * FROM cards")
        return c.fetchall()


def convert_name_to_url_name(name):
    url_name = ''
    for i, ch in enumerate(name):
        if ch.isalpha():
            url_name += ch.lower()
        elif len(url_name) > 0:
            if ch == "'":
                continue
            if url_name[-1] != '-':
                url_name += '-'
    return url_name


@app.route('/')
@app.route('/home')
def index():
    return render_template('home.html')


@app.route('/search')
def search_results():
    keyword = request.args.get('name')
    updated = request.args.get('updated', default='false')
    # add_cards_by_partial_name(keyword)
    cards = get_cards_in_db_by_name(keyword)
    return render_template('search_res.html', cards=cards, keyword=keyword, updated=updated)


@app.route('/update_db_with_search_res/<keyword>')
def update_db_with_search_res(keyword):
    # keyword = request.args.get('name')
    is_db_changed = add_cards_by_partial_name(keyword)
    return 'changed' if is_db_changed else 'not changed'


@app.route('/card/all-versions/<url_name>')
def card_all_versions(url_name):
    updated = request.args.get('updated', default='false')
    card_name = get_card_in_db_by_url_name(url_name).name
    cards = get_cards_in_db_by_name(card_name, is_exact_match=True, get_duplicates=True)
    return render_template('card_all_versions.html', cards=cards, card_name=card_name, card_url_name=url_name, updated=updated)


@app.route('/update_db_with_card_versions/<url_name>')
def update_db_with_card_versions(url_name):
    card_name = get_card_in_db_by_url_name(url_name).name
    card = get_cards_in_db_by_name(card_name, is_exact_match=True)[0]
    is_db_changed = add_all_versions_of_card(card.card_url)
    return 'changed' if is_db_changed else 'not changed'


@app.route('/card/<collector_num>/<edition>')
def card_page(collector_num, edition):
    card = get_card_in_db_by_primary_key(collector_num, edition)
    text_list = [card.oracle_text]
    for t in re.findall("(<abbr.*?>{(?P<symbol>.*?)}</abbr>)", card.oracle_text):
        idx = text_list[-1].find(t[0])
        last_text_pile = text_list[-1]
        text_list[-1] = last_text_pile[:idx]
        text_list.append(f"/{t[1].replace('/', 'or')}/")
        text_list.append(last_text_pile[idx+len(t[0]):].replace('<i>', '').replace('</i>', ''))
    print(text_list)
    # re.findall("<abbr.*?>{(?P<symbol>.*?)}</abbr>", card.oracle_text)
    return render_template('card.html', card=card, text_list=text_list)


app.run(debug=True)


# add_cards_by_partial_name('apex')
# display_cards('apex')
# get_card_names_in_database_by_partial_name()

conn.close()

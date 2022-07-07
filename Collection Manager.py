import random
import sqlite3
import urllib.request
import urllib.parse
import re
from flask import Flask, render_template, request


class Card:
    def __init__(self, name, type, oracle_text, edition, collector_num, card_url, img_url, nonfoil_price, foil_price, color_identity, mana_cost, mana_value, url_name):
        self.name = name
        self.type = type
        self.oracle_text = oracle_text
        self.edition = edition
        self.collector_num = collector_num
        self.card_url = card_url
        self.img_url = img_url
        self.nonfoil_price = nonfoil_price
        self.foil_price = foil_price
        self.color_identity = color_identity
        self.mana_cost = mana_cost
        self.mana_value = mana_value
        self.url_name = url_name

        self.text_list = [self.oracle_text]


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
#             nonfoil_price real,
#             foil_price real,
#             color_identity text,
#             mana_cost text,
#             mana_value int,
#             url_name text,
#             CONSTRAINT card PRIMARY KEY (collector_num, edition)
#             )""")


# c.execute("""CREATE TABLE cards_collection (
#             ID INTEGER PRIMARY KEY AUTOINCREMENT,
#             edition text,
#             collector_num text,
#             box text,
#             is_foil boolean,
#             is_commander boolean
#             )""")


# c.execute("""CREATE TABLE boxes (
#             box_id INTEGER PRIMARY KEY AUTOINCREMENT,
#             box_name text,
#             type text,
#             description text
#             )""")


# c.execute("""CREATE TABLE decks_basic_lands (
#             name text,
#             deck_name text,
#             count int,
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
                  ":nonfoil_price, :foil_price, :color_identity, :mana_cost, :mana_value, :url_name)",
                  {'name': card.name, 'type': card.type, 'oracle_text': card.oracle_text,  'edition': card.edition,
                   'collector_num': card.collector_num, 'card_url': card.card_url, 'img_url': card.img_url,
                   'nonfoil_price': card.nonfoil_price, 'foil_price': card.foil_price, 'color_identity': card.color_identity,
                   'mana_cost': card.mana_cost, 'mana_value': card.mana_value, 'url_name': card.url_name})


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
            c.execute("SELECT * FROM cards WHERE name = :name ORDER by nonfoil_price desc", {'name': name})
        else:
            c.execute("SELECT * FROM cards WHERE name LIKE :name ORDER by nonfoil_price desc", {'name': '%{}%'.format(name)})
        return c.fetchall()


def get_card_in_db_by_primary_key(collector_num, edition):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM cards WHERE collector_num = :collector_num AND edition = :edition",
                  {'collector_num': collector_num, 'edition': edition})
        card = c.fetchone()
        if card is None:
            return None
        return Card(card[0], card[1], card[2], card[3], card[4], card[5], card[6], card[7], card[8], card[9], card[10], card[11], card[12])


def get_cards_in_db_by_name(name, get_duplicates=False, is_exact_match=False, get_cards_back=False):
    cards = []
    for card in get_cards_details_in_db_by_name(name, is_exact_match=is_exact_match):
        if not get_cards_back and card[4][0] == 'B':  # check if the card is the back of double faced card
            continue
        if not get_duplicates:
            # check if another card with the same name is already in the list
            if any(c.name == card[0] for c in cards):
                continue
        cards.append(Card(card[0], card[1], card[2], card[3], card[4], card[5], card[6], card[7], card[8], card[9], card[10], card[11], card[12]))
    return cards


def get_card_in_db_by_url_name(url_name):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM cards WHERE url_name = :url_name", {'url_name': url_name})
        card = c.fetchone()
        if card is None:
            return None
        return Card(card[0], card[1], card[2], card[3], card[4], card[5], card[6], card[7], card[8], card[9], card[10], card[11], card[12])


def search_card_urls_in_database(name):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT card_url FROM cards WHERE name LIKE :name", {'name': '%{}%'.format(name)})
        return c.fetchall()


def get_color_identity_from_HTML(HTML):
    card_colors = {'W': False, 'U': False, 'B': False, 'R': False, 'G': False}
    for html_part in re.findall(r"<span class=\"card-text-mana-cost\">.*?</span>", HTML, re.DOTALL) + \
            re.findall(r"<div class=\"card-text-box\".*?</div                               >", HTML, re.DOTALL): # find all mana costs and text boxes
        for mana in re.findall(r"{(?P<mana>.*?)}", html_part, re.DOTALL):
            for color in card_colors:
                if color in mana:
                    card_colors[color] = True
    for color_indicator in re.findall(r"<abbr class=\"color-indicator color-indicator-(?P<colors>.*?)\".*?</abbr>", HTML, re.DOTALL):
        for color in card_colors:
            if color in color_indicator:
                card_colors[color] = True

    color_identity = ''
    for color in card_colors:
        if card_colors[color]:
            color_identity += color
    if color_identity == '':
        color_identity = 'C'
    if len(color_identity) > 1:
        color_identity = f'M{color_identity}'
    return color_identity


def get_mana_val_and_cost_from_mana_cost_html(mana_cost_html):
    mana_value = 0
    mana_cost = ''
    if mana_cost_html:
        mana_cost_list = re.findall(r"<abbr.*?{(?P<mana>.*?)}.*?</abbr>", mana_cost_html, re.DOTALL)
        for i, m in enumerate(mana_cost_list):
            if m.isdecimal():
                mana_value += int(m)
            else:
                mana_value += 1
            mana_cost += f'{m}' if i == 0 else f' {m}'
    return mana_value, mana_cost


def add_card_from_details(url, edition, collector_num, card_name, is_editions_check=False, is_dfc=False):
    card = get_card_in_db_by_primary_key(f'F{collector_num}', edition)
    if card:
        print(card.name, edition)
        print('{} already in database'.format(card_name))
        return False  # card isn't added to database
    try:
        HTML = urllib.request.urlopen(url).read()
        nonfoil_price = re.search(r"<span class=\"price currency-usd\">\$(?P<price>.*?)</span>", HTML.decode("utf-8"),
                                  re.DOTALL)
        foil_price = re.search(r"<span class=\"price currency-usd\">✶\xa0\$(?P<price>.*?)</span>",
                               HTML.decode("utf-8"), re.DOTALL)
        if nonfoil_price:
            nonfoil_price = nonfoil_price['price']
        else:
            nonfoil_price = '-1'
        if foil_price:
            foil_price = foil_price['price']
        else:
            foil_price = '-1'
        if nonfoil_price == '-1' and foil_price == '-1':
            if not is_editions_check:
                for card_details in re.findall(r"<a data-component=\"card-tooltip\".*?href=\"(?P<url>/card/(?P<edition>.*?)/(?P<collector_num>.*?)/(?P<name>.*?))\".*?</a>",
                                               HTML.decode("utf-8"), re.DOTALL):
                    url, edition, collector_num, card_name = card_details
                    url = f'https://scryfall.com/{url}'
                    if card_name.find('/') != -1:
                        continue
                    if add_card_from_details(url, edition, collector_num, card_name, is_editions_check=True):
                        return True
            print(card_name, edition)
            print('    upload failed, card has no price!')
            return False  # card isn't added to database
        color_identity = get_color_identity_from_HTML(HTML.decode("utf-8"))
        if is_dfc:
            f_name_fixed, b_name_fixed = re.findall(r"<span class=\"card-text-card-name\">\n *(?P<name>.*?)\n", HTML.decode("utf-8"), re.DOTALL)
            f_name_fixed = decode_card_name(f_name_fixed)
            b_name_fixed = decode_card_name(b_name_fixed)
            url_name = convert_name_to_url_name(f'{f_name_fixed}-{b_name_fixed}')
            f_type, b_type = re.findall(r"<p class=\"card-text-type-line\".*?>\n *(<abbr class=\"color-indicator.*?</abbr> *)?(?P<type>[a-zA-Z ]*) ?.*? ?(?P<subtype>[a-z&A-Z ,]*)?\n</p>", HTML.decode("utf-8"), re.DOTALL)
            f_type = f'{f_type[1]} - {f_type[2]}' if f_type[2] else f_type[1]
            b_type = f'{b_type[1]} - {b_type[2]}' if b_type[2] else b_type[1]
            f_text, b_text = re.findall(r"<div class=\"card-text-oracle\">\n *(?P<text>.*?)\n *</div>", HTML.decode("utf-8"), re.DOTALL)
            f_text = f_text.replace('<p>', ' ').replace('</p>', '').replace('\n\n', '\n')
            b_text = b_text.replace('<p>', ' ').replace('</p>', '').replace('\n\n', '\n')
            img_url = re.search(r"img.*?src=\"(?P<img_url>[^\"]*)\"", HTML.decode("utf-8"), re.DOTALL)['img_url']
            img_url = img_url.replace("large", "normal")
            f_img_url = img_url
            b_img_url = img_url.replace("front", "back")
            mana_cost_htmls = re.findall(r"<span class=\"card-text-mana-cost\">.*?</span>", HTML.decode("utf-8"), re.DOTALL)
            if len(mana_cost_htmls) > 0:
                f_mana_val, f_mana_cost = get_mana_val_and_cost_from_mana_cost_html(mana_cost_htmls[0])
                if len(mana_cost_htmls) > 1:
                    b_mana_val, b_mana_cost = get_mana_val_and_cost_from_mana_cost_html(mana_cost_htmls[1])
                else:
                    b_mana_val, b_mana_cost = 0, ''
            else:
                f_mana_val, f_mana_cost = 0, ''
                b_mana_val, b_mana_cost = 0, ''
            print(f_name_fixed, collector_num, edition, nonfoil_price, color_identity)
            f_card = Card(f_name_fixed, f_type, f_text, edition, f'F{collector_num}', url, f_img_url, nonfoil_price, foil_price, color_identity, f_mana_cost,
                          f_mana_val, url_name)
            insert_card(f_card)
            print('    card added to database successfully!')

            print(b_name_fixed, collector_num, edition, nonfoil_price, color_identity)
            b_card = Card(b_name_fixed, b_type, b_text, edition, f'B{collector_num}', url, b_img_url, nonfoil_price, foil_price, color_identity, b_mana_cost,
                          b_mana_val, url_name)
            insert_card(b_card)
            print('    card added to database successfully!')
            return True  # card added to database
        else:
            name_fixed = re.search(r"<span class=\"card-text-card-name\">\n *(?P<name>.*?)\n", HTML.decode("utf-8"), re.DOTALL)['name']
            name_fixed = decode_card_name(name_fixed)
            url_name = convert_name_to_url_name(name_fixed)
            card_type = re.search(
                r"<p class=\"card-text-type-line\".*?>\n *(?P<type>[a-zA-Z ]*) ?.*? ?(?P<subtype>[a-z&A-Z ,]*)?\n</p>",
                HTML.decode("utf-8"), re.DOTALL)
            type = f'{card_type["type"]} - {card_type["subtype"]}' if card_type["subtype"] else card_type["type"]
            card_text = re.search(r"<div class=\"card-text-oracle\">\n *(?P<text>.*?)\n *</div>", HTML.decode("utf-8"), re.DOTALL)['text']
            text = card_text.replace('<p>', ' ').replace('</p>', '').replace('\n\n', '\n')
            img_url = re.search(r"img.*?src=\"(?P<img_url>[^\"]*)\"", HTML.decode("utf-8"), re.DOTALL)['img_url']
            img_url = img_url.replace("large", "normal")
            # prices = re.search(r"href=\"/card/{}/{}/{}\".*?<a title=\"(Nonfoil: \$(?P<nonfoil>.*?))?(, Foil: \$(?P<foil>[^\"]*))?\" class=\"currency-usd\"[^<]*</a>".format(edition, collector_num, card_name), HTML2.decode("utf-8"), re.DOTALL)
            find_mana_cost_html = re.search(r"<span class=\"card-text-mana-cost\">.*?</span>", HTML.decode("utf-8"), re.DOTALL)
            if find_mana_cost_html:
                mana_cost_html = find_mana_cost_html[0]
            else:
                mana_cost_html = ''
            mana_value, mana_cost = get_mana_val_and_cost_from_mana_cost_html(mana_cost_html)
            print(name_fixed, collector_num, edition, nonfoil_price, color_identity)
            card = Card(name_fixed, type, text, edition, f'F{collector_num}', url, img_url, nonfoil_price, foil_price, color_identity, mana_cost,
                        mana_value, url_name)
            insert_card(card)
            print('    card added to database successfully!')
            return True  # card added to database
    except:
        print('an error occurred while loading the card')


def add_all_versions_of_card(card_name, is_dfc=False):
    is_added = False
    HTML = urllib.request.urlopen(card_name).read()
    # find "next 60" button if exists
    for card_details in re.findall(
            r"<a data-component=\"card-tooltip\".*?href=\"(?P<url>/card/(?P<edition>.*?)/(?P<collector_num>.*?)/(?P<name>.*?))\".*?</a>",
            HTML.decode("utf-8"), re.DOTALL):
        url, edition, collector_num, card_name = card_details
        url = f'https://scryfall.com{url}'
        if card_name.find('/') != -1:
            continue
        if add_card_from_details(url, edition, collector_num, card_name, is_dfc=is_dfc):
            is_added = True
    return is_added


def add_cards_by_name(name, get_all_versions_of_card=False):
    # find all cards that contain the partial name in the database and in the browser
    name = name.replace(' ', '-').replace("'", "")
    is_db_changed = False
    webUrl = 'https://scryfall.com/search?q={}'.format(name)
    if get_all_versions_of_card:
        webUrl = 'https://scryfall.com/search?q=!{}&unique=prints'.format(name)
    try:
        HTML = urllib.request.urlopen(webUrl).read()
        one_faced_cards = re.findall(
            r"<a class=\"card-grid-item-card\" href=\"(?P<url>https://scryfall.com/card/(?P<edition>[^/]*)/(?P<collector_num>[^/]*)/(?P<card_name>[^\"]*))\">",
            HTML.decode("utf-8"), re.DOTALL)
        double_faced_cards = re.findall(
            r"<a class=\"card-grid-item-card\" data-component=\"card-grid-dfc\" href=\"(?P<url>https://scryfall.com/card/(?P<edition>[^/]*)/(?P<collector_num>[^/]*)/(?P<card_name>[^\"]*))\">",
            HTML.decode("utf-8"), re.DOTALL)
        if len(one_faced_cards) == 0 and len(double_faced_cards) == 0:
            # if the search sends you directly to the only card that in this search
            s = re.search(r"<a title=\".*?\".*?href=\"(?P<url>https://scryfall.com/card/(?P<edition>.*?)/(?P<collector_num>.*?)/(?P<card_name>.*?))\"/*?>en</a>",
                HTML.decode("utf-8"), re.DOTALL)
            is_dfc = False
            if re.search(r"<button.*?title=\"Turn Over Card\".*?</button>", HTML.decode("utf-8"), re.DOTALL):
                is_dfc = True
            is_db_changed = add_card_from_details(s['url'], s['edition'], s['collector_num'], s['card_name'], is_dfc=is_dfc) or is_db_changed
            # results = [(s['url'], s['edition'], s['collector_num'], s['card_name'])]
        else:
            for card_details in one_faced_cards:
                url, edition, collector_num, card_name = card_details
                is_db_changed = add_card_from_details(url, edition, collector_num, card_name) or is_db_changed
            for card_details in double_faced_cards:
                url, edition, collector_num, card_name = card_details
                is_db_changed = add_card_from_details(url, edition, collector_num, card_name, is_dfc=True) or is_db_changed
    except:
        print('invalid card name')
    return is_db_changed


def add_box_to_boxes(box_name, box_type, description):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("INSERT INTO boxes (box_name, type, description) VALUES (:box_name, :box_type, :description)",
                  {'box_name': box_name, 'box_type': box_type, 'description': description})
        if box_type == 'deck':
            c.execute("SELECT name FROM basic_lands")
            for land in c.fetchall():
                c.execute("INSERT INTO decks_basic_lands VALUES (:name, :deck_name, 0)", {'name': land[0], 'deck_name': box_name})



def add_card_to_collection(edition, collector_num, box, is_foil, is_commander=False):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("""INSERT INTO cards_collection (edition, collector_num, box, is_foil, is_commander)
                  VALUES (:edition, :collector_num, :box, :is_foil, :is_commander)""",
                  {'edition': edition, 'collector_num': collector_num, 'box': box, 'is_foil': is_foil, 'is_commander': is_commander})


def get_cards_in_collection_by_name(name):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        # do not allow duplicate names while searching for cards in the collection
        c.execute("""SELECT c.* from cards_collection as cc JOIN cards as c on cc.edition=c.edition AND
                     cc.collector_num=c.collector_num WHERE c.name like :name""", {'name': f'%{name}%'})
        cards = []
        for card in c.fetchall():
            if not any(c2.name == card[0] for c2 in cards):
                cards.append(Card(card[0], card[1], card[2], card[3], card[4], card[5], card[6], card[7], card[8], card[9],
                                  card[10], card[11], card[12]))
        return cards


def get_all_copies_in_collection(card_name):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("""SELECT cc.ID,cc.box,cc.is_foil,cc.is_commander, c.* from cards_collection as cc JOIN cards as c on
                  cc.edition=c.edition AND cc.collector_num=c.collector_num WHERE c.name=:card_name ORDER BY cc.box""",
                  {'card_name': card_name})
        decks_copies = []
        other_copies = []
        rows = c.fetchall()
        for row in rows:
            details = {'ID': row[0], 'box': row[1], 'is_foil': row[2], 'is_commander': row[3],
                       'card': Card(row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16])}
            c.execute("SELECT type from boxes where box_name=:box", {'box': details['box']})
            if c.fetchone()[0] == 'deck':
                decks_copies.append(details)
            else:
                other_copies.append(details)
        return decks_copies, other_copies


def get_all_cards_in_collection():
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT edition,collector_num FROM cards_collection")
        primary_keys = c.fetchall()
        cards = []
        for key in primary_keys:
            cards.append(get_card_in_db_by_primary_key(key[1], key[0]))
    return cards


def get_box_from_name(box_name):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT box_name,type,description FROM boxes WHERE box_name=:box_name", {'box_name': box_name})
        return c.fetchone()


def get_all_cards_in_box(box_name, get_commanders=False):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT c.*,cc.is_foil,cc.is_commander from cards_collection as cc JOIN cards as c on cc.edition=c.edition AND cc.collector_num=c.collector_num WHERE cc.box=:box_name", {'box_name': box_name})
        cards = []
        commanders = []
        for card in c.fetchall():
            if card[-1] == True:
                commanders.append({'card': Card(card[0], card[1], card[2], card[3], card[4], card[5], card[6], card[7],
                                   card[8], card[9], card[10], card[11], card[12]), 'is_foil': card[-2]})
            else:
                cards.append({'card': Card(card[0], card[1], card[2], card[3], card[4], card[5], card[6], card[7],
                              card[8], card[9], card[10], card[11], card[12]), 'is_foil': card[-2]})
    return cards, commanders if get_commanders else cards


def get_all_boxes(get_all=False):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT box_name, type FROM boxes")
        non_deck_boxes = []
        decks = []
        for box in c.fetchall():
            if box[1] == 'deck':
                decks.append(box[0])
            else:
                non_deck_boxes.append(box[0])
        if get_all:
            return non_deck_boxes + decks
        return non_deck_boxes, decks


def get_basic_lands_in_deck(deck, get_all_basics=False, get_count=False):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("""SELECT c.*,dbl.count FROM decks_basic_lands as dbl JOIN cards as c JOIN basic_lands bl on
                dbl.name=c.name AND c.name=bl.name WHERE dbl.deck_name=:deck order by bl.land_order""", {'deck': deck})
        cards = []
        all_basic_lands = []
        counts = {'Plains': 0, 'Island': 0, 'Swamp': 0, 'Mountain': 0, 'Forest': 0, 'Wastes': 0,
                  'Snow-Covered Plains': 0, 'Snow-Covered Island': 0, 'Snow-Covered Swamp': 0,
                  'Snow-Covered Mountain': 0, 'Snow-Covered Forest': 0}
        for basic_land in c.fetchall():
            counts[basic_land[0]] = basic_land[-1]
            card = Card(basic_land[0], basic_land[1], basic_land[2], basic_land[3], basic_land[4], basic_land[5],
                        basic_land[6], -1, -1, basic_land[9], basic_land[10], basic_land[11],
                        basic_land[12])  # -1 for prices
            if card.name[:5] != 'Snow-':
                all_basic_lands.append(card)
            for i in range(basic_land[-1]):
                cards.append(card)
        return_value = {'cards': cards}
        if get_all_basics:
            return_value['all_basic_lands'] = all_basic_lands
        if get_count:
            return_value['counts'] = counts
    return return_value


def get_all_basic_lands(get_snow=False):  # returns a list of all basic lands except for snow lands *not only basic lands in collection
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        names = ['Plains', 'Island', 'Swamp', 'Mountain', 'Forest', 'Wastes']
        if get_snow:
            names = ['Snow-Covered ' + name for name in names[:5]] + names[5:]
        c.execute(f"""SELECT name,img_url FROM cards WHERE name in ('{"','".join(names)}')""")
        return [{'name': bl[0], 'img_url': bl[1]} for bl in c.fetchall()]


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
    non_deck_boxes, decks = get_all_boxes()
    return render_template('home.html', non_deck_boxes=non_deck_boxes, decks=decks)


@app.route('/box/<box_name>')
def box_page(box_name):
    cards = get_all_cards_in_box(box_name)[0]
    box_type, description = get_box_from_name(box_name)[1:]
    return render_template('box.html', cards=cards, box_name=box_name, box_type=box_type, box_description=description)


@app.route('/deck/<deck_name>')
def deck_page(deck_name):
    cards, commanders = get_all_cards_in_box(deck_name, get_commanders=True)
    basics = get_basic_lands_in_deck(deck_name, get_all_basics=True, get_count=True)
    basic_lands, basic_lands_count, all_basic_lands = basics['cards'], basics['counts'], basics['all_basic_lands']
    for card in basic_lands:
        cards.append({'card': card, 'is_foil': False})
    deck_description = get_box_from_name(deck_name)[2]
    return render_template('deck.html', cards=cards, commanders=commanders, deck_name=deck_name,
                           deck_description=deck_description, basic_lands=all_basic_lands,
                           snow_basic_lands=get_all_basic_lands(get_snow=True), basic_lands_count=basic_lands_count)


@app.route('/search')
def search_results():
    keyword = request.args.get('name')
    updated = request.args.get('updated', default='false')
    cards = get_cards_in_db_by_name(keyword)
    return render_template('search_res.html', cards=cards, keyword=keyword, updated=updated)


@app.route('/search/in_collection')
def search_in_collection():
    keyword = request.args.get('name')
    cards = get_cards_in_collection_by_name(keyword)
    return render_template('collection_search_res.html', cards=cards, keyword=keyword)


@app.route('/update_basic_land_count/<deck>/<name>/<count>')
def update_basic_land_count(deck, name, count):
    deck = decode_card_name(deck)
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("""UPDATE decks_basic_lands SET count=:count WHERE name=:name and deck_name=:deck""", {'deck':deck, 'name': name, 'count': count})
    return 'updated'


@app.route('/update_db_with_search_res/<keyword>')
def update_db_with_search_res(keyword):
    is_db_changed = add_cards_by_name(keyword)
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
    front_card = get_cards_in_db_by_name(card_name, is_exact_match=True)[0]
    is_db_changed = add_cards_by_name(front_card.name, get_all_versions_of_card=True)
    return 'changed' if is_db_changed else 'not changed'


@app.route('/card/<collector_num>/<edition>')
def card_page(collector_num, edition):
    copy_id = request.args.get('copy_id', default=None)
    front_card = get_card_in_db_by_primary_key(collector_num, edition)
    back_card = get_card_in_db_by_primary_key(f'B{front_card.collector_num[1:]}', front_card.edition)
    for card in [front_card, back_card]:
        if card is not None:
            card.text_list[0] = card.text_list[0].replace('<i>', '').replace('</i>', '')
            for t in re.findall("(<abbr.*?>{(?P<symbol>.*?)}</abbr>)", card.oracle_text):
                idx = card.text_list[-1].find(t[0])
                last_text_pile = card.text_list[-1]
                card.text_list[-1] = last_text_pile[:idx]
                card.text_list.append(f"/{t[1].replace('/', 'or')}/")
                card.text_list.append(last_text_pile[idx+len(t[0]):].replace('<i>', '').replace('</i>', ''))
    return render_template('card.html', front_card=front_card, back_card=back_card, decks=get_all_boxes()[1], copy_id=copy_id)


@app.route('/card-copies/<name>')
def card_copies(name):
    decks_copies, other_copies = get_all_copies_in_collection(name)
    return render_template('card_copies.html', decks_copies=decks_copies, other_copies=other_copies, name=name, decks=get_all_boxes()[1])


@app.route('/remove_card_from_collection/<card_id>')
def remove_card_from_collection(card_id):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("DELETE FROM cards_collection WHERE ID=:card_id", {'card_id': card_id})
    return 'removed'


@app.route('/get_card_from_collection/<card_id>')
def get_card_from_collection(card_id):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT c.*,cc.is_foil from cards_collection as cc JOIN cards as c on cc.edition=c.edition AND cc.collector_num=c.collector_num WHERE cc.ID=:card_id", {'card_id': card_id})
        card = c.fetchone()
    return {**Card(card[0], card[1], card[2], card[3], card[4], card[5], card[6], card[7], card[8], card[9], card[10],
                   card[11], card[12]).__dict__, **{'is_foil': card[13]}}


@app.route('/get_box_for_card/<color_id>/<is_foil>/<nonfoil_price>/<foil_price>')
def get_box_for_card(color_id, is_foil, nonfoil_price, foil_price):
    box_name = ''
    if len(color_id) == 1:  # if color_id is a single color(W,U,B...) or colorless(C)
        box_name += color_id
    else:  # if card is a multicolored
        box_name += 'M'
    price = foil_price if is_foil == '1' else nonfoil_price
    if price == '-1':
        return 'false'  # if price is -1, it means that card has no price
    if float(price) >= 2:
        box_name = '2$+'
    elif 0.5 <= float(price) <= 2 and color_id != 'C' and color_id[0] != 'M':
        box_name += ' 0.5$-2$'
    elif 0 <= float(price) <= 0.5 and color_id != 'C' and color_id[0] != 'M':
        box_name += ' 0$-0.5$'
    elif color_id != 'C' and color_id[0] != 'M':
        return 'false'
    return box_name


@app.route('/move_card_to_box/<card_id>/<box_name>')
def move_card_to_box(card_id, box_name):
    if box_name == 'Get Proper Box':
        box_name = get_box_for_card()
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("UPDATE cards_collection SET box=:box_name WHERE ID=:card_id", {'card_id': card_id, 'box_name': box_name})
    return 'moved'


@app.route('/add_to_cards_collection/<edition>/<collector_num>/<box>/<is_foil>')
def add_to_cards_collection(edition, collector_num, box, is_foil):
    add_card_to_collection(edition, collector_num, box, True if is_foil == 'true' else False)
    return box


@app.route('/add_to_deck/<edition>/<collector_num>/<deck>/<is_foil>/<is_commander>')
def add_to_deck(edition, collector_num, deck, is_foil, is_commander):
    add_card_to_collection(edition, collector_num, deck, True if is_foil == 'true' else False, True if is_commander == 'true' else False)
    return deck


@app.route('/add_box/<box_name>/<box_type>')
def add_box(box_name, box_type):
    description = request.args.get('description', default='')
    add_box_to_boxes(box_name, box_type, description)
    return 'added'


app.run(debug=True)
conn.close()

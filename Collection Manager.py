import json
import sqlite3
import urllib.request
import urllib.parse
import re
from flask import Flask, render_template, request


class Card:
    def __init__(self, name, type, oracle_text, edition, collector_num, card_url, img_url, nonfoil_price, foil_price,
                 color_identity, mana_cost, mana_value, url_name, card_layout, json_url):
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
        self.card_layout = card_layout
        self.json_url = json_url

        self.text_list = [self.oracle_text]


app = Flask(__name__)
app.config['SECRET_KEY'] = '7ad953930b59971b4fded5852a023868'


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
        c.execute("""INSERT INTO cards VALUES (:name, :type, :oracle_text, :edition, :collector_num, :card_url, :img_url,
                     :nonfoil_price, :foil_price, :color_identity, :mana_cost, :mana_value, :url_name, :card_layout, :json_url)""",
                  {'name': card.name, 'type': card.type, 'oracle_text': card.oracle_text,  'edition': card.edition,
                   'collector_num': card.collector_num, 'card_url': card.card_url, 'img_url': card.img_url,
                   'nonfoil_price': card.nonfoil_price, 'foil_price': card.foil_price,
                   'color_identity': card.color_identity, 'mana_cost': card.mana_cost, 'mana_value': card.mana_value,
                   'url_name': card.url_name, 'card_layout': card.card_layout, 'json_url': card.json_url})


def update_card_values(collector_num, edition, card):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("""UPDATE cards SET name=:name, type=:type, oracle_text=:oracle_text, edition=:card_edition,
                     collector_num=:card_collector_num, card_url=:card_url, img_url=:img_url,
                     nonfoil_price=:nonfoil_price, foil_price=:foil_price, color_identity=:color_identity,
                     mana_cost=:mana_cost, mana_value=:mana_value, url_name=:url_name, card_layout=:card_layout,
                     json_url=:json_url WHERE collector_num = :collector_num AND edition = :edition""",
                  {'name': card.name, 'type': card.type, 'oracle_text': card.oracle_text, 'card_edition': card.edition,
                   'card_collector_num': card.collector_num, 'card_url': card.card_url, 'img_url': card.img_url,
                   'nonfoil_price': card.nonfoil_price, 'foil_price': card.foil_price,
                   'color_identity': card.color_identity, 'mana_cost': card.mana_cost, 'mana_value': card.mana_value,
                   'url_name': card.url_name, 'card_layout': card.card_layout, 'json_url': card.json_url,
                   'collector_num': collector_num, 'edition': edition,
                   })


def remove_card_by_primary_key(collector_num, edition):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("DELETE from cards WHERE collector_num = :collector_num AND edition = :edition",
                  {'collector_num': collector_num, 'edition': edition})


def get_cards_by_price(min_price, max_price):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM cards WHERE price <= :max_price AND :min_price <= price", {'min_price': min_price, 'max_price': max_price})
        return c.fetchall()


def get_cards_by_edition(edition):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
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
        return Card(card[0], card[1], card[2], card[3], card[4], card[5], card[6], card[7], card[8], card[9], card[10], card[11], card[12], card[13], card[14])


def get_cards_in_db_by_name(name, get_duplicates=False, is_exact_match=False, get_cards_back=False):
    cards = []
    for card in get_cards_details_in_db_by_name(name, is_exact_match=is_exact_match):
        if not get_cards_back and card[4][0] == 'B':  # check if the card is the back of double faced card
            continue
        if not get_duplicates:
            # check if another card with the same name is already in the list
            if any(c.name == card[0] for c in cards):
                continue
        cards.append(Card(card[0], card[1], card[2], card[3], card[4], card[5], card[6], card[7], card[8], card[9], card[10], card[11], card[12], card[13], card[14]))
    return cards


def get_card_in_db_by_url_name(url_name):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM cards WHERE url_name = :url_name", {'url_name': url_name})
        card = c.fetchone()
        if card is None:
            return None
        return Card(card[0], card[1], card[2], card[3], card[4], card[5], card[6], card[7], card[8], card[9], card[10], card[11], card[12], card[13], card[14])


def add_card_from_json(card_json, update_existing=False):
    # check if card in database
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute(f"SELECT * FROM cards WHERE collector_num=:collector_num AND edition=:edition",
                  {'collector_num': f"F{card_json['collector_number']}", 'edition': card_json['set']})
        if c.fetchone() and not update_existing:
            print(f'{card_json["name"]} already in database')
            return False

    layout = card_json['layout']
    if layout in ['modal_dfc', 'transform']:
        layout = 'dfc'
    elif layout not in ['split', 'flip', 'adventure']:
        layout = 'normal'
    if layout in ['split', 'flip', 'adventure']:
        print('split or flip cards are not supported currently')
        return False
    card_faces = [card_json]
    if layout in ['dfc', 'split', 'flip']:
        card_faces = card_json['card_faces']
    for card_face, face in zip(card_faces, ['F', 'B']):
        card_name = card_face['name']
        card_type = card_face['type_line']
        oracle_text = card_face['oracle_text']
        edition = card_json['set']
        collector_num = f"{face}{card_json['collector_number']}"  # (F/B)collector_number
        scryfall_url = card_json['scryfall_uri'].split('?')[0]  # remove '?utm_source=api'
        json_url = card_json['uri']
        img_url = card_face['image_uris']['normal']
        nonfoil_price = card_json['prices']['usd']
        foil_price = card_json['prices']['usd_foil']
        nonfoil_price = nonfoil_price if nonfoil_price else -1
        foil_price = foil_price if foil_price else -1
        if nonfoil_price == -1 and foil_price == -1:
            print(f'{card_name} {edition} {collector_num} has no price')
            return False
        color_identity = ''.join(card_json['color_identity'])
        if color_identity == '':
            color_identity = 'C'
        if len(color_identity) > 1:
            color_identity = 'M'+color_identity
        mana_cost = card_face['mana_cost']
        if 'cmc' in card_face:
            mana_value = card_face['cmc']
        else:
            mana_value = 0
            for mana in mana_cost.replace('{','').replace('}',''):
                if mana.isdecimal():
                    mana_value += int(mana)
                elif mana != 'X':
                    mana_value += 1

        url_name = scryfall_url.split('/')[-1]

        card = Card(card_name, card_type, oracle_text, edition, collector_num, scryfall_url, img_url, nonfoil_price,
                    foil_price, color_identity, mana_cost, mana_value, url_name, layout, json_url)

        print(card_name, edition, collector_num, layout)
        if update_existing:
            update_card_values(collector_num, edition, card)
            print('    card updated successfully!')
        else:
            insert_card(card)
            print('    card added to database successfully!')
    return True  # card added to database


def add_cards_from_json(json_url):
    is_db_changed = False
    with urllib.request.urlopen(json_url) as url:
        data = json.loads(url.read().decode())
        for card in data['data']:
            if card['lang'] == 'en':
                is_db_changed = add_card_from_json(card) or is_db_changed
        if 'next_page' in data:
            is_db_changed = add_cards_from_json(data['next_page']) or is_db_changed
    return is_db_changed


def add_cards_by_name(keyword, get_all_versions_of_card=False):
    # find all cards that contain the partial name in the database and in the browser
    keyword = convert_name_to_url_name(keyword)
    is_db_changed = False
    webUrl = f'https://api.scryfall.com/cards/search?order=name&q={keyword}'
    if get_all_versions_of_card:
        webUrl = f'https://api.scryfall.com/cards/search?order=name&q=!{keyword}&unique=prints'
    try:
        is_db_changed = add_cards_from_json(webUrl) or is_db_changed

    except Exception as e:
        print(e)
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
        if get_box_from_name(box) is None:
            add_box(box, 'box')
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
                                  card[10], card[11], card[12], card[13], card[14]))
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
                       'card': Card(row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13],
                                    row[14], row[15], row[16], row[17], row[18])}
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
                                   card[8], card[9], card[10], card[11], card[12], card[13], card[14]), 'is_foil': card[-2]})
            else:
                cards.append({'card': Card(card[0], card[1], card[2], card[3], card[4], card[5], card[6], card[7],
                              card[8], card[9], card[10], card[11], card[12], card[13], card[14]), 'is_foil': card[-2]})
    return cards, commanders if get_commanders else cards


def get_all_boxes(get_all=False):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT box_name, type, background FROM boxes")
        non_deck_boxes = []
        decks = []
        for box in c.fetchall():
            if box[1] == 'deck':
                decks.append({'name': box[0], 'background': box[2]})
            else:
                non_deck_boxes.append({'name': box[0], 'background': box[2]})
        if get_all:
            return non_deck_boxes + decks
        return non_deck_boxes, decks


def get_basic_lands_in_deck(deck, get_all_basics=False, get_count=False):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        # geet only one of each basic land name
        c.execute("""SELECT c.*,dbl.count FROM decks_basic_lands as dbl JOIN cards as c JOIN basic_lands bl on
                dbl.name=c.name AND c.name=bl.name WHERE dbl.deck_name=:deck group by bl.name order by bl.land_order""",
                  {'deck': deck})
        cards = []
        all_basic_lands = []
        counts = {'Plains': 0, 'Island': 0, 'Swamp': 0, 'Mountain': 0, 'Forest': 0, 'Wastes': 0,
                  'Snow-Covered Plains': 0, 'Snow-Covered Island': 0, 'Snow-Covered Swamp': 0,
                  'Snow-Covered Mountain': 0, 'Snow-Covered Forest': 0}
        for basic_land in c.fetchall():
            counts[basic_land[0]] = basic_land[-1]
            card = Card(basic_land[0], basic_land[1], basic_land[2], basic_land[3], basic_land[4], basic_land[5],
                        basic_land[6], -1, -1, basic_land[9], basic_land[10], basic_land[11],
                        basic_land[12], basic_land[13], basic_land[14])  # -1 for prices
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


def check_if_box_is_full(box_name, max_cards):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT count(*) FROM cards_collection WHERE box=:box_name", {'box_name': box_name})
        return c.fetchone()[0] >= max_cards


@app.route('/')
@app.route('/home')
def index():
    non_deck_boxes, decks = get_all_boxes()
    return render_template('home.html', non_deck_boxes=non_deck_boxes, decks=decks)


@app.route('/box/<box_name>')
def box_page(box_name):
    cards = get_all_cards_in_box(box_name)[0]
    box_type, description = get_box_from_name(box_name)[1:]
    total_price = get_box_total_price(box_name)
    return render_template('box.html', cards=cards, box_name=box_name, box_type=box_type, box_description=description,
                           total_price=total_price)


@app.route('/deck/<deck_name>')
def deck_page(deck_name):
    cards, commanders = get_all_cards_in_box(deck_name, get_commanders=True)
    basics = get_basic_lands_in_deck(deck_name, get_all_basics=True, get_count=True)
    basic_lands, basic_lands_count, all_basic_lands = basics['cards'], basics['counts'], basics['all_basic_lands']
    total_price = get_box_total_price(deck_name)
    for card in basic_lands:
        cards.append({'card': card, 'is_foil': False})
    deck_description = get_box_from_name(deck_name)[2]
    max_mv_col = 7
    column_titles = ['Lands', '0-1'] + [str(i) for i in range(2, max_mv_col)] + [str(max_mv_col)+'+']
    columns = [[] for i in range(max_mv_col+1)]
    for card in cards:
        mana_val = card['card'].mana_value
        idx = mana_val
        if 'Land' in card['card'].type:
            idx = 0
        elif mana_val == 0:
            idx = 1
        elif idx > max_mv_col:
            idx = max_mv_col
        columns[idx].append(card)
    return render_template('deck.html', cards=cards, commanders=commanders, deck_name=deck_name,
                           deck_description=deck_description, basic_lands=all_basic_lands,
                           basic_lands_count=basic_lands_count, columns=columns, column_titles=column_titles,
                           total_price=total_price)


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
    front_card = get_card_in_db_by_primary_key(f'F{collector_num}', edition)
    back_card = get_card_in_db_by_primary_key(f'B{collector_num}', front_card.edition)
    for card in [front_card, back_card]:
        if card is not None:
            card.text_list[0] = card.text_list[0].replace('<i>', '').replace('</i>', '')
            for t in re.findall("{(?P<symbol>.*?)}", card.oracle_text):
                idx = card.text_list[-1].find('{'+t+'}')
                last_text_pile = card.text_list[-1]
                card.text_list[-1] = last_text_pile[:idx]
                card.text_list.append('{'+t.replace('/', 'or')+'}')
                card.text_list.append(last_text_pile[idx+len('{'+t+'}'):].replace('<i>', '').replace('</i>', ''))
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
                   card[11], card[12], card[13], card[14]).__dict__, **{'is_foil': card[-1]}}


@app.route('/get_box_for_card/<card_type>/<color_id>/<is_foil>/<nonfoil_price>/<foil_price>')
def get_box_for_card(card_type, color_id, is_foil, nonfoil_price, foil_price):
    box_name = ''
    if len(color_id) == 1:  # if color_id is a single color(W,U,B...) or colorless(C)
        box_name += color_id
    else:  # if card is a multicolored
        box_name += 'M'
    price = foil_price if is_foil == 'true' else nonfoil_price
    if price == '-1':
        return 'false'  # if price is -1, it means that card has no price
    if float(price) >= 2:
        box_name = '2$+'
    elif card_type.find('Land') != -1:
        box_name = 'Lands'
    elif 0.5 <= float(price) <= 2 and color_id != 'C':
        box_name += ' 0.5$-2$'
    elif 0 <= float(price) <= 0.5 and color_id != 'C':
        box_name += ' 0$-0.5$'
    elif color_id != 'C':
        return 'false'

    if box_name != '2$+':
        box_name += ' #1'
        while check_if_box_is_full(box_name, 100):
            box_name = box_name[:-1] + str(int(box_name[-1]) + 1)

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


@app.route('/set_box_background/<box_name>')
def set_box_background(box_name):
    background = request.args.get('background', default='')
    box_name = decode_card_name(box_name)
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("UPDATE boxes SET background=:background WHERE box_name=:box_name", {'box_name': box_name, 'background': background})
    return 'success'


@app.route('/get_box_price/<box_name>')
def get_box_total_price(box_name):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute("""select sum(c.foil_price) from cards as c join cards_collection as cc on c.edition=cc.edition and
                     c.collector_num=cc.collector_num where cc.box=:box_name and cc.is_foil""", {'box_name': box_name})
        foil_price = c.fetchone()[0]
        c.execute("""select sum(c.nonfoil_price) from cards as c join cards_collection as cc on c.edition=cc.edition and
                     c.collector_num=cc.collector_num where cc.box=:box_name and not(cc.is_foil)""", {'box_name': box_name})
        nonfoil_price = c.fetchone()[0]
        if foil_price is None:
            foil_price = 0
        if nonfoil_price is None:
            nonfoil_price = 0
    return round(nonfoil_price + foil_price, 2)


@app.route('/update_card/<edition>/<collector_num>')
def update_card_in_db(edition, collector_num):
    with sqlite3.connect('cards database.db') as conn:
        c = conn.cursor()
        c.execute(f"SELECT * FROM cards WHERE collector_num=:collector_num AND edition=:edition",
                  {'collector_num': f'F{collector_num}', 'edition': edition})
        card = c.fetchone()
        if not card:
            return 'error'  # card is not in database
        json_url = card[14]
        with urllib.request.urlopen(json_url) as url:
            card_json = json.loads(url.read().decode())
            add_card_from_json(card_json, update_existing=True)
    return 'updated'


app.run(debug=True)

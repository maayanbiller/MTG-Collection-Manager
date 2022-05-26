import sqlite3

class Card():
    def __init__(self, name, edition, img_url, price):
        self.name = name
        self.edition = edition
        self.img_url = img_url
        self.price = price

conn = sqlite3.connect('cards database.db')

c = conn.cursor()

c.execute("""CREATE TABLE cards (
            name text,
            edition text,
            img_url text,
            price real
            )""")


def insert_card(card):
    with conn:
        c.execute("INSERT INTO cards VALUES (:name, :edition, :img_url, :price)", {'name': card.name, 'edition': card.edition, 'img_url': card.img_url, 'price': card.price})


def remove_card(card):
    with conn:
        c.execute("DELETE from cards WHERE name = :name AND edition = :edition", {'name': card.name, 'edition': card.edition})


def get_cards_by_price(min_price, max_price):
    with conn:
        c.execute("SELECT * FROM cards WHERE price <= :max_price AND :min_price <= price", {'min_price': min_price, 'max_price': max_price})
        return c.fetchall()


def get_cards_by_edition(edition):
    with conn:
        c.execute("SELECT * FROM cards WHERE edition=:edition", {'edition': edition})
        return c.fetchall()


def get_all_cards():
    with conn:
        c.execute("SELECT * FROM cards WHERE true")
        return c.fetchall()


# card1 = Card('swamp', 'C20', 0.05)
# insert_card(card1)

# print(get_cards_by_edition('IKO'))

# for i in range(1):
#     card_name = input('insert a card name: ')
#     edition = input('insert an edition code name: ')
#     price = input('insert a price: ')
#     card = Card(card_name, edition, price)
#     insert_card(card)
#     print('card added!\n    {}\n'.format((card_name, edition, price)))

card_name = 'swamp'


print(get_all_cards())

conn.close()

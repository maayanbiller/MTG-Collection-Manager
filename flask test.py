from flask import Flask, render_template
app = Flask(__name__)

app.config['SECRET_KEY'] = '7ad953930b59971b4fded5852a023868'

cards = [
    {
        'name': 'Opt',
        'edition': 'm21',
        'price': 0.24,
        'img_url': 'https://c1.scryfall.com/file/scryfall-cards/normal/front/3/2/323db259-d35e-467d-9a46-4adcb2fc107c.jpg?1652898493',
    },
    {
        'name': 'Jegantha, the Wellspring',
        'edition': 'iko',
        'price': 2.22,
        'img_url': 'https://c1.scryfall.com/file/scryfall-cards/normal/front/1/d/1d52e527-3835-4350-8c01-0f2d5d623b9c.jpg?1600967546',
    }
]


@app.route('/')
@app.route('/home')
def hello():
    return render_template('home.html', cards=cards)


# @app.route(f'/{card.name}')
# def hello(card):
#     return render_template('home.html', cards=cards)


if __name__ == '__main__':
    app.run(debug=True)
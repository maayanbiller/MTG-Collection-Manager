from flask import Flask, render_template
from forms import RegistrationForm, LoginForm
app = Flask(__name__)

app.config['SECRET_KEY'] = '7ad953930b59971b4fded5852a023868'

posts = [
    {
        'author': 'Corey Schafer',
        'title': 'Blog Post 1',
        'content': 'First post content',
        'date_posted': 'April 20, 2018'
    },
    {
        'author': 'Jane Doe',
        'title': 'Blog Post 2',
        'content': 'Second post content',
        'date_posted': 'April 21, 2018'
    }
]


@app.route('/')
@app.route('/home')
def hello():
    return render_template('search_res.html', posts=posts)

@app.route('/about')
def about():
    return render_template('about.html', title='About')

@app.route('/register')
def register():
    form = LoginForm()
    return render_template('login.html', title='Login', form=form)

@app.route('/login')
def register():
    form = RegistrationForm()
    return render_template('register.html', title='Register', form=form)


if __name__ == '__main__':
    app.run(debug=True)
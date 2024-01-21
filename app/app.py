from flask import Flask, render_template, session
from passlib.hash import sha256_crypt
from src import users, clubs
import src.llib as llib

app = Flask(__name__)
app.register_blueprint(users.blueprint)
app.register_blueprint(clubs.blueprint)
app.secret_key = 'BAD_SECRET_KEY'


@app.route('/')
def main():
    ret = llib.Response()
    if 'loggedIn' in session:
        ret = llib.getClubs()
    return render_template('index.html', back=None, clubs=ret.data)


if __name__ == '__main__':
    app.run()

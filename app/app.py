from flask import Flask, render_template
from passlib.hash import sha256_crypt
from src import users, clubs, trainings, results

app = Flask(__name__)
app.register_blueprint(users.blueprint)
app.register_blueprint(clubs.blueprint)
app.register_blueprint(trainings.blueprint)
app.register_blueprint(results.blueprint)


@app.route('/')
def main():
    return render_template('index.html', back=None)


if __name__ == '__main__':
    app.run()

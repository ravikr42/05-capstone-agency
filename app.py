import os
from flask import Flask
from models import setup_db, db_drop_and_create_all
from flask_cors import CORS


def create_app(test_config=None):

    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    @app.route('/')
    def get_greeting():
        # excited = os.environ['EXCITED']
        excited = 'true'
        greeting = "Hello"
        if excited == 'true':
            greeting = greeting + "!!!!!"
        else:
            greeting = greeting + "?????"
        return greeting

    @app.route('/coolkids')
    def be_cool():
        return "Be cool, man, be coooool! You're almost a FSND grad!"

    return app


app = create_app()

if __name__ == '__main__':
    app.run()

# starter:
# https://github.com/udacity/FSND/tree/master/projects/capstone/heroku_sample/starte
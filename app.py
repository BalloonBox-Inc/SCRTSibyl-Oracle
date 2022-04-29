from flask import Flask
from flask_cors import CORS


def create_app():

    app = Flask(__name__)
    CORS(app, resources={
        r'/*': {
            'methods': ['POST', 'GET', 'OPTIONS'],
            'allow_headers': ['*'],
            'supports_credentials': True
        }
    })
    return app


app = create_app()
app.app_context().push()

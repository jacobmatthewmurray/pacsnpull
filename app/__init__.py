import os 
from flask import Flask, session


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        SECRET_KEY='dev',
        UPLOAD_PATH=app.instance_path,)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import dicomconnect
    app.register_blueprint(dicomconnect.bp)

    return app 




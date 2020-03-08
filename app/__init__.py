import os 
from flask import Flask, render_template


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        SECRET_KEY='dev',
        UPLOAD_PATH=app.instance_path,)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route('/', methods=['GET'])
    def index():
        return render_template('/index.html')

    from . import dicomconnect
    app.register_blueprint(dicomconnect.bp)

    return app 




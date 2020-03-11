import os
from flask import Flask, render_template


def create_app():
    app = Flask(__name__)

    app.config.from_mapping(SECRET_KEY='dev',)

    [os.makedirs(os.path.join(app.instance_path, directory), exist_ok=True) for directory in ['dcm', 'log', 'qry']]

    @app.route('/', methods=['GET'])
    def index():
        return render_template('/index.html')

    from . import dicomconnect
    app.register_blueprint(dicomconnect.bp)

    return app




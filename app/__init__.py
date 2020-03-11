import os
from flask import Flask, render_template


def create_app():
    app = Flask(__name__)

    app.config.from_mapping(SECRET_KEY='dev',)
    os.makedirs(app.instance_path, exist_ok=True)

    @app.route('/', methods=['GET'])
    def index():
        return render_template('/index.html')

    from . import dicomconnect
    app.register_blueprint(dicomconnect.bp)

    return app




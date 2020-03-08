import os
import json
import io
import subprocess
from datetime import datetime
from flask import (
        Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify, render_template_string,
current_app
        )

from app.dicomconnector import Mover
from app.forms import ConfigurationForm

bp = Blueprint('dicomconnect', __name__, url_prefix='/dicomconnect')


@bp.route('/', methods=['GET'])
def index():
    return render_template('/dicomconnect/index.html')


@bp.route('/overview', methods=['GET'])
def overview():
    config_form = ConfigurationForm()

    if 'configuration' not in session:
        session['configuration'] = {}
    if 'query_preview' not in session:
        session['query_preview'] = {}

    configuration = session['configuration']
    query_preview = session['query_preview']


    return render_template('/dicomconnect/overview.html', config_form=config_form, configuration=configuration,
                           query_preview=query_preview)


@bp.route('/_query', methods=['GET', 'POST'])
def _query():

    if request.method == 'POST':
        file = request.files['file']
        data = json.load(io.BytesIO(file.stream.read()))

        with open(os.path.join(current_app.config['UPLOAD_PATH'], file.filename), 'w') as json_file:
            json.dump(data, json_file)

        session['current_query_file'] = file.filename

        return jsonify(data)

    elif request.method == 'GET':

        if 'current_query_file' not in session:
            return jsonify({})
        else:
            with open(os.path.join(current_app.config['UPLOAD_PATH'], session['current_query_file'])) as json_file:
                queries = json.load(json_file)
            return jsonify(queries)

    return None


@bp.route('/_configuration', methods=['POST', 'GET'])
def _configuration():
    if request.method == 'POST':
        session['configuration'] = {
            'host_ip': request.form['host_ip'],
            'host_port': int(request.form['host_port']),
            'client_name': request.form['client_name'],
            'client_ip': request.form['client_ip'],
            'client_port': int(request.form['client_port']),
            'dcm_storage_path': request.form['dcm_storage_path'],
            'log_storage_path': request.form['log_storage_path'],
            'query_model': request.form['query_model'],
            'query_break_count': int(request.form['query_break_count'])
        }
        configuration = session['configuration']

    else:
        if 'configuration' in session:
            configuration = session['configuration']
        else:
            configuration = {}

    return jsonify(configuration)


@bp.route('/_save_json', methods=['POST'])
def _save_json():
    if 'filename' not in request.headers:
        return 'error: no filename provided'

    filename = request.headers['filename']

    with open(os.path.join(current_app.config['UPLOAD_PATH'], filename + '.json'), 'w') as json_file:
        json.dump(request.json, json_file)

    return 'success: json file saved'


@bp.route('/_echo', methods=['GET'])
def _echo():
    connector = Mover(session['configuration'])
    response = connector.send_c_echo()
    return 'Status Code: {}, Status Category: {}'.format(response['status']['code'], response['status']['category'])


@bp.route('/find', methods=['GET'])
def find():
    return render_template('/dicomconnect/find.html')


@bp.route('/_find', methods=['POST'])
def _find():
    assert 'configuration' in session
    qry = request.get_json()
    connector = Mover(session['configuration'])
    responses_dict = connector.send_c_find(qry)
    connector.assoc.release()
    return jsonify(responses_dict)


@bp.route('/_move', methods=['POST'])
def _move():
    assert 'configuration' in session
    qry = request.get_json()
    connector = Mover(session['configuration'])
    responses_dict = connector.send_c_move(qry)
    connector.assoc.release()
    return jsonify(responses_dict)


@bp.route('/move', methods=['GET'])
def move():
    return render_template('/dicomconnect/move.html')


@bp.route('/_store', methods=['GET'])
def _store():
    if 'storage_running' not in session:
        session['storage_running'] = False

    store_status = ''

    if session['storage_running']:
        stop_store = 'kill $(pidof storescp | awk "{print $1}")'
        subprocess.Popen(stop_store, shell=True)
        store_status = 'store off'

    else:
        configuration = session['configuration']['dcm_storage_path']
        client_port = str(session['configuration']['client_port'])
        start_store = 'storescp -su "" -od "' + configuration + '" ' + client_port
        subprocess.Popen(start_store, shell=True)
        store_status = 'store on'

    session['storage_running'] = not session['storage_running']

    return store_status


@bp.route('/_store_stream', methods=['GET'])
def _store_stream():
    if 'storage_running' not in session:
        session['storage_running'] = False

    if session['storage_running']:
        # return stream from store process here
        pass
    else:
        return jsonify({})



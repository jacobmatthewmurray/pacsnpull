import os
import json
import io
import subprocess
import datetime
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
    configuration = session['configuration']

    return render_template('/dicomconnect/overview.html', config_form=config_form, configuration=configuration)


@bp.route('/_query', methods=['GET', 'POST'])
def _query():

    if request.method == 'POST':

        if 'file' in request.files:

            file = request.files['file']
            data = json.load(io.BytesIO(file.stream.read()))
            filename = file.filename

        else:

            data = request.get_json()
            filename = 'find_2_move_' + str(datetime.now()) + '.json'

        with open(os.path.join(current_app.config['UPLOAD_PATH'], filename), 'w') as json_file:
            json.dump(data, json_file)

        session['current_query_file'] = filename

        return jsonify(data)

    elif request.method == 'GET':

        if 'current_query_file' not in session:
            return jsonify({})
        else:
            with open(os.path.join(current_app.config['UPLOAD_PATH'], session['current_query_file'])) as json_file:
                queries = json.load(json_file)
            return jsonify(queries)

    return None


@bp.route('/_set_query_file', methods=['POST'])
def _set_query_file():
    assert 'current_query_file' in request.get_json()
    session['current_query_file'] = request.get_json()['current_query_file']
    return jsonify({'current_query_file': session['current_query_file']})


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


@bp.route('/_store', methods=['GET'])
def _store():

    if 'storage_running' not in session:
        session['storage_running'] = False

    if session['storage_running']:
        stop_store = 'kill $(pidof storescp | awk "{print $1}")'
        subprocess.Popen(stop_store, shell=True)
        session['storage_running'] = False

    else:
        configuration = session['configuration']['dcm_storage_path']
        client_port = str(session['configuration']['client_port'])
        start_store = 'storescp -su "" -od "' + configuration + '" ' + client_port
        subprocess.Popen(start_store, shell=True)
        session['storage_running'] = True

    return {'store_status': session['storage_running']}


@bp.route('/_store_stream', methods=['GET'])
def _store_stream():
    if 'storage_running' not in session:
        session['storage_running'] = False

    if session['storage_running']:
        # return stream from store process here
        pass
    else:
        return jsonify({})


@bp.route('/_store_status', methods=['GET'])
def _store_status():
    storage_status = False
    if 'storage_running' in session:
        if session['storage_running']:
            storage_status = True
    return {'store_status': storage_status}





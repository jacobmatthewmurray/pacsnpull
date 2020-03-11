import os
import csv
import json
import io
import subprocess
import datetime
import time
import click
from itertools import zip_longest
from datetime import datetime
from flask import (Blueprint, render_template, request, session, jsonify, current_app)
from app.dicomconnector import Mover
from app.forms import ConfigurationForm

from urllib import parse

bp = Blueprint('dicomconnect', __name__, url_prefix='/dicomconnect', cli_group=None)

global current_query_status


@bp.route('/', methods=['GET'])
def index(): return render_template('/dicomconnect/index.html')


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

        with open(os.path.join(current_app.instance_path, 'qry', filename), 'w') as json_file:
            json.dump(data, json_file)

        session['current_query_file'] = filename

        return jsonify(data)

    elif request.method == 'GET':

        if 'current_query_file' not in session:
            return jsonify({})
        else:
            with open(os.path.join(current_app.instance_path, 'qry', session['current_query_file'])) as json_file:
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

    with open(os.path.join(current_app.instance_path, 'qry', filename + '.json'), 'w') as json_file:
        json.dump(request.json, json_file)

    save_csv_response(pacsnpull_json_to_csv(request.json),
                      os.path.join(current_app.instance_path, 'qry', filename + '.csv'))

    return 'success: json file saved'


@bp.route('/_echo', methods=['GET'])
def _echo():
    configuration = decode_configuration(request.args)
    response = echo(configuration)
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
        store_path = os.path.join(current_app.instance_path, 'dcm')
        client_port = str(session['configuration']['client_port'])
        err_log_path = os.path.join(current_app.instance_path, 'log', 'store_err_' + timestamp() + '.log')
        out_log_path = os.path.join(current_app.instance_path, 'log', 'store_out_' + timestamp() + '.log')
        start_store = 'storescp -su "" -ll INFO -od "' + store_path + '" ' + client_port

        with open(out_log_path, 'a') as out, open(err_log_path, 'a') as err:
            subprocess.Popen(start_store, shell=True, stderr=err, stdout=out)

        session['storage_running'] = True

    return {'store_status': session['storage_running']}


@bp.route('/_store_status', methods=['GET'])
def _store_status():
    storage_status = False
    if 'storage_running' in session:
        if session['storage_running']:
            storage_status = True
    return {'store_status': storage_status}


def decode_configuration(configuration_multidict):
    configuration = {}
    for key in request.args:
        configuration[key] = configuration_multidict[key] if 'port' not in key else int(configuration_multidict[key])
    return configuration

def timestamp():
    return datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")


def pacsnpull_json_to_csv(pacsnpull_json):
    out = []
    query_id = pacsnpull_json['query_id']
    query = {}
    for key in pacsnpull_json['query']:
        query['query_' + key] = pacsnpull_json['query'][key]

    for i, (j, k) in enumerate(zip_longest(pacsnpull_json['query_response']['status'],
                                           pacsnpull_json['query_response']['data'], fillvalue={})):
        query_responses = {**j, **k}
        query_responses_new = {}
        for key in query_responses:
            query_responses_new['query_response_'+key] = query_responses[key]
        out.append({'query_id': query_id, **query, 'query_response_id': i, **query_responses_new})

    return out


def save_csv_response(list_of_dicts, destination_file):
    global current_query_status
    query_count = current_query_status[1] if current_query_status else 0

    with open(destination_file, 'a') as file:
        dict_writer = csv.DictWriter(file, list_of_dicts[0].keys())
        if query_count == 0:
            dict_writer.writeheader()
        dict_writer.writerows(list_of_dicts)


def store_status():
    process = subprocess.run(['pidof', 'storescp'], capture_output=True, text=True)
    return process.stdout.strip('\n')


def toggle_store(configuration):
    pid = store_status()
    if pid:
        subprocess.run(['kill',  pid])
    else:
        log_path = configuration['log_path']
        dcm_path = configuration['dcm_path']
        client_port = str(configuration['client_port'])
        log_level = configuration['log_level'] if 'log_level' in configuration else 'INFO'
        log_file = os.path.join(log_path, 'storescp_{}_' + timestamp() + '.log')

        cmd = 'storescp -su "" -ll ' + log_level + ' -od "' + dcm_path + '" ' + client_port

        with open(log_file.format('out'), 'a') as out, open(log_file.format('err'), 'a') as err:
            subprocess.Popen(cmd, shell=True, stderr=err, stdout=out)


def echo(configuration):
    connector = Mover(configuration)
    response = connector.send_c_echo()
    connector.assoc.release()
    return response


def query(configuration, queries, query_type):
    valid_query_type = ['find', 'move']
    assert query_type in valid_query_type, ValueError('query type must be in {}'.format(valid_query_type))

    global current_query_status
    start_time = datetime.now()
    current_query_status = (query_type, 0, len(queries), start_time, datetime.now(), 0)
    destination_file = os.path.join(configuration['qry_path'], query_type + '_' + timestamp() + '.csv')

    for i, q in enumerate(queries):
        connector = Mover(configuration)
        if query_type == 'find':
            responses = connector.send_c_find(q)
        elif query_type == 'move':
            responses = connector.send_c_move(q)
        else:
            responses = {}
        connector.assoc.release()
        csv_response = pacsnpull_json_to_csv({'query_id': i, 'query': q, 'query_response': responses})
        save_csv_response(csv_response, destination_file)

        current_query_status = (query_type, i+1, len(queries), start_time, datetime.now(),
                                datetime.now() - current_query_status[4])

        print_query_status()


def print_query_status():
    global current_query_status
    query_type, current_query, total_queries, start, current_time, diff_to_last = current_query_status
    print_string = f"""
    {'*'*80}
    # CURRENT QUERY STATUS
    # {'-'*78}
    # Query type: {query_type}
    # Current query count: {current_query}
    # Total query count: {total_queries}
    # Percent complete: {(current_query)/total_queries * 100}%
    # Start time: {start}
    # Current time: {current_time}
    # Run time of last query: {diff_to_last}
    {'*'*80}
    """
    print(print_string)





def json_load(path):
    with open(path) as file:
        data = json.load(file)
    return data


@bp.cli.command('echo')
@click.argument('configuration_file_path', type=click.Path(exists=True))
def click_echo(configuration_file_path):
    print(echo(json_load(configuration_file_path)))


@bp.cli.command('find')
@click.argument('configuration_file_path', type=click.Path(exists=True))
@click.argument('query_file_path', type=click.Path(exists=True))
def click_find(configuration_file_path, query_file_path):
    configuration = json_load(configuration_file_path)
    queries = json_load(query_file_path)
    query(configuration, queries, 'find')


@bp.cli.command('move')
@click.argument('configuration_file_path', type=click.Path(exists=True))
@click.argument('query_file_path', type=click.Path(exists=True))
@click.option('--store/--no-store', default=True)
@click.option('--storelife', default=10)
def click_find(configuration_file_path, query_file_path, store, storelife):
    configuration = json_load(configuration_file_path)
    queries = json_load(query_file_path)
    if store:
        toggle_store(configuration)
        query(configuration, queries, 'move')
        time.sleep(storelife)
        toggle_store(configuration)
    else:
        query(configuration, queries, 'move')



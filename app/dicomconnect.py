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
from flask import (Blueprint, render_template, request, session, jsonify, current_app, Response)
from app.dicomconnector import Mover
from app.forms import ConfigurationForm


bp = Blueprint('dicomconnect', __name__, url_prefix='/dicomconnect', cli_group=None)


@bp.route('/', methods=['GET'])
def index(): return render_template('/dicomconnect/index.html')


@bp.route('/overview', methods=['GET'])
def overview(): return render_template('/dicomconnect/overview.html', config_form=ConfigurationForm())


@bp.route('/_query_load', methods=['GET', 'POST'])
def _query_load():
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            data = json.load(io.BytesIO(file.stream.read()))
            return jsonify(data)
    else:
        return Response(status=400)


@bp.route('/_save_json', methods=['POST'])
def _save_json():
    if 'filename' not in request.headers:
        return 'error: no filename provided'

    filename = request.headers['filename']

    with open(os.path.join(current_app.instance_path, 'qry', filename + '.json'), 'w') as json_file:
        json.dump(request.json, json_file)

    return Response(status=200)


@bp.route('/_echo', methods=['GET'])
def _echo():
    configuration = decode_configuration(request.args)
    response = echo(configuration)
    return 'Status Code: {}, Status Category: {}'.format(response['status']['code'], response['status']['category'])


@bp.route('/_query', methods=['POST'])
def _query():
    query_data = request.get_json()
    configuration = decode_configuration(query_data['configuration'])
    queries = query_data['query']
    cqs = query_data['cqs']
    query_type = cqs['query_type']
    responses = query(configuration, queries, query_type, cqs)
    return jsonify(responses)


@bp.route('/_store', methods=['GET'])
def _toggle_store():
    toggle_store(decode_configuration(request.args))
    storage_status = True if store_status() else False
    return {'store_status': storage_status}


@bp.route('/_store_status', methods=['GET'])
def _store_status():
    storage_status = True if store_status() else False
    return {'store_status': storage_status}


def toggle_store(configuration):
    pid = store_status()
    if pid:
        subprocess.run(['kill',  pid])
    else:
        log_path = os.path.join(current_app.instance_path, 'log')
        dcm_path = os.path.join(current_app.instance_path, 'dcm')
        client_port = str(configuration['client_port'])
        log_level = configuration['log_level'] if 'log_level' in configuration else 'INFO'
        log_file = os.path.join(log_path, 'storescp_{}_' + timestamp() + '.log')

        cmd = 'storescp -su "" -ll ' + log_level + ' -od "' + dcm_path + '" ' + client_port

        with open(log_file.format('out'), 'a') as out, open(log_file.format('err'), 'a') as err:
            subprocess.Popen(cmd, shell=True, stderr=err, stdout=out)


def store_status():
    process = subprocess.run(['pidof', 'storescp'], capture_output=True, text=True)
    return process.stdout.strip('\n')


def echo(configuration):
    connector = Mover(configuration)
    response = connector.send_c_echo()
    connector.assoc.release()
    return response


def query(configuration, queries, query_type, cqs=None):

    # check validity of inputs
    valid_query_type = ['find', 'move']
    assert query_type in valid_query_type, ValueError('query type must be in {}'.format(valid_query_type))

    if not cqs:
        cqs = {
            'query_type': query_type,
            'current_query': 0,
            'total_queries': len(queries),
            'start_time': datetime.now(),
            'diff_to_last': 0,
            'filename': query_type + '_' + timestamp()
        }

    cqs['current_time'] = datetime.now()
    destination_file = os.path.join(current_app.instance_path, 'qry', cqs['filename'] + '.csv')

    responses_to_return = []

    for q in queries:
        connector = Mover(configuration)
        if query_type == 'find':
            responses = connector.send_c_find(q)
        elif query_type == 'move':
            responses = connector.send_c_move(q)
        else:
            responses = {}
        connector.assoc.release()

        # append to responses
        responses_to_return.append(responses)

        # save to csv
        augmented_query_response = {'query_id': cqs['current_query'], 'query': q, 'query_response': responses}
        csv_response = pacsnpull_json_to_csv(augmented_query_response)
        save_csv_response(csv_response, destination_file, cqs)

        # update status
        cqs['current_query'] = cqs['current_query'] + 1
        cqs['diff_to_last'] = datetime.now() - cqs['current_time']
        cqs['current_time'] = datetime.now()

        print_query_status(cqs)

    return responses_to_return


# Helper functions
def print_query_status(cqs):

    print_string = f"""
    {'*'*80}
    # CURRENT QUERY STATUS
    # {'-'*78}
    # Query type: {cqs['query_type']}
    # Current query count: {cqs['current_query']}
    # Total query count: {cqs['total_queries']}
    # Percent complete: {cqs['current_query']/cqs['current_query'] * 100}%
    # Start time: {cqs['start_time']}
    # Current time: {cqs['current_time']}
    # Run time of last query: {cqs['diff_to_last']}
    {'*'*80}
    """
    print(print_string)


def json_load(path):
    with open(path) as file:
        data = json.load(file)
    return data


def decode_configuration(configuration_multidict):
    configuration = {}
    for key in configuration_multidict:
        if 'port' in key:
            configuration[key] = int(configuration_multidict[key])
        elif 'break' in key:
            configuration[key] = int(configuration_multidict[key])
        else:
            configuration[key] = configuration_multidict[key]
    return configuration


def timestamp():
    return datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")


def save_csv_response(list_of_dicts, destination_file, cqs):

    with open(destination_file, 'a') as file:
        dict_writer = csv.DictWriter(file, list_of_dicts[0].keys())
        if cqs['current_query'] == 0:
            dict_writer.writeheader()
        dict_writer.writerows(list_of_dicts)


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


# Command line functions
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

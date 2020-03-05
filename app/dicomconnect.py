import json
from flask import (
        Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
        )

from app.db import get_db
from app.dicomconnector import Mover
from app.forms import NewPNPForm, ConfigurationForm, BasicStudySearchForm

bp = Blueprint('dicomconnect', __name__, url_prefix='/dicomconnect')


@bp.route('/new', methods=['GET', 'POST'])
def new_pnp():
    form = NewPNPForm()
    if request.method == 'POST':
        pnp_title = request.form['title']
        db = get_db()
        error = None

        if not pnp_title:
            error = 'Project name is required.'
        elif db.execute(
            'SELECT pnp_id FROM pnp WHERE title = ?', (pnp_title,)
        ).fetchone() is not None:
            error = 'Project {} already exists.'.format(pnp_title)
        if error is None:

            db.execute(
                'INSERT INTO pnp (title) VALUES (?)', (pnp_title,)
            )
            db.commit()

            pnp_id = db.execute(
                'SELECT pnp_id FROM pnp WHERE title = ?', (pnp_title,)
            ).fetchone()['pnp_id']
            session['pnp_id'] = pnp_id

            return redirect(url_for('dicomconnect.new_config'))

        flash(error)

    return render_template('dicomconnect/new.html', form=form)


@bp.route('/config', methods=['GET', 'POST'])
def new_config():
    form = ConfigurationForm()
    if form.validate_on_submit():

        fields = ('pnp_id',)
        values = (session['pnp_id'],)
        question_marks = ('?',)

        for field, value in form.data.items():
            if field not in ['submit', 'csrf_token']:
                fields += (field,)
                values += (value,)
                question_marks += ('?',)

        db = get_db()

        db.execute(
            'INSERT INTO configuration ('+','.join(fields)+') VALUES ('+','.join(question_marks)+')', values
        )
        db.commit()

        return redirect(url_for('dicomconnect.search'))

    return render_template('dicomconnect/config.html', form=form)


@bp.route('/search', methods=['GET', 'POST'])
def search():
    form = BasicStudySearchForm()
    db = get_db()

    if form.validate_on_submit():

        fields = ('pnp_id',)
        values = (session['pnp_id'],)
        question_marks = ('?',)

        for field, value in form.data.items():
            if field not in ['submit', 'csrf_token']:
                fields += (field,)
                values += (value,)
                question_marks += ('?',)

        db.execute(
            'INSERT INTO basic_study_search (' + ','.join(fields) + ') VALUES (' + ','.join(question_marks) + ')', values
        )
        db.commit()

    basic_search = db.execute('SELECT * FROM basic_study_search ORDER BY patient_name').fetchall()

    return render_template('dicomconnect/search.html', form=form, basic_search=basic_search)


def pacsify_variable(variable):

    pacs_variable = ''.join([x.capitalize() for x in variable.split('_')])
    pacs_variable = pacs_variable.replace('Id', 'ID').replace('Uid', 'UID')

    return pacs_variable


def depacsify_variable(pacs_variable):
    final = ''
    variable = pacs_variable.replace('UID', 'Uid').replace('ID', 'Id')
    for i, v in enumerate(variable):
        if v.isupper():
            if i != 0:
                final += '_'
            final += v.lower()
        else:
            final += v
    return final


@bp.route('/find', methods=['GET'])
def find():
    db = get_db()
    configuration = db.execute('SELECT * FROM configuration WHERE pnp_id = ?', (session['pnp_id'],)).fetchone()
    searches = db.execute('SELECT * FROM basic_study_search').fetchall()

    for search in searches:
        connector = Mover(configuration)
        qry = dict()
        for key, val in search:
            if key not in ['basic_study_search_id', 'pnp_id']:
                pacs_key = pacsify_variable(key)
                qry[pacs_key] = val

        responses = connector.send_c_find(qry)







def dcm_find():

    # These elements will come from configuration files and from query file

    configuration = {
        "network": {
            'host_ip': '127.0.0.1',
            'host_port': 4242,
            'client_name': 'localStore',
            'client_ip': '',
            'client_port': 2000,
        },
        "storage_path": {
            "dcm": "",
            "logs": ""
        },
        "query_model": 'S',
        "query_break_count": 10
    }

    qry = {
        'QueryRetrieveLevel': 'SERIES',
        'StudyInstanceUID': '*',
        'PatientName': '1579bb13abec8e5492249dd317f1a93d41b8ce084860cdbed5a394fd',
        'SeriesInstanceUID': '*'
    }

    connector = Mover(configuration)
    find_response = connector.send_c_find(qry)

    return jsonify(find_response)

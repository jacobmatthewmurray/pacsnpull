from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired


class ConfigurationForm(FlaskForm):
    host_ip = StringField('host ip', default='127.0.0.1')
    host_port = IntegerField('host port', default=4242)
    client_name = StringField('client name', default='STORESCP')
    client_ip = StringField('client ip')
    client_port = IntegerField('client port', default=2000)
    dcm_storage_path = StringField('dcm storage path', default='/home/jacob/storedir/')
    log_storage_path = StringField('log storage path', default='/home/jacob/storedir/')
    query_model = StringField('query model', default='S')
    query_break_count = IntegerField('query break count', default=10)
    submit = SubmitField('submit')

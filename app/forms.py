from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired


class ConfigurationForm(FlaskForm):
    host_ip = StringField('Host IP', default='127.0.0.1')
    host_port = IntegerField('Host Port', default=4242)
    client_name = StringField('Client Name', default='STORESCP')
    client_ip = StringField('Client IP')
    client_port = IntegerField('Client Port', default=2000)
    dcm_storage_path = StringField('DCM Storage Path', default='/home/jacob/storedir/')
    log_storage_path = StringField('Log Storage Path', default='/home/jacob/storedir/')
    query_model = StringField('Query Model', default='S')
    query_break_count = IntegerField('Query Break Count', default=10)
    submit = SubmitField('Create')

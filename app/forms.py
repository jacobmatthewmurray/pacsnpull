from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired


class ConfigurationForm(FlaskForm):
    host_ip = StringField('host ip', default='127.0.0.1')
    host_port = IntegerField('host port', default=4242)
    client_name = StringField('client name', default='STORESCP')
    client_ip = StringField('client ip')
    client_port = IntegerField('client port', default=2000)
    query_model = StringField('query model', default='S')
    query_break_count = IntegerField('query break count', default=10)
    submit = SubmitField('submit')

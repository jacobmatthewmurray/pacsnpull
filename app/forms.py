from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired


class NewPNPForm(FlaskForm):
    title = StringField('New PACS n PULL Project', validators=[DataRequired()])
    submit = SubmitField('Create')


class ConfigurationForm(FlaskForm):
    host_ip = StringField('Host IP', validators=[DataRequired()])
    host_port = IntegerField('Host Port', validators=[DataRequired()])
    client_name = StringField('Client Name', validators=[DataRequired()])
    client_ip = StringField('Client IP')
    client_port = IntegerField('Client Port', validators=[DataRequired()])
    dcm_storage_path = StringField('DCM Storage Path', validators=[DataRequired()])
    log_storage_path = StringField('Log Storage Path', validators=[DataRequired()])
    query_model = StringField('Query Model', default='S', validators=[DataRequired()])
    query_break_count = IntegerField('Query Break Count', default=10, validators=[DataRequired()])
    submit = SubmitField('Create')


class BasicStudySearchForm(FlaskForm):

    query_retrieve_level = StringField('QueryRetrieveLevel', default='STUDY')

    patient_name = StringField('PatientName')
    patient_id = StringField('PatientID')
    patient_birth_date = StringField('PatientBirthDate')

    study_instance_uid = StringField('StudyInstanceUID')
    study_description = StringField('StudyDescription')
    study_date = StringField('StudyField')
    study_id = StringField('StudyID')

    modality = StringField('Modality')

    submit = SubmitField('Create')


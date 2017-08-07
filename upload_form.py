import imghdr
from flask import session
from flask.ext.wtf import Form
from jinja2 import Markup, escape
from wtforms.ext.csrf.fields import CSRFTokenField
from wtforms import FileField, SubmitField, ValidationError

class UploadForm(Form):
    image_file = FileField('Image file')
    submit = SubmitField('Submit')

    csrf_token = CSRFTokenField()

    def hidden_tag(self, *fields):
        html = super(UploadForm, self).hidden_tag(*fields)
        tag = Markup(u'<input id="_csrf_token" name="_csrf_token"'
                     u'type="hidden" value="%s">') % self.csrf_token.current_token
        return html[:-6] + tag + html[-6:]

    def generate_csrf_token(self, csrf_context=None):
        if not self.csrf_enabled:
            return
        self.csrf_token.current_token = session.get('_csrf_token')
        return self.csrf_token.current_token

    def validate_csrf_token(self, field):
        if field.current_token != field.data:
            return ValidationError(field.gettext('Invalid CSRF Token'))

    def validate_image_file(self, field):
        if field.data.filename[-4:].lower() != '.jpg':
            raise ValidationError('Invalid file extension')
        if imghdr.what(field.data) != 'jpeg':
            raise ValidationError('Invalid image format')

from __future__ import unicode_literals
from pygrowup.exceptions import InvalidMeasurement

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

from nutrition.forms import CreateReportForm
from nutrition.handlers.base import NutritionPrefixMixin


class CreateReportHandler(NutritionPrefixMixin, KeywordHandler):
    keyword = 'report'
    form_class = CreateReportForm

    # The tokens, in order, which will be parsed from the message text.
    token_names = ['patient_id', 'weight', 'height', 'muac', 'oedema']

    help_text = 'To create a nutrition report, send: {prefix} {keyword} '\
            '<patient_id> <weight in kg> <height in cm> <muac in cm> <oedema '\
            '(Y/N)>'
    success_text = 'Thanks {reporter}. Nutrition update for {patient} '\
            '({patient_id}):\nweight: {weight} kg\nheight: {height} cm\n'\
            'muac: {muac} cm\noedema: {oedema}'
    error_text = 'Sorry, an unexpected error occurred while processing '\
            'your report. Please contact your administrator if this '\
            'continues to occur.'
    format_error_text = 'Sorry, the system could not understand your report. '
    invalid_measurement_text = 'Sorry, one of your measurements is invalid: '\
            '{message}'
    form_error_text = 'Sorry, an error occurred while processing your '\
            'message: {message}'

    def _get_form(self, data):
        return self.form_class(data, connection=self.connection)

    def _parse(self, text):
        """Tokenize message text."""
        result = {}
        tokens = text.strip().split()
        for name in self.token_names:
            try:
                result[name] = tokens.pop(0)
            except IndexError:
                raise ValueError('Received too few tokens')
        if tokens:
            raise ValueError('Received too many tokens')
        return result

    @property
    def _success_text(self):
        """Fill in success text with data about the created report."""
        data = self.report.indicators
        data['reporter'] = 'placeholder'  # TODO
        data['patient'] = self.report.patient['name']
        data['patient_id'] = self.report.patient_id
        return self.success_text.format(**data)

    def handle(self, text):
        # The reporter determined from the message connection.
        self.connection = self.msg.connection
        self.debug('Received report message from {0}'.format(self.connection))

        # Parse the message into its components.
        try:
            parsed = self._parse(text)
        except ValueError as e:
            # Incorrect number of tokens.
            self.exception()
            self.respond(self.format_error_text + self._help_text)
            return
        else:
            data = ', '.join([': '.join((k, v)) for k, v in parsed.items()])
            self.debug('Parsed report data: {0}'.format(data))

        # Validate the components using a form.
        form = self._get_form(parsed)
        if not form.is_valid():
            data = {'message': form.error}
            self.debug('Form error: {message}'.format(**data))
            self.respond(self.form_error_text.format(**data))
            return

        # Create the new report.
        try:
            self.report = form.save()
            self.report.analyze()  # Calculates z-scores and re-saves.
        except InvalidMeasurement as e:
            # This may be thrown by pygrowup when calculating z-scores if
            # the measurements provided are beyond reasonable limits.
            self.exception()
            data = {'message': str(e)}
            self.respond(self.invalid_measurement_text.format(**data))
            return
        except Exception as e:
            self.error('An unexpected error occurred')
            self.exception()
            self.respond(self.error_text)
            return
        else:
            # Send a success message to the reporter.
            self.debug('Successfully created a new report!')
            self.respond(self._success_text)

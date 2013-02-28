from __future__ import unicode_literals

from pygrowup.exceptions import InvalidMeasurement

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

from nutrition.handlers.base import NutritionPrefixMixin
from nutrition.forms import CreateReportForm


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
        for i in range(len(tokens)):
            result[self.token_names[i]] = tokens.pop(0)
        return result

    @property
    def _success_text(self):
        """Fill in success text with data about the created report."""
        data = self.report.indicators
        data['reporter'] = 'placeholder'  # TODO
        data['patient'] = report.patient['name']
        data['patient_id'] = report.patient_id
        return self.success_text.format(**data)

    def handle(self, text):
        # The reporting health worker is determined from the message
        # connection.
        self.connection = self.msg.connection
        self.debug('Received report message from {0}'.format(self.connection))

        parsed = self._parse(text)
        data = ', '.join([': '.join((k, v)) for k, v in parsed.iteritems()])
        self.debug('Parsed report data: {0}'.format(data))

        # Check for incorrect length early in order to provide a more helpful
        # error message.
        count = len(parsed)
        correct = len(self.token_names)
        if count != correct:
            args = (count, correct)
            self.debug('Incorrect number of tokens: {0}/{1}'.format(*args))
            self.respond(self.format_error_text + self._help_text)
            return

        form = self._get_form(parsed)
        if not form.is_valid():
            data = {'message': form.error}
            self.debug('Form error: {message}'.format(**data))
            self.respond(self.form_error_text.format(**data))
            return

        try:
            self.report = form.save()
            self.report.analyze()  # Calculate z-scores and re-save.
        except InvalidMeasurement as e:
            # This may be thrown by pygrowup when calculating z-scores if
            # the measurements provided are beyond reasonable limits.
            self.exception()
            data = {'message': e.message}
            self.respond(self.invalid_measurement_text.format(**data))
            return

        # Send a success message to the reporter.
        self.debug('Successfully created a new report!')
        self.respond(self._success_text)

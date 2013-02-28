from __future__ import unicode_literals

from pygrowup.exceptions import InvalidMeasurement

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

from nutrition.handlers.base import NutritionPrefixMixin
from nutrition.forms import CreateReportForm


class CreateReportHandler(NutritionPrefixMixin, KeywordHandler):
    keyword = 'report'

    # The tokens, in order, which will be parsed from the message text.
    token_names = ['patient_id', 'weight', 'height', 'muac', 'oedema']

    help_text = 'To create a nutrition report, send: {prefix} {keyword} '\
            '<patient_id> <weight in kg> <height in cm> <muac in cm> <oedema (Y/N)>'
    success_text = 'Thanks {reporter}. Nutrition update for {patient} '\
            '({patient_id}):\nweight: {weight} kg\nheight: {height} cm\n'\
            'muac: {muac} cm\noedema: {oedema}'
    format_error_text = 'Sorry, the system could not understand your report. '
    invalid_measurement_text = 'Sorry, one of your measurements is invalid: '\
            '{message}'


    def _parse(self, text):
        """Tokenize message text."""
        result = {}
        tokens = text.strip().split()
        for i in range(len(tokens)):
            result[self.token_names[i]] = tokens.pop(0)
        return result

    def handle(self, text):
        # The reporting health worker is determined from the message
        # connection.
        connection = self.msg.connection
        self.debug('Received report message from {0}'.format(connection))

        parsed = self._parse(text)
        self.debug('Parsed report data: {0}'.format(
                ', '.join([': '.join((k, v)) for k, v in parsed.iteritems()])))

        # Check for incorrect length early in order to provide a more helpful
        # error message.
        count = len(parsed)
        correct = len(self.token_names)
        if count != correct:
            self.debug('Incorrect number of tokens: {0}/{1}'.format(count, correct))
            self.respond(self.format_error_text + self._help_text)
            return

        form = CreateReportForm(parsed, connection=connection)
        if not form.is_valid():
            error = form.error
            self.debug('Form error: {0}'.format(error))
            self.respond(error)
            return

        try:
            report = form.save()
            report.analyze()  # Calculate z-scores and re-save.
        except InvalidMeasurement as e:
            self.exception()
            data = {'message': e.message}
            self.respond(self.invalid_measurement_text.format(**data))
            return

        self.debug('Successfully created a new report!')

        data = report.indicators
        data['reporter'] = 'placeholder'  # TODO
        data['patient'] = report.patient['name']
        data['patient_id'] = report.patient_id
        success = self.success_text.format(**data)
        self.respond(success)

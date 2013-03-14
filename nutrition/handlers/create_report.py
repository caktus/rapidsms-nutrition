from __future__ import unicode_literals
from pygrowup.exceptions import InvalidMeasurement

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

from nutrition.forms import CreateReportForm
from nutrition.handlers.base import NutritionHandlerBase


class CreateReportHandler(NutritionHandlerBase, KeywordHandler):
    keyword = 'report'
    form_class = CreateReportForm

    # We accept messages in the format:
    #   NUTRITION REPORT patient_id indicator1 value1 indicator2 value2 [...]
    # By using indicator names, the user need not remember an order by
    # which to send measurements, and can skip unknown information.
    _HEIGHT = 'height'
    _WEIGHT = 'weight'
    _MUAC = 'muac'
    _OEDEMA = 'oedema'
    indicators = {  # Associate canonical names with an indicator.
        'height': _HEIGHT, 'ht': _HEIGHT, 'h': _HEIGHT,
        'weight': _WEIGHT, 'wt': _WEIGHT, 'w': _WEIGHT,
        'muac': _MUAC, 'm': _MUAC,
        'oedema': _OEDEMA, 'o': _OEDEMA,
    }

    messages = {
        'help': 'To create a nutrition report, send: {prefix} {keyword} '\
                '<patient_id> H <height (cm)> W <weight (kg)> M <muac (cm)> '\
                'O <oedema (Y/N>',

        'success': 'Thanks {reporter}. Nutrition report for {patient} '\
                '({patient_id}):\nweight: {weight} kg\nheight: {height} cm\n'\
                'muac: {muac} cm\noedema: {oedema}',

        'format_error': 'Sorry, the system could not understand your report. '\
                'To create a nutrition report, send: {prefix} {keyword} '\
                '<patient_id> H <height (cm)> W <weight (kg)> M <muac (cm)> '\
                'O <oedema (Y/N>',

        'invalid_measurement': 'Sorry, one of your measurements is invalid: '\
                '{message}',

        'form_error': 'Sorry, an error occurred while processing your '\
                'message: {message}',

        'error': 'Sorry, an unexpected error occurred while processing '\
                'your report. Please contact your administrator if this '\
                'continues to occur.',
    }

    def _parse(self, text):
        """Tokenize message text."""
        # Must have one token for patient identifier + 2 for each indicator.
        tokens = text.split()
        if len(tokens) % 2 != 1:
            raise ValueError('Wrong number of tokens.')
        result = {}

        # The first token is interpreted as the patient identifier.
        result['patient_id'] = tokens.pop(0)

        # Each two of the remaining tokens are interpreted as
        # indicator name + value.
        while len(tokens):
            name = tokens.pop(0).lower()
            val = tokens.pop(0)
            if name not in self.indicators:
                raise ValueError('Unrecognized indicator.')
            indicator = self.indicators.get(name)
            if indicator in result:
                raise ValueError('Duplicate indicator.')
            result[indicator] = val

        return result

    def _process(self, parsed):
        # Validate the parsed data using a form.
        form = self._get_form(parsed)
        if not form.is_valid():
            data = {'message': form.error}
            self.debug('Form error: {message}'.format(**data))
            self._respond('form_error', **data)
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
            self._respond('invalid_measurement', **data)
            return
        except Exception as e:
            self.error('An unexpected error occurred')
            self.exception()
            self._respond('error')
            return
        else:
            # Send a success message to the reporter.
            self.debug('Successfully created a new report!')
            data = self.report.indicators
            if self.report.reporter:
                data['reporter'] = self.report.reporter.get('name', '')
            else:
                data['reporter'] = 'anonymous'  # TODO
            data['patient'] = self.report.patient.get('name', '')
            data['patient_id'] = self.report.patient_id
            self._respond('success', **data)

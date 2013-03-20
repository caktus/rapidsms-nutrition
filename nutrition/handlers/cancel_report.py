from __future__ import unicode_literals

from rapidsms.contrib.handlers import KeywordHandler

from nutrition.forms import CancelReportForm
from nutrition.models import Report
from nutrition.handlers.base import NutritionHandlerBase


__all__ = ['CancelReportHandler']


class CancelReportHandler(NutritionHandlerBase, KeywordHandler):
    keyword = 'cancel'
    form_class = CancelReportForm

    _messages = {
        'help': 'To cancel the most recent nutrition report, send: {prefix} '\
                '{keyword} <patient_id>',

        'success': 'Thanks {reporter}. The most recent nutrition report for '\
                '{patient} ({patient_id}) has been cancelled.',

        'no_report': 'Sorry, {patient_id} does not have any reports in the '\
                'system.',

        'format_error': 'Sorry, the system could not understand whose report '\
                'you would like to cancel. To cancel the most recent '\
                'nutrition report, send: {prefix} {keyword} <patient_id>',
    }

    def _parse(self, raw_text):
        """Tokenize message text."""
        tokens = raw_text.split()
        if len(tokens) != 1:
            raise ValueError('Only one token should be specified.')
        return {'patient_id': tokens[0]}

    def _process(self, parsed):
        # Validate the parsed data using a form.
        form = self._get_form(parsed)
        if not form.is_valid():
            data = {'message': form.error}
            self.debug('Form error: {message}'.format(**data))
            self._respond('form_error', **data)
            return

        # Cancel the most recent report.
        try:
            self.report = form.cancel()
        except Report.DoesNotExist:
            self.exception()
            data = {'patient_id': form.cleaned_data['patient_id']}
            self._respond('no_report', **data)
        except Exception as e:
            self.error('An unexpected error occurred')
            self.exception()
            self._respond('error')
        else:
            # Send a success message to the reporter.
            self.debug('Successfully cancelled a report!')
            data = {}
            if form.reporter:  # TODO
                name = form.reporter.get('name', '')
                data['reporter'] = name or form.reporter['id']
            else:
                data['reporter'] = 'anonymous'
            data['patient'] = form.patient.get('name', '')
            data['patient_id'] = form.patient['id']
            self._respond('success', **data)

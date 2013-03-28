from __future__ import unicode_literals
import logging

from django.utils.translation import ugettext_lazy as _

from rapidsms.contrib.handlers import KeywordHandler

from nutrition.forms import CancelReportForm
from nutrition.models import Report
from nutrition.handlers.base import NutritionHandlerBase


__all__ = ['CancelReportHandler']


logger = logging.getLogger(__name__)


class CancelReportHandler(NutritionHandlerBase, KeywordHandler):
    keyword = 'cancel'
    form_class = CancelReportForm

    _messages = {
        'help': _('To cancel the most recent nutrition report, send: {prefix} '
                '{keyword} <patient_id>'),

        'success': _('Thanks {reporter}. The most recent nutrition report for '
                '{patient} ({patient_id}) has been cancelled.'),

        'no_report': _('Sorry, you have not made any reports for '
                '{patient_id}.'),

        'format_error': _('Sorry, the system could not understand whose '
                'report you would like to cancel. To cancel the most recent '
                'nutrition report, send: {prefix} {keyword} <patient_id>'),
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
            logger.error('Form error: {message}'.format(**data))
            self._respond('form_error', **data)
            return

        # Cancel the most recent report.
        try:
            self.report = form.cancel()
        except Report.DoesNotExist:
            logger.exception('There is no report to cancel')
            data = {'patient_id': form.cleaned_data['patient_id']}
            self._respond('no_report', **data)
        except Exception as e:
            logger.exception('An unexpected processing error occurred')
            self._respond('error')
        else:
            # Send a success message to the reporter.
            logger.debug('Successfully cancelled a report!')
            data = {}
            if self.report.reporter_connection:
                data['reporter'] = self.report.reporter_connection.contact
            else:
                data['reporter'] = 'Anonymous'
            data['patient'] = form.patient.get('name', '')
            data['patient_id'] = form.patient['id']
            self._respond('success', **data)

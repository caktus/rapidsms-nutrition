from __future__ import unicode_literals
import datetime
from decimal import Decimal
import mock
from pygrowup.exceptions import InvalidMeasurement

from rapidsms.messages import IncomingMessage
from rapidsms.tests.harness import RapidTest

from healthcare.api import client

from ..handlers.create_report import CreateReportHandler
from ..models import Report, HEALTHCARE_SOURCE


__all__ = ['CreateReportHandlerTest']


class CreateReportHandlerTest(RapidTest):
    """Tests for KeywordHandler to add a nutrition report."""
    Handler = CreateReportHandler

    def setUp(self):
        self.patient_id = 'asdf'
        self.birth_date = datetime.date(2010, 2, 14)
        self.patient = client.patients.create(name='test', sex='M',
                birth_date=self.birth_date)
        client.patients.link(self.patient['id'], self.patient_id,
                HEALTHCARE_SOURCE)

    def _send(self, text):
        return self.Handler.test(text)

    def test_wrong_prefix(self):
        """Handler should not reply to an incorrect prefix."""
        replies = self._send('hello report asdf 10 50 10 Y')
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(replies, False)

    def test_wrong_keyword(self):
        """Handler should not reply to an incorrect keyword."""
        replies = self._send('nutrition hello asdf 10 50 10 Y')
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(replies, False)

    def test_help(self):
        """Prefix + keyword should return help text."""
        replies = self._send('nutrition report')
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('To create a nutrition report, send'))

    def test_too_few_tokens(self):
        """Report message requires prefix, keyword, and 5 arguments."""
        replies = self._send('nutrition report asdf 10 50 10')
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, the system could not '\
                'understand your report.'))

    def test_too_many_tokens(self):
        """Report message requires prefix, keyword, and 5 arguments."""
        replies = self._send('nutrition report asdf 10 50 10 Y extra')
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, the system could not '\
                'understand your report.'))

    def test_unregistered_healthworker(self):
        pass  # TODO

    def test_unregistered_patient(self):
        """Report patient must be registered."""
        replies = self._send('nutrition report fakeid 10 50 10 Y')
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '))
        self.assertTrue('Nutrition reports must be for a patient '\
                'who is registered and active.' in reply)

    def test_negative_weight(self):
        """An error should be sent if reported weight is less than 0."""
        replies = self._send('nutrition report asdf -10 50 10 Y')
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '))
        self.assertTrue('Please send a positive value (in kg) for '\
                'weight.' in reply)

    def test_large_weight(self):
        """An error should be sent if reported weight has >4 digits."""
        replies = self._send('nutrition report asdf 10000 50 10 Y')
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '))
        self.assertTrue('Nutrition report measurements ' in reply)

    def test_specific_weight(self):
        """Reported weight should be rounded to 1 decimal place."""
        replies = self._send('nutrition report asdf 10.55 50 10 Y')
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.get()
        self.assertEqual(report.patient_id, 'asdf')
        self.assertEqual(report.weight, Decimal('10.6'))
        self.assertEqual(report.height, 50)
        self.assertEqual(report.muac, 10)
        self.assertTrue(report.oedema)
        self.assertEqual(report.status, Report.GOOD_STATUS)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Thanks'))

    def test_null_weight(self):
        """Weight should not be a required measurement."""
        replies = self._send('nutrition report asdf x 50 10 Y')
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.get()
        self.assertEqual(report.patient_id, 'asdf')
        self.assertEqual(report.weight, None)
        self.assertEqual(report.height, 50)
        self.assertEqual(report.muac, 10)
        self.assertTrue(report.oedema)
        self.assertEqual(report.status, Report.GOOD_STATUS)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Thanks'))

    def test_negative_height(self):
        """An error should be sent if reported height is less than 0."""
        replies = self._send('nutrition report asdf 10 -50 10 Y')
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '))
        self.assertTrue('Please send a positive value (in cm) for '\
                'height.' in reply)

    def test_large_height(self):
        """An error should be sent if reported height has >4 digits."""
        replies = self._send('nutrition report asdf 10 50000 10 Y')
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '))
        self.assertTrue('Nutrition report measurements ' in reply)

    def test_specific_height(self):
        """Reported height should be rounded to 1 decimal place."""
        replies = self._send('nutrition report asdf 10 50.55 10 Y')
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.get()
        self.assertEqual(report.patient_id, 'asdf')
        self.assertEqual(report.weight, 10)
        self.assertEqual(report.height, Decimal('50.6'))
        self.assertEqual(report.muac, 10)
        self.assertTrue(report.oedema)
        self.assertEqual(report.status, Report.GOOD_STATUS)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Thanks'))

    def test_null_height(self):
        """Height should not be a required measurement."""
        replies = self._send('nutrition report asdf 10 x 10 Y')
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.get()
        self.assertEqual(report.patient_id, 'asdf')
        self.assertEqual(report.weight, 10)
        self.assertEqual(report.height, None)
        self.assertEqual(report.muac, 10)
        self.assertTrue(report.oedema)
        self.assertEqual(report.status, Report.GOOD_STATUS)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Thanks'))

    def test_invalid_measurement(self):
        """An error should be sent if pygrowup deems a measurement invalid."""
        with mock.patch('pygrowup.pygrowup.Calculator.zscore_for_measurement') as method:
            method.side_effect = InvalidMeasurement
            replies = self._send('nutrition report asdf 10 50 10 Y')
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.get()
        self.assertEqual(report.patient_id, 'asdf')
        self.assertEqual(report.weight, 10)
        self.assertEqual(report.height, 50)
        self.assertEqual(report.muac, 10)
        self.assertTrue(report.oedema)
        self.assertEqual(report.status, report.SUSPECT_STATUS)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, one of your measurements '\
                'is invalid: '))

    def test_negative_muac(self):
        """An error should be sent if reported muac is less than 0."""
        replies = self._send('nutrition report asdf 10 50 -10 Y')
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '))
        self.assertTrue('Please send a positive value (in cm) for '\
                'mid-upper arm circumference.' in reply)

    def test_large_muac(self):
        """An error should be sent if reported muac has >4 digits."""
        replies = self._send('nutrition report asdf 10 50 10000 Y')
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '))
        self.assertTrue('Nutrition report measurements ' in reply)

    def test_specific_muac(self):
        """Reported muac should be rounded to one decimal place."""
        replies = self._send('nutrition report asdf 10 50 10.55 Y')
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.get()
        self.assertEqual(report.patient_id, 'asdf')
        self.assertEqual(report.weight, 10)
        self.assertEqual(report.height, 50)
        self.assertEqual(report.muac, Decimal('10.6'))
        self.assertTrue(report.oedema)
        self.assertEqual(report.status, Report.GOOD_STATUS)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Thanks'))

    def test_null_muac(self):
        """Muac should not be a required measurement."""
        replies = self._send('nutrition report asdf 10 50 x Y')
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.get()
        self.assertEqual(report.patient_id, 'asdf')
        self.assertEqual(report.weight, 10)
        self.assertEqual(report.height, 50)
        self.assertEqual(report.muac, None)
        self.assertTrue(report.oedema)
        self.assertEqual(report.status, Report.GOOD_STATUS)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Thanks'))

    def test_invalid_oedema(self):
        """An error should be sent if reported oedema isn't Y/N."""
        replies = self._send('nutrition report asdf 10 50 10 invalid')
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '))
        self.assertTrue('Please send Y or N to indicate whether the patient '\
                'has oedema.' in reply)

    def test_null_oedema(self):
        """Oedema should not be a required measurement."""
        replies = self._send('nutrition report asdf 10 50 10 x')
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.get()
        self.assertEqual(report.patient_id, 'asdf')
        self.assertEqual(report.weight, 10)
        self.assertEqual(report.height, 50)
        self.assertEqual(report.muac, 10)
        self.assertEqual(report.oedema, None)
        self.assertEqual(report.status, Report.GOOD_STATUS)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Thanks'))

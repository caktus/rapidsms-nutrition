from __future__ import unicode_literals
import datetime
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
        self.assertEqual(replies, False)
        self.assertEqual(Report.objects.count(), 0)

    def test_wrong_keyword(self):
        """Handler should not reply to an incorrect keyword."""
        replies = self._send('nutrition hello asdf 10 50 10 Y')
        self.assertEqual(replies, False)
        self.assertEqual(Report.objects.count(), 0)

    def test_help(self):
        """Prefix + keyword should return help text."""
        replies = self._send('nutrition report')
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('To create a nutrition report, send'))

    def test_too_few_tokens(self):
        replies = self._send('nutrition report asdf 10 50 10')
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, the system could not '\
                'understand your report.'))

    def test_too_many_tokens(self):
        replies = self._send('nutrition report asdf 10 50 10 Y extra')
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, the system could not '\
                'understand your report.'))

    def test_unregistered_healthworker(self):
        pass  # TODO

    def test_unregistered_patient(self):
        replies = self._send('nutrition report fakeid 10 50 10 Y')
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '))
        self.assertTrue('Nutrition reports must be for a patient '\
                'who is registered and active.' in reply)

    def test_negative_weight(self):
        replies = self._send('nutrition report asdf -10 50 10 Y')
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '))
        self.assertTrue('Please send a positive decimal (in kg) for '\
                'weight.' in reply)

    def test_null_weight(self):
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

    def test_negative_height(self):
        replies = self._send('nutrition report asdf 10 -50 10 Y')
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '))
        self.assertTrue('Please send a positive decimal (in cm) for '\
                'height.' in reply)

    def test_null_height(self):
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
        replies = self._send('nutrition report asdf 10 50 -10 Y')
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '))
        self.assertTrue('Please send a positive decimal (in cm) for '\
                'mid-upper arm circumference.' in reply)

    def test_null_muac(self):
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
        replies = self._send('nutrition report asdf 10 50 10 invalid')
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '))
        self.assertTrue('Please send Y or N to indicate whether the patient '\
                'has oedema.' in reply)

    def test_null_oedema(self):
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

from __future__ import unicode_literals
import datetime
from decimal import Decimal
import mock
from pygrowup.exceptions import InvalidMeasurement

from rapidsms.messages import IncomingMessage

from healthcare.api import client

from ..handlers.create_report import CreateReportHandler
from ..models import Report
from .base import NutritionTestBase


__all__ = ['CreateReportHandlerTest']


class CreateReportHandlerTest(NutritionTestBase):
    """Tests for KeywordHandler to add a nutrition report."""
    Handler = CreateReportHandler

    def setUp(self):
        super(CreateReportHandlerTest, self).setUp()
        self.patient_id = 'asdf'
        self.patient_id, self.source, self.patient = self.create_patient(
                self.patient_id)

    def _send(self, text):
        return self.Handler.test(text)

    def test_wrong_prefix(self):
        """Handler should not reply to an incorrect prefix."""
        replies = self._send('hello report asdf w 10 h 50 m 10 o Y')
        self.assertEqual(replies, False)
        self.assertEqual(Report.objects.count(), 0)

    def test_wrong_keyword(self):
        """Handler should not reply to an incorrect keyword."""
        replies = self._send('nutrition hello asdf w 10 h 50 m 10 o Y')
        self.assertEqual(replies, False)
        self.assertEqual(Report.objects.count(), 0)

    def test_help(self):
        """Prefix + keyword should return help text."""
        replies = self._send('nutrition report')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('To create a nutrition report, send'),
                reply)
        self.assertEqual(Report.objects.count(), 0)

    def test_even_tokens(self):
        """Report message requires prefix, keyword, and an odd number of tokens"""
        replies = self._send('nutrition report asdf 10')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, the system could not '\
                'understand your report.'), reply)
        self.assertEqual(Report.objects.count(), 0)

    def test_unregistered_reporter(self):
        """Reporter must be registered."""
        pass  # TODO

    def test_inactive_reporter(self):
        """Reporter must be active."""
        pass  # TODO

    def test_unregistered_patient(self):
        """Report patient must be registered."""
        replies = self._send('nutrition report fakeid w 10 h 50 m 10 o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '), reply)
        self.assertTrue('Nutrition reports must be for a patient '\
                'who is registered and active.' in reply, reply)
        self.assertEqual(Report.objects.count(), 0)

    def test_no_birth_date(self):
        """
        When patient birth date is not known, report is created but analysis
        is unsuccessful.
        """
        _, _, another = self.create_patient('another', birth_date=None)
        replies = self._send('nutrition report another w 10 h 50 m 10 o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Thanks'), reply)
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.get()
        self.assertEqual(report.patient_id, 'another')
        self.assertEqual(long(report.global_patient_id), another['id'])
        self.assertEqual(report.weight, 10)
        self.assertEqual(report.height, 50)
        self.assertEqual(report.muac, 10)
        self.assertTrue(report.oedema)
        self.assertEqual(report.status, Report.INCOMPLETE_STATUS)

    def test_no_sex(self):
        """
        When patient sex is not known, report is created but analysis is
        unsuccessful.
        """
        _, _, another, = self.create_patient('another', sex=None)
        replies = self._send('nutrition report another w 10 h 50 m 10 o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Thanks'), reply)
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.get()
        self.assertEqual(report.patient_id, 'another')
        self.assertEqual(long(report.global_patient_id), another['id'])
        self.assertEqual(report.weight, 10)
        self.assertEqual(report.height, 50)
        self.assertEqual(report.muac, 10)
        self.assertTrue(report.oedema)
        self.assertEqual(report.status, Report.INCOMPLETE_STATUS)

    def test_inactive_patient(self):
        """Report patient must be active."""
        client.patients.update(self.patient['id'], status='I')
        replies = self._send('nutrition report asdf w 10 h 50 m 10 o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '), reply)
        self.assertTrue('Nutrition reports must be for a patient '\
                'who is registered and active.' in reply)
        self.assertEqual(Report.objects.count(), 0)

    def test_negative_weight(self):
        """An error should be sent if reported weight is less than 0."""
        replies = self._send('nutrition report asdf w -10 h 50 m 10 o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '), reply)
        self.assertTrue('Please send a positive value (in kg) for '\
                'weight.' in reply, reply)
        self.assertEqual(Report.objects.count(), 0)

    def test_large_weight(self):
        """An error should be sent if reported weight has >4 digits."""
        replies = self._send('nutrition report asdf w 10000 h 50 m 10 o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '), reply)
        self.assertTrue('Nutrition report measurements ' in reply, reply)
        self.assertEqual(Report.objects.count(), 0)

    def test_specific_weight(self):
        """Reported weight should be rounded to 1 decimal place."""
        replies = self._send('nutrition report asdf w 10.55 h 50 m 10 o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Thanks'), reply)
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.get()
        self.assertEqual(report.patient_id, 'asdf')
        self.assertEqual(long(report.global_patient_id), self.patient['id'])
        self.assertEqual(report.weight, Decimal('10.6'))
        self.assertEqual(report.height, 50)
        self.assertEqual(report.muac, 10)
        self.assertTrue(report.oedema)
        self.assertEqual(report.status, Report.GOOD_STATUS)

    def test_invalid_weight(self):
        """Reported weight must be a number."""
        replies = self._send('nutrition report asdf w invalid h 50 m 10 o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '), reply)
        self.assertTrue('Please send a positive value (in kg) for weight.' in
                reply, reply)
        self.assertEqual(Report.objects.count(), 0)

    def test_no_weight(self):
        """Weight is not required, but the report will be incomplete."""
        replies = self._send('nutrition report asdf h 50 m 10 o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Thanks'), reply)
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.get()
        self.assertEqual(report.patient_id, 'asdf')
        self.assertEqual(long(report.global_patient_id), self.patient['id'])
        self.assertEqual(report.weight, None)
        self.assertEqual(report.height, 50)
        self.assertEqual(report.muac, 10)
        self.assertTrue(report.oedema)
        self.assertEqual(report.status, Report.INCOMPLETE_STATUS)

    def test_null_weight(self):
        """Weight is not required, but the report will be incomplete."""
        replies = self._send('nutrition report asdf w x h 50 m 10 o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Thanks'), reply)
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.get()
        self.assertEqual(report.patient_id, 'asdf')
        self.assertEqual(long(report.global_patient_id), self.patient['id'])
        self.assertEqual(report.weight, None)
        self.assertEqual(report.height, 50)
        self.assertEqual(report.muac, 10)
        self.assertTrue(report.oedema)
        self.assertEqual(report.status, Report.INCOMPLETE_STATUS)

    def test_negative_height(self):
        """An error should be sent if reported height is less than 0."""
        replies = self._send('nutrition report asdf w 10 h -50 m 10 o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '), reply)
        self.assertTrue('Please send a positive value (in cm) for '\
                'height.' in reply, reply)
        self.assertEqual(Report.objects.count(), 0)

    def test_large_height(self):
        """An error should be sent if reported height has >4 digits."""
        replies = self._send('nutrition report asdf w 10 h 50000 m 10 o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '), reply)
        self.assertTrue('Nutrition report measurements ' in reply, reply)
        self.assertEqual(Report.objects.count(), 0)

    def test_specific_height(self):
        """Reported height should be rounded to 1 decimal place."""
        replies = self._send('nutrition report asdf w 10 h 50.55 m 10 o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Thanks'), reply)
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.get()
        self.assertEqual(report.patient_id, 'asdf')
        self.assertEqual(long(report.global_patient_id), self.patient['id'])
        self.assertEqual(report.weight, 10)
        self.assertEqual(report.height, Decimal('50.6'))
        self.assertEqual(report.muac, 10)
        self.assertTrue(report.oedema)
        self.assertEqual(report.status, Report.GOOD_STATUS)

    def test_invalid_height(self):
        """Reported height must be a number."""
        replies = self._send('nutrition report asdf w 10 h invalid m 10 o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '), reply)
        self.assertTrue('Please send a positive value (in cm) for height.' in
                reply, reply)
        self.assertEqual(Report.objects.count(), 0)

    def test_no_height(self):
        """Height is not required, but the report will be incomplete."""
        replies = self._send('nutrition report asdf w 10 m 10 o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Thanks'), reply)
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.get()
        self.assertEqual(report.patient_id, 'asdf')
        self.assertEqual(long(report.global_patient_id), self.patient['id'])
        self.assertEqual(report.weight, 10)
        self.assertEqual(report.height, None)
        self.assertEqual(report.muac, 10)
        self.assertTrue(report.oedema)
        self.assertEqual(report.status, Report.INCOMPLETE_STATUS)

    def test_null_height(self):
        """Height is not required, but the report will be incomplete."""
        replies = self._send('nutrition report asdf w 10 h x m 10 o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Thanks'), reply)
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.get()
        self.assertEqual(report.patient_id, 'asdf')
        self.assertEqual(long(report.global_patient_id), self.patient['id'])
        self.assertEqual(report.weight, 10)
        self.assertEqual(report.height, None)
        self.assertEqual(report.muac, 10)
        self.assertTrue(report.oedema)
        self.assertEqual(report.status, Report.INCOMPLETE_STATUS)

    def test_invalid_measurement(self):
        """An error should be sent if pygrowup deems a measurement invalid."""
        with mock.patch('pygrowup.pygrowup.Calculator.zscore_for_measurement') as method:
            method.side_effect = InvalidMeasurement
            replies = self._send('nutrition report asdf w 10 h 50 m 10 o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, one of your measurements '\
                'is invalid: '), reply)
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.get()
        self.assertEqual(report.patient_id, 'asdf')
        self.assertEqual(long(report.global_patient_id), self.patient['id'])
        self.assertEqual(report.weight, 10)
        self.assertEqual(report.height, 50)
        self.assertEqual(report.muac, 10)
        self.assertTrue(report.oedema)
        self.assertEqual(report.status, report.SUSPECT_STATUS)

    def test_negative_muac(self):
        """An error should be sent if reported muac is less than 0."""
        replies = self._send('nutrition report asdf w 10 h 50 m -10 o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '), reply)
        self.assertTrue('Please send a positive value (in cm) for '\
                'mid-upper arm circumference.' in reply, reply)
        self.assertEqual(Report.objects.count(), 0)

    def test_large_muac(self):
        """An error should be sent if reported muac has >4 digits."""
        replies = self._send('nutrition report asdf w 10 h 50 m 10000 o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '), reply)
        self.assertTrue('Nutrition report measurements ' in reply, reply)
        self.assertEqual(Report.objects.count(), 0)

    def test_specific_muac(self):
        """Reported muac should be rounded to one decimal place."""
        replies = self._send('nutrition report asdf w 10 h 50 m 10.55 o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Thanks'), reply)
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.get()
        self.assertEqual(report.patient_id, 'asdf')
        self.assertEqual(long(report.global_patient_id), self.patient['id'])
        self.assertEqual(report.weight, 10)
        self.assertEqual(report.height, 50)
        self.assertEqual(report.muac, Decimal('10.6'))
        self.assertTrue(report.oedema)
        self.assertEqual(report.status, Report.GOOD_STATUS)

    def test_invalid_muac(self):
        """Reported muac must be a number."""
        replies = self._send('nutrition report asdf w 10 h 50 m invalid o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '), reply)
        self.assertTrue('Please send a positive value (in cm) for mid-upper '\
                'arm circumference.')
        self.assertEqual(Report.objects.count(), 0)

    def test_no_muac(self):
        """Muac should not be a required measurement."""
        replies = self._send('nutrition report asdf w 10 h 50 o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Thanks'), reply)
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.get()
        self.assertEqual(report.patient_id, 'asdf')
        self.assertEqual(long(report.global_patient_id), self.patient['id'])
        self.assertEqual(report.weight, 10)
        self.assertEqual(report.height, 50)
        self.assertEqual(report.muac, None)
        self.assertTrue(report.oedema)
        self.assertEqual(report.status, Report.GOOD_STATUS)

    def test_null_muac(self):
        """Muac should not be a required measurement."""
        replies = self._send('nutrition report asdf w 10 h 50 m x o Y')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Thanks'), reply)
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.get()
        self.assertEqual(report.patient_id, 'asdf')
        self.assertEqual(long(report.global_patient_id), self.patient['id'])
        self.assertEqual(report.weight, 10)
        self.assertEqual(report.height, 50)
        self.assertEqual(report.muac, None)
        self.assertTrue(report.oedema)
        self.assertEqual(report.status, Report.GOOD_STATUS)

    def test_invalid_oedema(self):
        """An error should be sent if reported oedema isn't Y/N."""
        replies = self._send('nutrition report asdf w 10 h 50 m 10 o invalid')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Sorry, an error occurred while '\
                'processing your message: '), reply)
        self.assertTrue('Please send Y or N to indicate whether the patient '\
                'has oedema.' in reply, reply)
        self.assertEqual(Report.objects.count(), 0)

    def test_no_oedema(self):
        """Oedema should not be a required measurement."""
        replies = self._send('nutrition report asdf w 10 h 50 m 10')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Thanks'), reply)
        self.assertTrue(Report.objects.count(), 1)
        report = Report.objects.get()
        self.assertEqual(report.patient_id, 'asdf')
        self.assertEqual(long(report.global_patient_id), self.patient['id'])
        self.assertEqual(report.weight, 10)
        self.assertEqual(report.height, 50)
        self.assertEqual(report.muac, 10)
        self.assertEqual(report.oedema, None)
        self.assertEqual(report.status, Report.GOOD_STATUS)

    def test_null_oedema(self):
        """Oedema should not be a required measurement."""
        replies = self._send('nutrition report asdf w 10 h 50 m 10 o x')
        self.assertEqual(len(replies), 1)
        reply = replies[0]
        self.assertTrue(reply.startswith('Thanks'), reply)
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.get()
        self.assertEqual(report.patient_id, 'asdf')
        self.assertEqual(long(report.global_patient_id), self.patient['id'])
        self.assertEqual(report.weight, 10)
        self.assertEqual(report.height, 50)
        self.assertEqual(report.muac, 10)
        self.assertEqual(report.oedema, None)
        self.assertEqual(report.status, Report.GOOD_STATUS)

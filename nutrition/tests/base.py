from __future__ import unicode_literals
import datetime

from django.conf import settings
from django.contrib.auth.models import User

from rapidsms.tests.harness import RapidTest

from healthcare.api import client

from ..models import Report


class NutritionTestBase(RapidTest):

    def setUp(self):
        # Before doing anything else, we must clear out the dummy backend
        # as this is not automatically flushed between tests.
        self.clear_healthcare_backends()
        return super(NutritionTestBase, self).setUp()

    def clear_healthcare_backends(self):
        for registry in (client.patients, client.providers):
            registry.backend._patients = {}
            registry.backend._patient_ids = {}
            registry.backend._providers = {}

    def create_patient(self, patient_id=None, source=None, **kwargs):
        defaults = {
            'name': self.random_string(25),
            'birth_date': datetime.date(2010, 3, 14),
            'sex': 'M',
        }
        defaults.update(**kwargs)
        patient = client.patients.create(**defaults)

        source = source or getattr(settings,
                'NUTRITION_PATIENT_HEALTHCARE_SOURCE', None)
        patient_id = patient_id or self.random_string(25)
        client.patients.link(patient['id'], patient_id, source)
        return patient_id, source, patient

    def create_report(self, analyze=True, **kwargs):
        if 'patient_id' not in kwargs:
            patient_id, source, patient = self.create_patient()
            kwargs['patient_id'] = patient_id
            kwargs['global_patient_id'] = patient['id']
        report = Report.objects.create(**kwargs)
        if analyze:
            report.analyze()
        return report

    def create_user(self, username=None, password=None, email=None,
            user_permissions=None, groups=None, **kwargs):
        username = username or self.random_string(25)
        password = password or self.random_string(25)
        email = email or '{0}@example.com'.format(self.random_string(25))
        user = User.objects.create_user(username, email, password)
        if user_permissions:
            user.user_permissions = user_permissions
        if groups:
            user.groups = groups
        if kwargs:
            User.objects.filter(pk=user.pk).update(**kwargs)
        return User.objects.get(pk=user.pk)

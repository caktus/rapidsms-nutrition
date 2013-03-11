from __future__ import unicode_literals
import datetime

from rapidsms.tests.harness import RapidTest

from healthcare.api import client

from ..models import HEALTHCARE_SOURCE


class NutritionTestBase(RapidTest):

    def setUp(self):
        # Before doing anything else, we must clear out the dummy backend.
        for registry in (client.patients, client.providers):
            registry.backend._patients = {}
            registry.backend._patient_ids = {}
            registry.backend._providers = {}
        return super(NutritionTestBase, self).setUp()

    def create_patient(self, patient_id=None, source=None, **kwargs):
        data = {
            'name': self.random_string(25),
            'birth_date': datetime.date(2010, 3, 14),
            'sex': 'M',
        }
        data.update(**kwargs)
        source = source or HEALTHCARE_SOURCE
        patient = client.patients.create(**data)
        client.patients.link(patient['id'], patient_id, source)
        return patient


from __future__ import unicode_literals
import datetime
from decimal import Decimal
from pygrowup.exceptions import InvalidMeasurement
from pygrowup.pygrowup import Calculator

from django.db import models

from healthcare.api import client


# Used with rapidsms-healthcare.
HEALTHCARE_SOURCE = 'nutrition'


class Report(models.Model):
    GOOD_STATUS = 'G'
    CANCELLED_STATUS = 'C'  # Health worker cancelled the report.
    SUSPECT_STATUS = 'S'  # Measurements are beyond reasonable limits.
    STATUSES = (
        (GOOD_STATUS, 'Good'),
        (CANCELLED_STATUS, 'Cancelled'),
        (SUSPECT_STATUS, 'Suspect'),
    )

    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=1, choices=STATUSES,
            default=GOOD_STATUS)

    healthworker_id = models.CharField(max_length=96, blank=True, null=True)
    patient_id = models.CharField(max_length=96)

    # Indicators, gathered from the health worker.
    height = models.DecimalField(max_digits=4, decimal_places=1, blank=True,
            null=True)  # cm
    weight = models.DecimalField(max_digits=4, decimal_places=1, blank=True,
            null=True)  # kg
    muac = models.DecimalField(max_digits=4, decimal_places=1, blank=True,
            null=True)  # cm
    oedema = models.NullBooleanField(default=None)

    # Calculated but stored here for easy reference.
    age_in_months = models.IntegerField(blank=True, null=True)

    # Nutrition z-scores, calcuated from indicators.
    weight4age = models.DecimalField(max_digits=4, decimal_places=2,
            blank=True, null=True)
    height4age = models.DecimalField(max_digits=4, decimal_places=2,
            blank=True, null=True)
    weight4height = models.DecimalField(max_digits=4, decimal_places=2,
            blank=True, null=True)

    class Meta:
        permissions = (
            ('can_view', 'Can View Nutrition Reports'),
        )
        verbose_name = 'nutrition report'

    def __unicode__(self):
        return 'Patient {0} on {1}'.format(self.patient_id, self.created.date())

    def _set_age_in_months(self):
        """
        Set the patient's age in months, rounded to the nearest full month.

        This method should only be called after created is set (after initial
        save).
        """
        birth_date = self.patient['birth_date']
        if birth_date:
            diff = self.created.date() - birth_date
            self.age_in_months = int(diff.days / 30.475)
        else:
            self.age_in_months = None

    def _set_zscores(self, calculator=None):
        calculator = calculator or Calculator(False, False, False)

        if self.age_in_months is None:
            return

        age = Decimal(str(self.age_in_months))
        sex = self.patient['sex']

        try:
            if self.weight is not None:
                self.weight4age = calculator.wfa(self.weight, age, sex)
            if self.height is not None:
                self.height4age = calculator.lhfa(self.height, age, sex)
            if self.weight is not None and self.height is not None:
                if age <= 24:
                    self.weight4height = calculator.wfl(self.weight, age, sex,
                            self.height)
                else:
                    self.weight4height = calculator.wfh(self.weight, age, sex,
                            self.height)
        except InvalidMeasurement:
            # This may be thrown by pygrowup when calculating z-scores if
            # the measurements provided are beyond reasonable limits.
            self.status = self.SUSPECT_STATUS
            self.save()
            raise

    def analyze(self):
        """
        This method should only be called after created is set (after initial
        save).
        """
        self._set_age_in_months()
        self._set_zscores()
        self.save()

    def cancel(self, save=True):
        self.status = Report.CANCELLED_STATUS
        if save:
            self.save()

    @property
    def healthworker(self):
        if self.healthworker_id:
            return client.providers.get(self.healthworker_id,
                    source=HEALTHCARE_SOURCE)
        return None

    @property
    def indicators(self):
        return {
            'height': self.height,
            'weight': self.weight,
            'muac': self.muac,
            'oedema': self.oedema,
        }

    @property
    def patient(self):
        return client.patients.get(self.patient_id, source=HEALTHCARE_SOURCE)


    @property
    def zscores(self):
        return {
            'weight4age': self.weight4age,
            'height4age': self.height4age,
            'weight4height': self.weight4height,
        }

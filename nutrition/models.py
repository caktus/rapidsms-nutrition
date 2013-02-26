import datetime
from pygrowup.pygrowup import Calculator

from django.db import models

from healthcare.api import client


# Used with rapidsms-healthcare.
HEALTHCARE_SOURCE = 'nutrition'


class Assessment(models.Model):
    GOOD_STATUS = 'G'
    CANCELLED_STATUS = 'C'  # Health worker cancelled the report.
    STATUSES = (
        (GOOD_STATUS, 'Good'),
        (CANCELLED_STATUS, 'Cancelled'),
    )

    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=1, choices=STATUSES, default=GOOD_STATUS)

    healthworker_id = models.CharField(max_length=96, blank=True, null=True)
    patient_id = models.CharField(max_length=96)

    # Indicators, gathered from the health worker.
    height = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)  # cm
    weight = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)  # kg
    muac = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)  # cm
    oedema = models.NullBooleanField(default=None)

    # Calculated but stored here for easy reference.
    age_in_months = models.DecimalField(blank=True, null=True)

    # Nutrition z-scores, calcuated from indicators.
    weight4age = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    height4age = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    weight4height = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    class Meta:
        permissions = (
            ('can_view', 'Can View Nutrition Assessments'),
        )
        verbose_name = 'nutrition assessment'

    def __unicode__(self):
        return 'Patient {0} on {1}'.format(self.patient_id, self.date.date())

    @property
    def healthworker(self):
        if self.healthworker_id:
            return client.providers.get(self.healthworker_id, source=HEALTHCARE_SOURCE)
        return None

    @property
    def patient(self):
        return client.patients.get(self.patient_id, source=HEALTHCARE_SOURCE)

    def _set_age_in_months(self):
        """
        Set the patient's age in months, rounded to the nearest full month.
        """
        birth_date = self.patient['birth_date']
        if birth_date:
            diff = self.date.date() - birth_date
            self.age_in_months = int(diff.days / 30.475)
        else:
            self.age_in_months = None

    def _set_zscores(calculator=None):
        calculator = calculator or Calculator(false, false, false)

        age = self.age_in_months
        if age is None:
            return

        sex = self.patient['sex']
        if self.weight is not None:
            self.weight4age = calculator.wfa(self.weight, age, sex)
        if self.height is not None:
            self.height4age = calculator.lhfa(self.height, age, sex)
        if self.weight is not None and self.height is not None:
            if age <= 24:
                self.weight4height = calculator.wfl(self.weight, age, sex, self.height)
            else:
                self.weight4height = calculator.wfh(self.weight, age, sex, self.height)

    def save(self, **kwargs):
        if not self.pk:
            self._set_age_in_months()
            self._set_zscores()
        super(Assessment, self).save(**kwargs)


    def cancel(self, save=True):
        self.status = Assessment.CANCELLED_STATUS
        if save:
            self.save()

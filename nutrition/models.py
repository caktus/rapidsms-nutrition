from __future__ import unicode_literals
import datetime
from decimal import Decimal
from pygrowup.exceptions import InvalidMeasurement
from pygrowup.pygrowup import Calculator

from django.db import models

from healthcare.api import client
from healthcare.exceptions import PatientDoesNotExist, ProviderDoesNotExist


class Report(models.Model):
    UNANALYZED_STATUS = 'U'  # The report has not yet been analyzed.
    GOOD_STATUS = 'G'  # The report analysis ran completely.
    CANCELLED_STATUS = 'C'  # Reporter cancelled the report.
    SUSPECT_STATUS = 'S'  # Measurements are beyond reasonable limits.
    INCOMPLETE_STATUS = 'I'  # Patient birth date or sex are not set.
    STATUSES = (
        (UNANALYZED_STATUS, 'Not Analyzed'),
        (GOOD_STATUS, 'Good'),
        (CANCELLED_STATUS, 'Cancelled'),
        (SUSPECT_STATUS, 'Suspect'),
        (INCOMPLETE_STATUS, 'Incomplete'),
    )

    # Meta data.
    created = models.DateTimeField(auto_now_add=True,
            verbose_name='report date')
    last_updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=1, blank=True, null=True,
            choices=STATUSES, default=UNANALYZED_STATUS)

    # Local identifiers, unique to the nutrition healthcare sources defined in
    # the project settings.
    # If source is None, these will be equivalent to the global identifiers.
    reporter_id = models.CharField(max_length=255, blank=True, null=True)
    patient_id = models.CharField(max_length=255)

    # Global identifiers, created by rapidsms-healthcare.
    global_reporter_id = models.CharField(max_length=255, blank=True,
            null=True)
    global_patient_id = models.CharField(max_length=255)

    # Indicators, gathered from the reporter.
    height = models.DecimalField(max_digits=4, decimal_places=1, blank=True,
            null=True, verbose_name='Height (CM)')
    weight = models.DecimalField(max_digits=4, decimal_places=1, blank=True,
            null=True, verbose_name='Weight (KG)')
    muac = models.DecimalField(max_digits=4, decimal_places=1, blank=True,
            null=True, verbose_name='MUAC (CM)')
    oedema = models.NullBooleanField(default=None)

    # Nutrition z-scores, calcuated from indicators.
    weight4age = models.DecimalField(max_digits=4, decimal_places=2,
            blank=True, null=True)
    height4age = models.DecimalField(max_digits=4, decimal_places=2,
            blank=True, null=True)
    weight4height = models.DecimalField(max_digits=4, decimal_places=2,
            blank=True, null=True)

    class Meta:
        permissions = (
            ('view_report', 'Can View Nutrition Reports'),
        )
        verbose_name = 'nutrition report'

    def __unicode__(self):
        return 'Patient {0} on {1}'.format(self.patient_id,
                self.created.date())

    @property
    def age(self):
        """
        Returns the patient's age at the time of this report, rounded down to
        the nearest full month.
        """
        patient = self.patient
        birth_date = patient.get('birth_date', None) if patient else None
        if birth_date:
            diff = self.created.date() - birth_date
            return int(diff.days / 30.475)

    def analyze(self, save=True, calculator=None):
        """Uses pygrowup to calculate z-scores from indicator data.

        If save is True, then the Report will be saved in its updated state.
        """
        calculator = calculator or Calculator(False, False, False)

        # If the patient's birth_date or sex is not present, pygrowup
        # cannot analyze the measurements.
        if self.age is None or self.sex is None:
            self.weight4age = None
            self.height4age = None
            self.weight4height = None
            self.status = Report.INCOMPLETE_STATUS
            if save:
                self.save()
            return self

        try:
            if self.weight is not None:
                self.weight4age = calculator.wfa(self.weight, self.age,
                        self.sex)
            if self.height is not None:
                self.height4age = calculator.lhfa(self.height, self.age,
                        self.sex)
            if self.weight is not None and self.height is not None:
                if self.age <= 24:
                    self.weight4height = calculator.wfl(self.weight, self.age,
                            self.sex, self.height)
                else:
                    self.weight4height = calculator.wfh(self.weight, self.age,
                            self.sex, self.height)
        except InvalidMeasurement as e:
            # This may be thrown by pygrowup when calculating z-scores if
            # the measurements provided are beyond reasonable limits.
            # Before raising this error to the caller, we'll remove
            # all calculations and set the status to suspect.
            self.weight4age = None
            self.height4age = None
            self.weight4height = None
            self.status = Report.SUSPECT_STATUS
            if save:
                self.save()
            raise e

        self.status = Report.GOOD_STATUS
        if save:
            self.save()
        return self

    def cancel(self, save=True):
        self.status = Report.CANCELLED_STATUS
        if save:
            self.save()

    def get_oedema_display(self):
        if self.oedema is None:
            return 'Unknown'
        return 'Yes' if self.oedema else 'No'

    @property
    def reporter(self):
        if not hasattr(self, '_reporter'):
            self._reporter = None  # TODO - integrate with rapidsms_healthcare app
        return self._reporter

    @property
    def indicators(self):
        return {
            'height': self.height,
            'weight': self.weight,
            'muac': self.muac,
            'oedema': self.get_oedema_display(),
        }

    @property
    def patient(self):
        """Retrieves the patient record associated with this report.

        If a caller requires that the patient record actually exist, it must
        ensure that patient is not None.
        """
        if not hasattr(self, '_patient'):
            try:
                self._patient = client.patients.get(self.global_patient_id)
            except PatientDoesNotExist:
                self._patient = None
        return self._patient

    @property
    def sex(self):
        """Returns the patient's sex."""
        patient = self.patient
        return patient.get('sex', None) if patient else None

    @property
    def zscores(self):
        return {
            'weight4age': self.weight4age,
            'height4age': self.height4age,
            'weight4height': self.weight4height,
        }

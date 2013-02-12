=======
Reports
=======

By submitting periodic reports of a patient's growth measurements, a health
worker can monitor the growth of a child over time. Each growth measurement
report contains the following information:

===========  =========  ==================================================
Parameter    Format     Description
===========  =========  ==================================================
patient_id   String     The patient's identifier
birth_date   YYYYMMDD   The date the patient was born.
sex          M/F        The patient's sex.
weight       Number     The patient's weight today, in kg.
height       Number     The patient's height today, in cm.
oedema       Y/N        Whether the patient has oedema today.
muac         Number     The patient's mid-upper arm circumference, in cm.
===========  =========  ==================================================

To make a report for an existing patient via SMS, send ``NUTRITION REPORT
<patient_id> <birth_date> <sex> <weight> <height> <oedema> <muac>``. If any
measurement is not available, send 'X' or 'x' in its place. The stored values
for birth date and sex will be updated with the latest values.

To cancel a patient's most recent report, send ``NUTRITION CANCEL
<patient_id>``.

As an example, the following conversation could occur::

    You:      NUTRITION REPORT
    RapidSMS: help text
    You:      NUTRITION REPORT zyx-321 20071114 F 18.5 110 N x
    RapidSMS: Thanks Jordan Brown. Nutrition update for Sam Green (zyx-321):
              dob=14 nov 2007
              sex=female
              weight=18.5kg
              height=110 cm
              oedema=no
              muac=unknown
    You:      NUTRITION REPORT mno-456 20080315 M 15 90 Y 18
    RapidSMS: Please register mno-456 as a nutrition patient before making a
              report.
    You:      NUTRITION CANCEL zyx-321
    RapidSMS: The latest nutrition report for Sam Green (zyx-321) has been
              cancelled.

TODO
====

* How should reporting healthcare worker be chosen?
* Is the latest report the last report made, or the last report you made?
* The Mwana app has 3 models - are they all still useful?

  - Survey - collection of SurveyEntries for a time period, and some baseline
    stats
  - SurveyEntry - a raw report, collected from the healthworker
  - Assessment - an analyzed SurveyEntry, which looks like it contains a lot
    of duplicated info from SurveyEntry.


=======
Reports
=======

By submitting periodic reports of a patient's growth measurements, a health
worker can monitor the health of a child over time. Each growth report
contains the following information:

===========  =========  =======================================================
Parameter    Format     Description
===========  =========  =======================================================
patient_id   String     The patient's unique identifier.
weight       Number     The patient's weight today, in kg.
height       Number     The patient's height today, in cm.
muac         Number     The patient's mid-upper arm circumference today, in cm.
oedema       Y/N        Whether the patient has oedema today.
===========  =========  =======================================================

To make a report for an existing patient via SMS, send ``NUTRITION REPORT
<patient_id> <weight> <height> <muac> <oedema>``. If any measurement is not
available, send 'X' or 'x' in its place.

To cancel a patient's most recent report, send ``NUTRITION CANCEL
<patient_id>``.

As an example, the following conversation could occur::

    You:      NUTRITION REPORT
    RapidSMS: To create a nutrition report, send: NUTRITION REPORT
              <patient_id> <weight in kg> <height in cm> <muac in cm>
              <oedema (Y/N)>
    You:      NUTRITION REPORT zyx-321 18.5 110 x N
    RapidSMS: Thanks Jordan Brown. Nutrition update for Sam Green (zyx-321):
              weight: 18.5 kg
              height: 110 cm
              muac: unknown
              oedema: no
    You:      NUTRITION REPORT mno-456 15 90 18 Y
    RapidSMS: Please register mno-456 as a nutrition patient before making a
              report.
    You:      NUTRITION CANCEL zyx-321
    RapidSMS: The latest nutrition report you made for Sam Green (zyx-321)
              has been cancelled.

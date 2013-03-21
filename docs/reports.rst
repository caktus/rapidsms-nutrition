=======
Reports
=======

By submitting periodic reports of a patient's growth measurements, a reporter
can monitor the health of a child over time. Each growth report contains the
following information:

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
<patient_id> W <weight> H <height> M <muac> O <oedema>``. If any measurement
is not available, you may omit it or send 'X' or 'x' in its place.

To cancel a patient's most recent report, send ``NUTRITION CANCEL
<patient_id>``.

As an example, the following conversation could occur::

    You:      NUTRITION REPORT
    RapidSMS: To create a nutrition report, send: NUTRITION REPORT
              <patient_id> W <weight (kg)> H <height (cm)> M <muac (cm)> O
              <oedema (Y/N)>
    You:      NUTRITION REPORT zyx-321 W 18.5 H 110 O N
    RapidSMS: Thanks Jordan Brown. Nutrition report for Sam Green (zyx-321):
              weight: 18.5 kg
              height: 110 cm
              muac: unknown
              oedema: no
    You:      NUTRITION REPORT mno-456 W 15 H 90 M 18 O Y
    RapidSMS: Sorry, an error occurred while processing your message:
              Nutrition reports must be for a patient who is registered and
              active.
    You:      NUTRITION CANCEL zyx-321
    RapidSMS: Thanks Jordan Brown. The most recent nutrition report for
              Sam Green (zyx-321) has been cancelled.

Report Statuses
---------------

Reports may have the following statuses:

* **Unanalyzed.** This is the default status when a report has been receieved
  but analysis has not yet been attempted.
* **Incomplete.** Analysis failed (partially or completely) because one or
  more pieces of information was missing:

  - patient sex
  - patient birth date
  - reported weight
  - reported height

* **Suspect.** Analysis failed completely, because reported measurements were
  outside of reasonable bounds.
* **Error.** Analysis failed completely, for some other reason. For example, the
  patient might be old enough that there is no CDC data against which to
  analyze, or maybe an internal error occurred.
* **Analyzed.** Analysis completed in full, and the report has z-scores for
  weight vs. height, weight vs. age, and height vs. age.

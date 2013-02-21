============
Registration
============

In rapidsms-nutrition, **health workers** keep track of the growth of child
**patients**. Each health worker and patient must be registered in the
application.

.. _registration-health-workers:

Health Workers
==============

The following information is needed to register a health worker:

==========  =======  ==========================================
Parameter   Format   Description
==========  =======  ==========================================
id          String   A unique identifier for the health worker.
name        String   The health worker's human-readable name.
==========  =======  ==========================================

To register a health worker via SMS, send ``NUTRITION REGISTER HEALTHWORKER
<id> <name>``. The system will register a new health worker with the given
name and identifier. The identifier must be unique and not already in use.

To deactivate a health worker via SMS, send ``NUTRITION DEACTIVATE
HEALTHWORKER <id>``. The health worker's record will be marked as inactive and
they will not be able to make additional assessments.

As an example, the following conversation could occur::

    You:      NUTRITION REGISTER HEALTHWORKER
    RapidSMS: To register a new nutrition health worker, send: NUTRITION
              REGISTER HEALTHWORKER <id> <name>
    You:      NUTRITION REGISTER HEALTHWORKER abc-123 Jordan Brown
    RapidSMS: You have registered a new nutrition health worker: Jordan
              Brown (abc-123).
    You:      NUTRITION REGISTER HEALTHWORKER abc-123 Alex Blue
    RapidSMS: Sorry, a nutrition health worker is already registered using
              the identifier abc-123.
    You:      NUTRITION DEACTIVATE HEALTHWORKER abc-123
    RapidSMS: Nutrition health worker Jordan Brown (abc-123) has been marked
              as inactive.

.. _registration-patients:

Patients
========

The following information is needed to register a child patient:

==========  ========  =====================================
Parameter   Format    Description
==========  ========  =====================================
id          String    A unique identifier for the patient.
name        String    The patient's human-readable name.
birth_date  YYYYMMDD  The date the patient was born.
sex         M/F       The patient's sex.
==========  ========  =====================================

To register a patient via SMS, send ``NUTRITON REGISTER PATIENT <id> <name>
<birth_date> <sex>``. The system will register a new patient with the given
information. The identifier must be unique and not already in use.

To remove a patient from the system via SMS, send ``NUTRITION DEACTIVATE
PATIENT <id>``. The patient's record will be marked as inactive and health
workers will not be able to make additional assessments for that patient.

As an example, the following conversation could occur::

    You:      NUTRITION REGISTER PATIENT
    RapidSMS: To register a new nutrition patient, send: NUTRITION REGISTER
              PATIENT <id> <name> <birth_date> <sex>
    You:      NUTRITION REGISTER PATIENT zyx-321 Sam Green 20100328 F
    RapidSMS: You have registered a new nutrition patient: Sam Green
              (zyx-321), female, born 28 Mar 2010.
    You:      NUTRITION REGISTER PATIENT zyx-321 Morgan Black 2010.04.01 M
    RapidSMS: Sorry, a nutrition patient is already registered using the
              identifier zyx-321.
    You:      NUTRITION DEACTIVATE PATIENT zyx-321
    RapidSMS: Nutrition patient Sam Green (zyx-321) has been removed from the
              system.

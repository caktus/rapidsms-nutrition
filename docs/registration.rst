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

    :id:   A unique identifier string.
    :name: A readable name/identifier string.

To register a health worker via SMS, send ``NUTRITION REGISTER HEALTHWORKER
<id> <name>``. The system will register a new health worker with the given
name and identifier. The identifier must be unique and not already in use.

To remove a health worker from the system via SMS, send ``NUTRITION REMOVE
HEALTHWORKER <id>``. The health worker's record will be fully deleted from the
database.

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
    You:      NUTRITION REMOVE HEALTHWORKER abc-123
    RapidSMS: Nutrition health worker Jordan Brown (abc-123) has been removed
              from the system.

.. _registration-patients:

Patients
========

The following information is needed to register a child patient:

    :id:         A unique identifier string
    :name:       A readable name/identifier string

To register a patient via SMS, send ``NUTRITON REGISTER PATIENT <id> <name>``.
The system will register a new patient with the given name and identifier.
The identifier must be unique and not already in use.

To remove a patient from the system via SMS, send ``NUTRITION REMOVE PATIENT
<id>``. The patient's record will be fully deleted from the database.

As an example, the following conversation could occur::

    You:      NUTRITION REGISTER PATIENT
    RapidSMS: To register a new nutrition patient, send: NUTRITION REGISTER
              PATIENT <id> <name>
    You:      NUTRITION REGISTER PATIENT zyx-321 Sam Green
    RapidSMS: You have registered a new nutrition patient: Sam Green
              (zyx-321).
    You:      NUTRITION REGISTER PATIENT zyx-321 Morgan Black
    RapidSMS: Sorry, a nutrition patient is already registered using the
              identifier zyx-321.
    You:      NUTRITION REMOVE PATIENT zyx-321
    RapidSMS: Nutrition patient Sam Green (zyx-321) has been removed from the
              system.

TODO
====

* Should there be a way to update patient/CHW info?
* Could we store birth date and sex when registering a patient, rather than
  sending them for each report?
* When a patient/CHW is removed from the system, are they fully deleted or
  rather marked as inactive? What should happen to their report data?
* When a patient/CHW who has been removed re-registers, what should happen?
* How should we associate RapidSMS Contacts with CHWs?
* Can a single phone number/Contact be used by more than one CHW?

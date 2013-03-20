===============
Getting Started
===============

Installation
============

The easiest way to install rapidsms-nutrition is (or will be) to use pip::

    pip install rapidsms-nutrition

If you choose to install from `source
<http://github.com/caktus/rapidsms-nutrition>`_, take care to also install the
additional programs listed in the `requirements` directory.

1. Add ``'nutrition'`` and its requirements to :setting:`INSTALLED_APPS` in
   your RapidSMS project::

    INSTALLED_APPS = [
        ...
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'rapidsms',
        'rapidsms.contrib.handlers',
        'django_tables2',
        'healthcare',
        'nutrition',
        ...
    ]

2. Ensure that the request context processor is in
   :setting:`TEMPLATE_CONTEXT_PROCESSORS`, as required by `django_tables2`::

    TEMPLATE_CONTEXT_PROCESSORS = [
        ...
        'django.core.context_processors.request',
        ...
    ]

3. `Configure rapidsms-healthcare
   <http://rapidsms-healthcare.readthedocs.org/en/latest/quick-start.html#configuration>`_
   to use the storage backend of your choice.

4. Update the database via::

    python manage.py migrate nutrition

   If you are not using South, you can create the tables via::

    python manage.py syncdb

.. _configuration:

Configuration
=============

The behavior of rapidsms-nutrition may be configured via Django project
settings.

* **NUTRITION_PATIENT_HEALTHCARE_SOURCE** (*Default*: ``None``)

  Patients are identified using a *global identifier*, assigned by
  rapidsms-healthcare, as well as any number of *canonical identifiers*, each
  associated with and unique to a particular *source*.

  To send a new report for a patient via SMS, reporters must know the
  patient's canonical ID associated with the source specified in
  :setting:`NUTRITION_PATIENT_HEALTHCARE_SOURCE` (or the global ID if the
  setting is ``None``). For example, National ID numbers could be a source
  used to identify patients.

  Take care when updating this setting after initial development, as this will
  change the information that your reporters need to know to send in patient
  reports via SMS.

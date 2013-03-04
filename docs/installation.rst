============
Installation
============

The easiest way to install rapidsms-nutrition is (or will be) to use pip::

    pip install rapidsms-nutrition

If you choose to install from `source
<http://github.com/caktus/rapidsms-nutrition>`_, take care to also install the
additional programs listed in the `requirements` directory.

After installing, you should add ``'nutrition'`` and its requirements (if
not already present) to :setting:`INSTALLED_APPS` in your RapidSMS project::

    INSTALLED_APPS [
        ...
        'rapidsms',
        'rapidsms.contrib.handlers',
        'django_tables2',
        'healthcare',
        'nutrition'
    ]

You will need to `configure rapidsms-healthcare
<http://rapidsms-healthcare.readthedocs.org/en/latest/quick-start.html#configuration>`_
to use the storage backend of your choice, and ensure that
``'django.core.context_processors.request'`` is in
:setting:`TEMPLATE_CONTEXT_PROCESSORS` as required by `django_tables2`.

Since this application implements a registration process for
:ref:`health workers <registration-health-workers>` and :ref:`child patients
<registration-patients>`, you may want to disable
`rapidsms.contrib.registration
<http://rapidsms.readthedocs.org/en/latest/topics/contrib/registration.html>`_
by removing it from your :setting:`INSTALLED_APPS`.

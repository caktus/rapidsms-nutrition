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
        'healthcare',
        'nutrition'
    ]

Since this application implements a registration process for
:ref:`health workers <registration-health-workers>` and :ref:`child patients
<registration-patients>`, you may want to disable
`rapidsms.contrib.registration
<http://rapidsms.readthedocs.org/en/latest/topics/contrib/registration.html>`_
by removing it from your :setting:`INSTALLED_APPS`.

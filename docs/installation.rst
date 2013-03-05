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

    INSTALLED_APPS = [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'rapidsms',
        'rapidsms.contrib.handlers',
        'django_tables2',
        'healthcare',
        'nutrition',
    ]

You will need to `configure rapidsms-healthcare
<http://rapidsms-healthcare.readthedocs.org/en/latest/quick-start.html#configuration>`_
to use the storage backend of your choice, and ensure that
``'django.core.context_processors.request'`` is in
:setting:`TEMPLATE_CONTEXT_PROCESSORS` as required by `django_tables2`.

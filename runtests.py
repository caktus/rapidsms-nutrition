#!/usr/bin/env python
import optparse
import sys

from django.conf import settings


if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        HEALTHCARE_STORAGE_BACKEND='healthcare.backends.dummy.DummyStorage',
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'rapidsms',
            'rapidsms.contrib.handlers',
            'django_tables2',
            'healthcare',
            'healthcare.backends.dummy',
            'nutrition',
        ),
        TEMPLATE_CONTEXT_PROCESSORS = (
            'django.contrib.auth.context_processors.auth',
            'django.core.context_processors.debug',
            'django.core.context_processors.i18n',
            'django.core.context_processors.media',
            'django.core.context_processors.static',
            'django.contrib.messages.context_processors.messages',
            'django.core.context_processors.request',
        ),
        ROOT_URLCONF='nutrition.tests.urls',
        PROJECT_NAME='Nutrition Test',
        SITE_ID=1,
        SECRET_KEY='this-is-just-for-tests-so-not-that-secret',

        NUTRITION_PATIENT_HEALTHCARE_SOURCE='nutrition',
        NUTRITION_REPORTER_HEALTHCARE_SOURCE='nutrition',
    )


from django.test.utils import get_runner


def runtests():
    parser = optparse.OptionParser()
    _, tests = parser.parse_args()
    tests = tests or ['nutrition']

    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=1, interactive=True, failfast=False)
    sys.exit(test_runner.run_tests(tests))


if __name__ == '__main__':
    runtests()


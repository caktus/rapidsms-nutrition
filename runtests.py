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
        ROOT_URLCONF='nutrition.tests.urls',
        PROJECT_NAME='Nutrition Test',
        SITE_ID=1,
        SECRET_KEY='this-is-just-for-tests-so-not-that-secret',
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


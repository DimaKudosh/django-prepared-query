import argparse
import sys
from os.path import abspath, dirname, join
import django
from django.conf import settings
from django.test.runner import DiscoverRunner
from django.db import connections


SOURCE_DIR = dirname(dirname(abspath(__file__)))
TESTS_DIR = join(SOURCE_DIR, 'tests')

sys.path.append(SOURCE_DIR)
sys.path.append(TESTS_DIR)

AVAILABLE_DATABASES = ['postgresql', 'mysql']
CURRENT_DB = AVAILABLE_DATABASES[0]

DATABASES = {
    'postgresql': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'prepared_statements_test',
    },
    'mysql': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'prepared_statements_test',
    }
}
DATABASES['default'] = DATABASES[CURRENT_DB]


parser = argparse.ArgumentParser()
parser.add_argument('--db', dest='db', help='DB name')
args = parser.parse_args()


def run_tests(db):
    print('Run tests for %s' % db)
    connections['default'] = connections[db]
    return test_runner.run_tests(['tests'])


settings.configure(DATABASES=DATABASES, INSTALLED_APPS=('test_app',))
django.setup()
test_runner = DiscoverRunner(top_level=TESTS_DIR, interactive=False, keepdb=True)
failures = 0
if args.db:
    if args.db in AVAILABLE_DATABASES:
        failures = run_tests(args.db)
    else:
        print('Incorrect database name')
else:
    failures = 0
    for db in AVAILABLE_DATABASES:
        failures += run_tests(db)

if failures:
    print('Failed %d tests' % failures)

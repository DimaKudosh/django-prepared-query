import sys
from os.path import abspath, dirname, join
import django
from django.conf import settings
from django.test.runner import DiscoverRunner


SOURCE_DIR = dirname(dirname(abspath(__file__)))
TESTS_DIR = join(SOURCE_DIR, 'tests')

sys.path.append(SOURCE_DIR)
sys.path.append(TESTS_DIR)


DATABASES = {
    'postgresql': {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'prepared_statements_test',
        }
    },
}


settings.configure(DATABASES=DATABASES['postgresql'], INSTALLED_APPS=('test_app', ))


django.setup()
test_runner = DiscoverRunner(top_level=TESTS_DIR, interactive=False, keepdb=False)

failures = test_runner.run_tests(['tests'])
if failures:
    sys.exit(failures)

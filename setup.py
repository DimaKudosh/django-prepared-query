import os
from setuptools import setup

exec(open('django_prepared_query/version.py').read())


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='django-prepared-query',
    version=__version__,
    packages=['django_prepared_query'],
    include_package_data=True,
    url='https://github.com/DimaKudosh/django-prepared-query',
    license='MIT',
    author='Dima Kudosh',
    author_email='dimakudosh@gmail.com',
    description='Prepared statements support for Django',
    keywords=['django', 'orm'],
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: POSIX',
        'Programming Language :: Python',
    ],
)

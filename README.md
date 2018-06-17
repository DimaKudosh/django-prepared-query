# DJANGO-PREPARED-QUERY[![Build Status](https://travis-ci.org/DimaKudosh/django-prepared-query.svg?branch=master)](https://travis-ci.org/DimaKudosh/django-prepared-query)[![Coverage Status](https://coveralls.io/repos/github/DimaKudosh/django-prepared-query/badge.svg?branch=master)](https://coveralls.io/github/DimaKudosh/django-prepared-query?branch=master)[![PyPI](https://img.shields.io/pypi/pyversions/Django.svg)]()

## Installation
You can install `django-prepared-query` using pip:
```
$ pip install django-prepared-query
```

## Example
```python
from django_prepared_query import PreparedManager, BindParam


class Book(models.Model):
    objects = PreparedManager()

qs = Book.objects.filter(name__startswith=BindParam('name_start'))
books = qs.execute(name_start='A')
```

## Documentation
Documentation is available here http://django-prepared-query.readthedocs.io/en/latest/

## Benchmark
[Here](https://github.com/DimaKudosh/django-prepared-query/blob/master/demo/benchmark.ipynb) you can find notebook with benchmark.

## Goals
* ~~Add support for in lookup.~~
* ~~Add support for limit/offset.~~
* Make this working without specifying BindParams.
* Add support for INSERT/UPDATE sql queries.

.. django_prepared_query documentation master file, created by
   sphinx-quickstart on Fri Nov 17 20:54:01 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Django Prepared Query documentation!
===============================================

SQL prepared statement support for Django ORM.

Installation
------------

**django_prepared_query** works only with Python 3 and Django 1.11+.
Currently it supports only PostgreSQL and MySQL.
It can be installed with **pip**:

.. code-block:: bash

    $ pip install django_prepared_query

Usage
-----

For using prepared statements you must replace model standard manager with `PreparedManager`.

.. code-block:: python

    from django_prepared_query import PreparedManager

    class Book(Model):
        objects = PreparedManger()
        ...

`PreparedManager` has 2 additional methods: prepare and execute that are equivalent to SQL prepare and execute commands.
Calling execute before prepare raises `QueryNotPrepared` exception.
After prepare you can call only use execute method, other methods raises `OperationOnPreparedStatement` exception.

.. code-block:: python

    qs = Book.objects.prepare()
    result = qs.execute()

It's possible to add dynamic parameters to query using `BindParam` expression.
It takes parameter name and not required field type for situations when it can't automatically detect type.
Parameter name will be used in execute method. Passing incorrect parameter name raises `IncorrectBindParameter` exception.

.. code-block:: python

    from django_prepared_query import BindParam

    qs = Book.objects.filter(name=BindParam('book_name')).prepare()
    result = qs.execute(book_name='Harry Potter')

Also you can use different built-in lookups except `isnull` and `in` that raises `NotSupportedLookup` exception.

.. code-block:: python

    from django_prepared_query import BindParam

    qs = Book.objects.filter(name__startswith=BindParam('book_name')).prepare()
    result = qs.execute(book_name='Harry Potter')


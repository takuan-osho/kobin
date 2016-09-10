=====
Kobin
=====

.. image:: https://travis-ci.org/c-bata/kobin.svg?branch=master
   :target: https://travis-ci.org/c-bata/kobin

.. image:: https://badge.fury.io/py/kobin.svg
   :target: https://badge.fury.io/py/kobin

.. image:: https://coveralls.io/repos/github/c-bata/kobin/badge.svg?branch=coveralls
   :target: https://coveralls.io/github/c-bata/kobin?branch=master

.. image:: https://codeclimate.com/github/c-bata/kobin/badges/gpa.svg
   :target: https://codeclimate.com/github/c-bata/kobin
   :alt: Code Climate


`Kobin <https://kobin.readthedocs.org/>`_ is a small and statically-typed WSGI micro web framework for Python.
**This library is a pre-release. Expect missing docs and breaking API changes.**
Kobin has following features.

- **Statically-typed** web framework with PEP 0484(Type Hints).
- **Lightweight** implementations for solving your problems easily.
- Kobin provides Routing, WSGI request and response wrapper, Jinja2 template adapter and several useful utilities.


Hello World
===========

::

   $ pip install kobin


.. code-block:: python

   from kobin import Kobin
   app = Kobin()

   @app.route('^/(?P<name>\w*)$')
   def hello(name: str):
       return "Hello {}!!".format(name)

   if __name__ == '__main__':
       app.run()


Requirements
============

Kobin Requires the following:

- Python 3.5

Kobin is no dependencies other than the `Python Standard Library <https://docs.python.org/3/library/>`_.
The following packages are optional:

- Jinja2
- gunicorn


Topics
======

Static files
------------

If you want a function for serving static files, you want to use `wsgi-static-middleware <https://pypi.python.org/pypi/wsgi-static-middleware>`_ .

.. code-block:: python

   import os
   from kobin import Kobin

   BASE_DIR = os.path.dirname(__name__)
   STATIC_DIRS = [os.path.join(BASE_DIR, 'static')]

   app = Kobin()


   @app.route(
   def app(env, start_response):
       start_response('200 OK', [('Conte-type', 'text/plain; charset=utf-8')])
       return [b'Hello World']


   if __name__ == '__main__':
       from wsgiref.simple_server import make_server
       from wsgi_static_middleware import StaticMiddleware
       app = StaticMiddleware(app, static_root='static', static_dirs=STATIC_DIRS)
       httpd = make_server('', 8000, app)
       httpd.serve_forever()


Resources
=========

* `Documentation (English) <https://kobin.readthedocs.org/en/latest/>`_
* `Documentation (日本語) <https://kobin.readthedocs.org/ja/latest/>`_
* `Github <https://github.com/c-bata/kobin>`_
* `PyPI <https://pypi.python.org/pypi/kobin>`_


License
=======

This software is licensed under the MIT License.

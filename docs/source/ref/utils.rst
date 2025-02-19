===================
Utils API reference
===================

.. module:: django_mongodb_backend.utils
   :synopsis: Built-in utilities.

This document covers the public API parts of ``django_mongodb_backend.utils``.
Most of the module's contents are designed for internal use and only the
following parts can be considered stable.

``parse_uri()``
===============

.. function:: parse_uri(uri, db_name=None, conn_max_age=0, test=None)

Parses a MongoDB `connection string`_ into a dictionary suitable for Django's
:setting:`DATABASES` setting.

.. _connection string: https://www.mongodb.com/docs/manual/reference/connection-string/

Example::

    import django_mongodb_backend

    MONGODB_URI = "mongodb+srv://my_user:my_password@cluster0.example.mongodb.net/defaultauthdb?retryWrites=true&w=majority&tls=false"
    DATABASES["default"] = django_mongodb_backend.parse_uri(MONGODB_URI, db_name="example")

You must specify ``db_name`` (the :setting:`NAME` of your database) if the URI
doesn't specify ``defaultauthdb``.

You can use the parameters to customize the resulting :setting:`DATABASES`
setting:

- Use ``conn_max_age`` to configure :ref:`persistent database connections
  <persistent-database-connections>`.
- Use ``test`` to provide a dictionary of settings for test databases in the
  format of :setting:`TEST <DATABASE-TEST>`.

But for maximum flexibility, construct :setting:`DATABASES` manually as
described in :ref:`configuring-databases-setting`.

``DATABASES`` settings
======================

Some MongoDB-specific database settings are available via the Django
``DATABASES`` setting.

SRV Connection
--------------

For MongoDB Atlas clusters, you can use the ``srv`` connection string to
connect to your cluster.

For example, you could configure ``HOST`` with a connection string like this::

    DATABASES = {
        'default': {
            'ENGINE': 'django_mongodb',
            'NAME': 'mydatabase',
            'HOST': 'mongodb+srv://<cluster>',
        }
    }

Replica Sets
------------

For MongoDB Replica Sets, you can configure the ``HOST`` setting with
multiple host entries like this::

    DATABASES = {
        'default': {
            'ENGINE': 'django_mongodb',
            'NAME': 'mydatabase',
            'HOST': 'localhost:27017,localhost:27018,localhost:27019',
        }
    }

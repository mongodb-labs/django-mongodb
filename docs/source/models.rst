Model reference
===============

.. module:: django_mongodb_backend.models

One MongoDB-specific model is available in ``django_mongodb_backend.models``.

.. class:: EmbeddedModel

An abstract model which all :doc:`embedded models <embedded-models>` must
subclass.

Since these models are not stored in their own collection, they do not have
any of the normal ``QuerySet`` methods (``all()``, ``filter()``, ``delete()``,
etc.) You also cannot call ``Model.save()`` and ``delete()`` on them.

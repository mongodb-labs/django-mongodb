# Django MongoDB Backend

This backend is currently in development and is not advised for Production workflows. Backwards incompatible
changes may be made without notice. We welcome your feedback as we continue to
explore and build. The best way to share this is via our [MongoDB Community Forum](https://www.mongodb.com/community/forums/tag/python)

## Install

The development version of this package supports Django 5.0.x. To install it:

`pip install django-mongodb-backend~=5.0.0`


## Quickstart

This tutorial shows you how to create a Django project, connect to a MongoDB cluster hosted on MongoDB Atlas, and interact with data in your cluster. To read more, please check our MongoDB Backend for Django tutorials page.

### Start a Project

From your shell, run the following command to create a new Django project called example based on a custom template:

```bash
$ django-admin startproject example --template https://github.com/mongodb-labs/django-mongodb-project/archive/refs/heads/5.0.x.zip
```


### Connect to the Database

Navigate to your `example/settings.py` file and find the variable named `DATABASES` Replace the `DATABASES` setting with this:

```python
DATABASES = {
   "default": django_mongodb_backend.parse_uri("<CONNECTION_STRING_URI>"),
}
```

Where `<CONNECTION_STRING_URI>` is your connection string from the previous step.

### Start the Server
To verify that you installed Django MongoDB Backend and correctly configured your project, run the following command from your project root:
```bash
python manage.py runserver
```
Then, visit http://127.0.0.1:8000/. This page displays a "Congratulations!" message and an image of a rocket.


## Capabilities of Django Backend for MongoDB

- **Model MongoDB Documents Through Django’s ORM**  
    
  - Translate Django model instances to MongoDB documents.  
  - Create new collections corresponding to models.  
  - Supports field validation, data storage, updating, and deletion.  
  - Maps Django's built-in fields to MongoDB data types.  
  - Provides new custom fields for arrays (ArrayField) and embedded documents (EmbeddedModelField).  
  - Supports core migration functionalities including creating, deleting, and updating indexes and collections


- **Index Management**  
    
  - Create single, compound, and unique indexes using Django Indexes  
  - Create MongoDB partial indexes in Django using Q notation.


- **Querying Data**  

  - Supports most functions of the Django QuerySet API  
  - Support Query Annotations and common SQL AGGREGATE operators  
   Support foreign key usage and execute JOIN operations
  - Through our custom raw\_aggregate call, MQL operations like Vector Search, Atlas Search, and GeoSpatial querying still yield Django QuerySet resutts,


- **Administrator Dashboard & Authentication**  
    
  - Manage your data in Django’s admin site.  
  - Fully integrated with Django's authentication framework.  
  - Supports native user management features like creating users and sessions.

## Limitations of django-mongodb-backend

- Database Variables `ATOMIC_REQUESTS`, `AUTOCOMMIT`, `CONN_HEALTH_CHECKS`, `TIME_ZONE` not supported
- No support for GeoDjango
- Functions such as `Chr`, `ExtractQuarter`, `MD5`, `Now`, `Ord`, `Pad`, `Repeat`, `Reverse`, `Right`, `SHA1`, `SHA224`, `SHA256`, `SHA384`, `SHA512`, and `Sign`.
- The `tzinfo` parameter of the `Trunc` database functions does not work properly because MongoDB converts the result back to UTC.
- Schema Validation is not enforced. Refer to MongoDB documentation for how to enforce schema validation.
- Django DDL Transactions are not supported.
- The `migrate --fake-initial` command is not supported due to the inability to introspect MongoDB collection schema.
- The asynchronous functionality of the Django API has not yet been tested.
- `BSONRegExp` has no custom field class. It is best represented as a `CharField`.


#### **Model Limitations**

  - `$vectorSearch` and `$search` and Geospatial index creation through the Django Indexes API is not yet available.
  - Updating indexes in `EmbeddedModels` do not work after the first table creation.

  - **ArrayField**
    - Does not support `EmbeddedModel` within `ArrayField`.

  - **EmbeddedModel**
    - Limited schema change support (no changing of embedded models).
    - Embedded documents cannot take Django ForeignKeys.
    - Arbitrary or untyped `EmbeddedModelField` is not supported. All fields must derive from an `EmbeddedModel` class.

  - **JSONField**
    - There is no way to distinguish between a JSON "null" and a SQL null in specific queries.
    - Some queries with Q objects, e.g., `Q(value__foo="bar")`, don't work properly, particularly with `QuerySet.exclude()`.
    - Filtering for a `None` key, e.g., `QuerySet.filter(value__j=None)`, incorrectly returns objects where the key doesn't exist.

  - **DateTimeField**
    - No support for microsecond granularity.

  - **DurationField**:
    - Stores milliseconds rather than microseconds.

  - **Unavailable Fields**:
    - `GeneratedField`
    - `ImageField`


- **These QuerySet API methods do not work**

  - `distinct()`
  - `dates()`
  - `datetimes()`
  - `prefetch_related()`
  - `extra()`
  - `QuerySet.delete()` and `update()` do not support queries that span multiple collections.


- **Django Management Commands that do not work**
  - `createcachetable`
  - `inspectdb`
  - `optimizemigration`
  - `sqlflush`
  - `sqlsequencereset`


## Future Commitments of Django Backend for MongoDB

- **Advanced Indexing**  
    
  - Support for advanced index types like geospatial, text, and vector search indexes.  
      
- **Improved Data Modeling**  
    
  - Support ArrayFields containing Embedded Models  
  - Support Collections with multiple Django Models  
  - Possible support for additional Django fields such as ImageField


- **Extended Querying Features**  
    
  - Exploring smoother ways to allow users to use full-text search, vector search, or geospatial querying.


- **Enhanced Transactions Support**  
    
  - Investigation and support for transactions, allowing features like `ATOMIC_REQUESTS` and `AUTOCOMMIT`.

- **Asynchronous Capabilities**  
    
  - Evaluation and support for Django’s asynchronous callback functions.


- **Performance Optimization**  
    
  - Focus on performance tuning, especially concerning JOIN operations and ensure competitive performance relative to SQL databases.


- **Expanded Third-Party Library Support**  
    
  - Vet our backend library works effortlessly with major Django Third-Party solutions

These future capabilities are intended to enhance the functionality of the Django Backend for MongoDB as it progresses towards a General Availability (GA) release. If you have any more specific questions or need further details, feel free to ask\!  


### Issues & Help

We're glad to have such a vibrant community of users of Django MongoDB Backend. We recommend seeking support for general questions through the MongoDB Community Forums.

#### Bugs / Feature Requests
To report a bug or to request a new feature in Django MongoDB Backend, please open an issue in JIRA, our issue-management tool, using the following steps:

1. [Create a JIRA account.](https://jira.mongodb.org/)

2. Navigate to the [Python Integrations project](https://jira.mongodb.org/projects/INTPYTHON/).

3. Click **Create Issue**. Please provide as much information as possible about the issue and the steps to reproduce it.

Bug reports in JIRA for the Django MongoDB Backend project can be viewed by everyone.

If you identify a security vulnerability in the driver or in any other MongoDB project, please report it according to the instructions found in [Create a Vulnerability Report](https://www.mongodb.com/docs/manual/tutorial/create-a-vulnerability-report/).
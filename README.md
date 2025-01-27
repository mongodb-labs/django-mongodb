# Django MongoDB Backend

This backend is currently in development and is not advised for Production workflows. Backwards incompatible
changes may be made without notice. We welcome your feedback as we continue to
explore and build. The best way to share this is via our [MongoDB Community Forum](https://www.mongodb.com/community/forums/tag/python)

## Install

The development version of this package supports Django 5.0.x. To install it:

`pip install django-mongodb-backend`

### Resources

 Check back soon as we aim to provide more links that will dive deeper into our library!

* [Developer Notes](DEV_NOTES.md)


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

- **Database Connectivity**  
    
  - Directly tune MongoDB connection settings within your Django configuration\!  
  - Work against a persisted cloud instance of MongoDB for free\!


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
    
  - Querying API powered through the amazing MongoDB Aggregation Pipeline  
  - Supports most functions of the Django QuerySet API  
  - Support Query Annotations and common SQL AGGREGATE operators  
  - We support foreign keys and execute JOIN operations all in 1 database call  
  - Through our custom raw\_aggregate call, MQL operations like Vector Search, Atlas Search, and GeoSpatial querying still yield Django QuerySet results\!


- **Administrator Dashboard & Authentication**  
    
  - Manage your data in Django’s admin site.  
  - Fully integrated with Django's authentication framework.  
  - Supports native user management features like creating users and sessions.


- **Management Commands**  
    
  - Use commands like `migrate`, `makemigrations`, `flush`, `sqlmigrate`, many more.


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
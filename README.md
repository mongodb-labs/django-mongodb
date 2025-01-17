# Django MongoDB Backend

This backend is currently in development and is not advised for Production workflows. Backwards incompatible
changes may be made without notice. We welcome your feedback as we continue to
explore and build. The best way to share this is via our [MongoDB Community Forum](https://www.mongodb.com/community/forums/tag/python)

## Install

The development version of this package supports Django 5.0.x. To install it:

`pip install django-mongodb-backend`

## Get Started

This tutorial shows you how to create a Django app, connect to a MongoDB cluster hosted on MongoDB Atlas, and interact with data in your cluster.

### Start a Project

From your shell, run the following command to create a new Django project called example based on a custom template:

```bash
$ django-admin startproject example --template https://github.com/mongodb-labs/django-mongodb-project/archive/refs/heads/5.0.x.zip
```

### Create a Connection String

Check out [Create a Connection String](https://deploy-preview-132--docs-pymongo.netlify.app/get-started/create-a-connection-string/) in our documentation to learn how to obtain a free MongoDB Atlas cluster.

Once finished, your URI should look something like this:
```bash
mongodb+srv://<username>:<password>@samplecluster.jkiff1s.mongodb.net/?retryWrites=true&w=majority&appName=SampleCluster
```
Replace the `<username>` and `<password>` placeholders with your database user's username and password.

Then, specify a connection to your example database from the Atlas sample datasets by adding it after the hostname, as shown in the following example:

```bash
mongodb+srv://<username>:<password>@samplecluster.jkiff1s.mongodb.net/<DATABASE_NAME>?retryWrites=true&w=majority&appName=SampleCluster
```

Replacing `<DATABASE_NAME>` with your database name of choice.


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

Once you've done that, you'll see messages saying you haven't run migrations yet. Make sure to run this command:
```bash
python manage.py migrate
```
### Create an app
An app is a web application that does something – e.g., a blog system, a database of public records or a small poll app.

From your project's root directory, run the following command to create a new Django app called polls based on a custom template:

```bash
python manage.py startapp polls --template https://github.com/mongodb-labs/django-mongodb-app/archive/refs/heads/5.0.x.zip
```

This will register a new `polls` app in your project, and provide the necessary files to have your polls app be a registered in `INSTALLED_APPS` within `example/settings.py` setting. It’ll look like this:

```python
INSTALLED_APPS = [
    "polls.apps.PollsConfig",
    'example.apps.MongoAdminConfig',
    'example.apps.MongoAuthConfig',
    'example.apps.MongoContentTypesConfig',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]
```

### Make a Django Model

Go to `example/polls/models.py` and paste this example code to creat a `Poll` and `Question` model.

```python
from django.db import models


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
```

With your new models defined and configs set, call the `makemigrations` command from the root of your directory.
```bash
python manage.py makemigrations polls
```

### Query your data
Hop into the interactive Python shell provided by the Django api with this command:
```bash
python manage.py shell
```

Within the shell, play around with creating, reading, updating, and deleting your models. Here's a few steps to start (provided by django tutorial):
```python
>>> from polls.models import Choice, Question  # Import the model classes we just wrote.

# No questions are in the system yet.
>>> Question.objects.all()
<QuerySet []>

# Create a new Question.
# Support for time zones is enabled in the default settings file, so
# Django expects a datetime with tzinfo for pub_date. Use timezone.now()
# instead of datetime.datetime.now() and it will do the right thing.
>>> from django.utils import timezone
>>> q = Question(question_text="What's new?", pub_date=timezone.now())

# Save the object into the database. You have to call save() explicitly.
>>> q.save()

# Now it has an ID.
>>> q.id
1

# Access model field values via Python attributes.
>>> q.question_text
"What's new?"
>>> q.pub_date
datetime.datetime(2012, 2, 26, 13, 0, 0, 775217, tzinfo=datetime.timezone.utc)

# Change values by changing the attributes, then calling save().
>>> q.question_text = "What's up?"
>>> q.save()

# objects.all() displays all the questions in the database.
>>> Question.objects.all()
<QuerySet [<Question: Question object (1)>]>
```

Check out the Django [database API](https://docs.djangoproject.com/en/5.1/topics/db/queries/) documentation for more information on queries.

### View the Admin Dashboard
1. Make the poll app modifiable in the admin site. Route to the `polls/admin.py` file and include this code:
   ```python
   from django.contrib import admin

   from .models import Question

   admin.site.register(Question)
   ```
2. Create a superuser. When prompted, enter your desired username, password, and email address.
   ```bash
   $ python manage.py createsuperuser
   ```
3. Start the Development Server
   ```bash
   $ python manage.py runserver
   ```
4. Open a web browser and go to “/admin/” on your local domain – e.g., http://127.0.0.1:8000/admin/. Login and explore the free admin functionality!

### Congrats! You've made your first Django MongoDB Backend Project

Check back soon as we aim to provide more links that will dive deeper into our library!

<!-- * Developer Notes
* Capabilities & Limitations
* Tutorials
* Troubleshooting -->

### Issues & Help

We're glad to have such a vibrant community of users of Django MongoDB Backend. We recommend seeking support for general questions through the MongoDB Community Forums.

#### Bugs / Feature Requests
To report a bug or to request a new feature in Django MongoDB Backend, please open an issue in JIRA, our issue-management tool, using the following steps:

1. [Create a JIRA account.](https://jira.mongodb.org/)

2. Navigate to the [Python Integrations project](https://jira.mongodb.org/projects/INTPYTHON/).

3. Click **Create Issue**. Please provide as much information as possible about the issue and the steps to reproduce it.

Bug reports in JIRA for the Django MongoDB Backend project can be viewed by everyone.

If you identify a security vulnerability in the driver or in any other MongoDB project, please report it according to the instructions found in [Create a Vulnerability Report](https://www.mongodb.com/docs/manual/tutorial/create-a-vulnerability-report/).
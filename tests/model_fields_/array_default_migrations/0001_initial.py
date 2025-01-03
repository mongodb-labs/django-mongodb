from django.db import migrations, models

import django_mongodb


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="IntegerArrayDefaultModel",
            fields=[
                (
                    "id",
                    django_mongodb.fields.ObjectIdAutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "field",
                    django_mongodb.fields.ArrayField(models.IntegerField(), size=None),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
    ]

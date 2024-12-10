from django.db import migrations, models

import django_mongodb


class Migration(migrations.Migration):
    dependencies = [
        ("model_fields_", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="integerarraydefaultmodel",
            name="field_2",
            field=django_mongodb.fields.ArrayField(models.IntegerField(), default=[], size=None),
            preserve_default=False,
        ),
    ]

from django.db import migrations

import core.utils


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bucket',
            name='color',
            field=core.fields.ColorField(default=core.utils.random_color, max_length=7),
        ),
    ]

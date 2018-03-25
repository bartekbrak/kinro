import core.utils
from django.db import migrations


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

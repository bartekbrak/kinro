from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_randomize_bucket_color'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='bucket',
            unique_together=set([('title', 'url')]),
        ),
    ]

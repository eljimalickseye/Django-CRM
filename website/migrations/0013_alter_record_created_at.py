# Generated by Django 5.0.2 on 2024-03-05 15:02

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0012_alter_record_commentaire'),
    ]

    operations = [
        migrations.AlterField(
            model_name='record',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]

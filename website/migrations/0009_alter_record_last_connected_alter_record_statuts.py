# Generated by Django 5.0.2 on 2024-02-28 10:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0008_alter_record_statuts'),
    ]

    operations = [
        migrations.AlterField(
            model_name='record',
            name='last_connected',
            field=models.DateField(null=True),
        ),
        migrations.AlterField(
            model_name='record',
            name='statuts',
            field=models.CharField(max_length=20, null=True),
        ),
    ]

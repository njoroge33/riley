# Generated by Django 3.1.4 on 2020-12-29 21:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('delivery', '0002_auto_20201230_0014'),
    ]

    operations = [
        migrations.AlterField(
            model_name='request',
            name='delivery_location',
            field=models.JSONField(),
        ),
    ]

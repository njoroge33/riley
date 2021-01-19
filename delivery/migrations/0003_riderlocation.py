# Generated by Django 3.1.4 on 2021-01-11 09:02

from django.db import migrations, models
import django.db.models.deletion
import django_mysql.models


class Migration(migrations.Migration):

    dependencies = [
        ('delivery', '0002_auto_20210105_1400'),
    ]

    operations = [
        migrations.CreateModel(
            name='RiderLocation',
            fields=[
                ('request', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='delivery.request')),
                ('current_location', django_mysql.models.ListCharField(models.CharField(max_length=50), max_length=9801, size=99)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('rider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='delivery.rider')),
            ],
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-11-01 19:56
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('todolist', '0002_auto_20171101_2254'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usertoken',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]

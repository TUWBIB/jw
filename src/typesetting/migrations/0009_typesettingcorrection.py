# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-04-16 11:39
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0033_set_default_xml_galley_xsl'),
        ('typesetting', '0008_auto_20200316_1231'),
    ]

    operations = [
        migrations.CreateModel(
            name='TypesettingCorrection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_requested', models.DateTimeField(auto_now_add=True)),
                ('date_completed', models.DateTimeField(blank=True, null=True)),
                ('date_declined', models.DateTimeField(blank=True, null=True)),
                ('file_checksum', models.CharField(blank=True, max_length=255, null=True)),
                ('galley', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.Galley')),
                ('task', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='corrections', to='typesetting.TypesettingAssignment')),
            ],
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2022-05-10 09:53
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('repository', '0028_merge_20220223_1229'),
    ]

    operations = [
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_assigned', models.DateTimeField(auto_now_add=True, null=True)),
                ('date_due', models.DateField(blank=True, null=True, verbose_name='Due date')),
                ('date_accepted', models.DateTimeField(blank=True, null=True)),
                ('date_completed', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('new', 'New'), ('accepted', 'Accepted'), ('declined', 'Declined'), ('complete', 'Complete'), ('withdrawn', 'Withdrawn')], max_length=10)),
                ('access_code', models.UUIDField(default=uuid.uuid4)),
                ('anonymous', models.BooleanField(default=False)),
                ('status_reason', models.TextField(blank=True, help_text='Information supplied by a reviewer when declining or completing a review or by staff withdrawing a review', null=True)),
                ('notification_sent', models.BooleanField(default=False)),
                ('comment', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='repository.Comment')),
                ('manager', models.ForeignKey(help_text='The manager making the review request.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='review_manager', to=settings.AUTH_USER_MODEL)),
                ('preprint', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='repository.Preprint')),
                ('reviewer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='review_reviewer', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='repository',
            name='manager_review_status_change',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='repository',
            name='review_helper',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='repository',
            name='review_invitation',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='repository',
            name='reviewer_review_status_change',
            field=models.TextField(blank=True, null=True),
        ),
    ]

# Generated by Django 4.2.14 on 2024-07-26 13:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0105_migrate_affiliation_institution'),
        ('submission', '0083_article_jats_article_type_override_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='frozenauthor',
            name='country',
        ),
        migrations.RemoveField(
            model_name='frozenauthor',
            name='department',
        ),
        migrations.RemoveField(
            model_name='frozenauthor',
            name='institution',
        ),
    ]

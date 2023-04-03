# Generated by Django 3.2.16 on 2023-01-20 15:46

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0078_auto_20230120_1546'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('press', '0027_auto_20220107_1219'),
        ('journal', '0057_verbose_names_20230301_1914'),
        ('submission', '0069_delete_blank_keywords'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='journal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='journal.journal'),
        ),
        migrations.AlterField(
            model_name='article',
            name='preprint_journal_article',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='submission.article'),
        ),
        migrations.AlterField(
            model_name='field',
            name='journal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='journal.journal'),
        ),
        migrations.AlterField(
            model_name='field',
            name='press',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='press.press'),
        ),
        migrations.AlterField(
            model_name='frozenauthor',
            name='author',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='frozenauthor',
            name='country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.country'),
        ),
        migrations.AlterField(
            model_name='note',
            name='creator',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='publishernote',
            name='creator',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='submissionconfiguration',
            name='default_license',
            field=models.ForeignKey(blank=True, help_text='The default license applied when no option is presented', null=True, on_delete=django.db.models.deletion.SET_NULL, to='submission.licence'),
        ),
        migrations.AlterField(
            model_name='submissionconfiguration',
            name='default_section',
            field=models.ForeignKey(blank=True, help_text='The default section of articles when no option is presented', null=True, on_delete=django.db.models.deletion.SET_NULL, to='submission.section'),
        ),
    ]
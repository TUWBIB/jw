from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0019_auto_20240328_1743'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='client_ip',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='loginattempt',
            name='ip_address',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
    ]

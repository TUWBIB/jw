# Generated by Django 4.2.16 on 2025-01-17 16:21

from django.db import migrations
from django.db.models import Q


def get_or_create_location_with_country_only(apps, old_country=None):
    if not old_country:
        return None

    Location = apps.get_model("core", "Location")
    location, created = Location.objects.get_or_create(
        name='',
        country=old_country,
    )
    return location


def create_organization(apps, old_institution=None, old_country=None):
    if not old_institution:
        return None

    Organization = apps.get_model("core", "Organization")
    OrganizationName = apps.get_model("core", "OrganizationName")

    organization = Organization.objects.create()
    location = get_or_create_location_with_country_only(apps, old_country)
    if location:
        organization.locations.add(location)
    OrganizationName.objects.create(
        value=old_institution,
        custom_label_for=organization,
    )
    return organization


def create_affiliation(
    apps,
    old_institution,
    old_department,
    old_country,
    account=None,
    frozen_author=None,
    preprint_author=None,
):
    ControlledAffiliation = apps.get_model("core", "ControlledAffiliation")
    organization = create_organization(apps, old_institution, old_country)

    affiliation, _created = ControlledAffiliation.objects.get_or_create(
        account=account,
        frozen_author=frozen_author,
        preprint_author=preprint_author,
        organization=organization,
        department=old_department,
        is_primary=True,
    )
    return affiliation


def migrate_affiliation_institution(apps, schema_editor):
    Account = apps.get_model("core", "Account")
    FrozenAuthor = apps.get_model("submission", "FrozenAuthor")
    PreprintAuthor = apps.get_model("repository", "PreprintAuthor")

    for account in Account.objects.filter(
        ~Q(institution__exact='')
        | ~Q(department__exact='')
    ):
        create_affiliation(
            apps,
            account.institution,
            account.department,
            account.country,
            account=account,
        )

    for frozen_author in FrozenAuthor.objects.filter(
        ~Q(institution__exact='')
        | ~Q(department__exact='')
    ):
        create_affiliation(
            apps,
            frozen_author.institution,
            frozen_author.department,
            frozen_author.country,
            frozen_author=frozen_author,
        )

    for preprint_author in PreprintAuthor.objects.filter(
        controlledaffiliation__isnull=True,
    ):
        create_affiliation(
            apps,
            preprint_author.affiliation,
            '',
            None,
            preprint_author=preprint_author,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0104_location_organization_affiliation'),
    ]

    operations = [
        migrations.RunPython(
            migrate_affiliation_institution,
            reverse_code=migrations.RunPython.noop
        ),
    ]

__copyright__ = "Copyright 2025 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.shortcuts import reverse
from django.test import TestCase, override_settings

from utils.testing import helpers

from core import model_utils as model_utils


class TestModelUtils(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.request = helpers.get_request(
            press=cls.press,
            journal=cls.journal_one,
        )

    @override_settings(URL_CONFIG="path")
    def test_auth_success_url_with_next(self):
        next_url = '/special/path/'
        self.assertEqual(
            self.request.site_type.auth_success_url(next_url=next_url),
            '/special/path/',
        )

    @override_settings(URL_CONFIG="path")
    def test_auth_success_url_with_journal(self):
        self.assertEqual(
            self.request.site_type.auth_success_url(),
            reverse('core_dashboard'),
        )

    @override_settings(URL_CONFIG="path")
    def test_auth_success_url_with_repository(self):
        self.repository, self.subject = helpers.create_repository(
            self.press,
            [],
            [],
        )
        self.request.site_type = self.repository
        self.assertEqual(
            self.request.site_type.auth_success_url(),
            reverse('repository_dashboard'),
        )

    @override_settings(URL_CONFIG="path")
    def test_auth_success_url_with_press(self):
        self.request.site_type = self.press
        self.assertEqual(
            self.request.site_type.auth_success_url(),
            reverse('website_index'),
        )

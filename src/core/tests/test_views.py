__copyright__ = "Copyright 2024 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from mock import patch
from uuid import uuid4

from django.test import Client, TestCase, override_settings

from utils.testing import helpers
from utils import orcid

from core import models as core_models
from core import views as core_views


class CoreViewTestsWithData(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        helpers.create_roles(['author', 'editor', 'reviewer'])
        cls.themes = ['clean', 'OLH', 'material']
        cls.user_email = 'sukv8golcvwervs0y7e5@example.org'
        cls.user_password = 'xUMXW1oXn2l8L26Kixi2'
        cls.user = core_models.Account.objects.create_user(
            cls.user_email,
            password=cls.user_password,
        )
        cls.user.confirmation_code = uuid4()

        cls.user.is_active = True
        cls.user_orcid = '0000-0001-2345-6789'
        cls.user_orcid_uri = f'https://orcid.org/{cls.user_orcid}/'
        cls.user.orcid = cls.user_orcid_uri
        cls.orcid_token_uuid = uuid4()
        cls.orcid_token = core_models.OrcidToken.objects.create(
            token=cls.orcid_token_uuid,
            orcid=cls.user_orcid_uri,
        )
        cls.reset_token_uuid = uuid4()
        cls.reset_token = core_models.PasswordResetToken.objects.create(
            account=cls.user,
            token=cls.reset_token_uuid,
        )
        cls.user.save()

        # The raw unicode string of a 'next' URL
        cls.next_url_raw = '/target/page/?a=b&x=y'

        # The unicode string url-encoded with safe='/'
        cls.next_url_encoded = '/target/page/%3Fa%3Db%26x%3Dy'

        # The unicode string url-encoded with safe=''
        cls.next_url_encoded_no_safe = '%2Ftarget%2Fpage%2F%3Fa%3Db%26x%3Dy'

        # The unicode string url-encoded with safe=''
        # two times
        cls.next_url_doubly_encoded = '%252Ftarget%252Fpage%252F%253Fa%253Db%2526x%253Dy'

        # The state parameter with action=login
        cls.state_login = orcid.encode_state(cls.next_url_raw, 'login')

        # The state parameter including login and the next URL
        cls.state_register = orcid.encode_state(cls.next_url_raw, 'register')

        # next_url_encoded with its 'next' key
        cls.next_url_query_string = 'next=/target/page/%3Fa%3Db%26x%3Dy'

        # The core_login url with encoded next url
        cls.core_login_with_next = '/login/?next=/target/page/%3Fa%3Db%26x%3Dy'

        # The core_register url with encoded next url
        cls.core_register_with_next = '/register/?next=/target/page/%3Fa%3Db%26x%3Dy'

    def setUp(self):
        self.client = Client()


class AccountManagementTemplateTests(CoreViewTestsWithData):

    def test_user_login(self):
        url = '/login/'
        data = {}
        template = 'admin/core/accounts/login.html'
        response = self.client.get(url, data)
        self.assertTemplateUsed(response, template)

    def test_get_reset_token(self):
        url = '/reset/step/1/'
        data = {}
        template = 'admin/core/accounts/get_reset_token.html'
        response = self.client.get(url, data)
        self.assertTemplateUsed(response, template)

    def test_reset_password(self):
        url = f'/reset/step/2/{self.reset_token_uuid}/'
        data = {}
        template = 'admin/core/accounts/reset_password.html'
        response = self.client.get(url, data)
        self.assertTemplateUsed(response, template)

    def test_register(self):
        url = '/register/step/1/'
        data = {}
        template = 'admin/core/accounts/register.html'
        response = self.client.get(url, data)
        self.assertTemplateUsed(response, template)

    def test_orcid_registration(self):
        url = f'/register/step/orcid/{self.orcid_token_uuid}/'
        data = {}
        template = 'admin/core/accounts/orcid_registration.html'
        response = self.client.get(url, data)
        self.assertTemplateUsed(response, template)

    def test_activate_account(self):
        url = f'/register/step/2/{self.user.confirmation_code}/'
        data = {}
        template = 'admin/core/accounts/activate_account.html'
        response = self.client.get(url, data)
        self.assertTemplateUsed(response, template)

    def test_edit_profile(self):
        self.client.login(username=self.user_email, password=self.user_password)
        url = '/profile/'
        data = {}
        template = 'admin/core/accounts/edit_profile.html'
        response = self.client.get(url, data)
        self.assertTemplateUsed(response, template)


class GenericFacetedListViewTests(CoreViewTestsWithData):
    """
    A test suite for the core logic in GenericFacetedListView.
    Uses JournalUsers and BaseUserList to get access to URLs and facets
    as they are actually used, and so to help these tests catch
    potential regressions.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # Journal 1 users
        cls.journal_one_authors = []
        for num in range(0,30):
            cls.journal_one_authors.append(
                helpers.create_user(
                    f'author_{num}_eblazi52pnxnivl4vox2@example.org',
                    roles=['author'],
                    journal=cls.journal_one,
                )
            )
        cls.journal_one_editor = helpers.create_user(
            'editor_q2flnkp5ryxqtr5iuvvl@example.org',
            roles=['editor'],
            journal=cls.journal_one,
        )
        cls.journal_one_editor.is_active = True
        cls.journal_one_editor.save()
        cls.journal_one_reviewer = cls.journal_one_authors[0]
        cls.journal_one_reviewer.add_account_role('reviewer', cls.journal_one)

        # Journal 2 users
        cls.journal_two_authors = []
        # The first five authors are the same as journal 1
        for author in cls.journal_one_authors[:5]:
            cls.journal_two_authors.append(
                author.add_account_role('author', cls.journal_two)
            )
        # The next five are new
        for num in range(0,5):
            cls.journal_two_authors.append(
                helpers.create_user(
                    f'author_{num}_c9zn2ag7efuyecanpyl1@example.org',
                    roles=['author'],
                    journal=cls.journal_two,
                )
            )
        # Journal 2's reviewer is the same as journal 1's 15th author
        cls.journal_two_reviewer = cls.journal_one_authors[15]
        cls.journal_two_reviewer.add_account_role(
            'reviewer',
            journal=cls.journal_two,
        )

    def setUp(self):
        super().setUp()
        self.client.force_login(self.journal_one_editor)

    def test_get_paginate_by_default(self):
        url = '/user/all/'
        data = {}
        response = self.client.get(url, data)
        self.assertEqual(response.context['paginate_by'], 25)
        self.assertEqual(len(response.context['account_list']), 25)

    def test_get_paginate_by_all(self):
        url = '/user/all/'
        data = {
            'paginate_by': 'all',
        }
        response = self.client.get(url, data)
        self.assertGreater(len(response.context['account_list']), 25)

    def test_get_facet_form_foreign_key(self):
        """
        Checks that only account roles in Journal One
        are included in facet counts.
        """
        url = '/user/all/'
        data = {}
        response = self.client.get(url, data)
        form = response.context['facet_form']
        self.assertEqual(
            form.fields['accountrole__role__pk'].choices,
            [
                (1, 'Author (30)'),
                (2, 'Editor (1)'),
                (3, 'Reviewer (1)'),
            ]
        )

    def test_get_queryset_foreign_key(self):
        """
        Checks that only account roles in Journal One
        are included in queryset results.
        """
        url = '/user/all/'
        data = {
            'accountrole__role__pk': 3, # filter to reviewers
        }
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['account_list']), 1)


class UserLoginTests(CoreViewTestsWithData):

    def test_is_authenticated_redirects_to_next(self):
        self.client.login(username=self.user_email, password=self.user_password)
        data = {
            'next': self.next_url_raw,
        }
        response = self.client.get('/login/', data, follow=True)
        self.assertIn((self.next_url_raw, 302), response.redirect_chain)

    @patch('core.views.authenticate')
    def test_login_success_redirects_to_next(self, authenticate):
        authenticate.return_value = self.user
        data = {
            'user_name': self.user_email,
            'user_pass': self.user_password,
            'next': self.next_url_raw,
        }
        response = self.client.post('/login/', data, follow=True)
        self.assertIn((self.next_url_raw, 302), response.redirect_chain)

    @override_settings(ENABLE_OIDC=True)
    def test_oidc_link_has_next(self):
        data = {
            'next': self.next_url_raw,
        }
        response = self.client.get('/login/', data)
        self.assertIn(
            f'/oidc/authenticate/?next={self.next_url_encoded}',
            response.content.decode(),
        )

    @override_settings(ENABLE_ORCID=True)
    def test_orcid_link_has_next(self):
        data = {
            'next': self.next_url_raw,
        }
        response = self.client.get('/login/', data)
        self.assertIn(
            f'/login/orcid/?next={self.next_url_encoded}',
            response.content.decode(),
        )

    def test_forgot_password_link_has_next(self):
        data = {
            'next': self.next_url_raw,
        }
        response = self.client.get('/login/', data)
        self.assertIn(
            f'/reset/step/1/?next={self.next_url_encoded}',
            response.content.decode(),
        )

    def test_register_link_has_next(self):
        data = {
            'next': self.next_url_raw,
        }
        response = self.client.get('/login/', data)
        self.assertIn(
            f'/register/step/1/?next={self.next_url_encoded}',
            response.content.decode(),
        )


class UserLoginOrcidTests(CoreViewTestsWithData):

    @override_settings(ENABLE_ORCID=False)
    def test_orcid_disabled_redirects_with_next(self):
        data = {
            'next': self.next_url_raw,
        }
        response = self.client.get('/login/orcid/', data, follow=True)
        self.assertIn(self.next_url_encoded, response.redirect_chain[0][0])

    @override_settings(ENABLE_ORCID=True)
    def test_no_orcid_code_redirects_with_next(self):
        data = {
            'next': self.next_url_raw,
        }
        response = self.client.get('/login/orcid/', data)
        self.assertIn(self.next_url_doubly_encoded, response.url)

    @patch('core.views.orcid.retrieve_tokens')
    @override_settings(ENABLE_ORCID=True)
    def test_no_orcid_id_redirects_with_next(self, retrieve_tokens):
        retrieve_tokens.return_value = None
        data = {
            'code': '12345',
            'next': self.next_url_raw,
        }
        response = self.client.get('/login/orcid/', data, follow=True)
        self.assertIn((self.core_login_with_next, 302), response.redirect_chain)

    @patch('core.views.orcid.retrieve_tokens')
    @override_settings(ENABLE_ORCID=True)
    def test_action_login_account_found_redirects_to_next(
        self,
        retrieve_tokens,
    ):
        retrieve_tokens.return_value = self.user_orcid_uri
        data = {
            'code': '12345',
            'next': self.next_url_raw,
        }
        response = self.client.get('/login/orcid/', data, follow=True)
        self.assertIn((self.next_url_raw, 302), response.redirect_chain)

    @patch('core.views.orcid.get_orcid_record_details')
    @patch('core.views.orcid.retrieve_tokens')
    @override_settings(ENABLE_ORCID=True)
    def test_action_login_matching_email_redirects_to_next(
        self,
        retrieve_tokens,
        orcid_details,
    ):
        # Change ORCID so it doesn't work
        retrieve_tokens.return_value = 'https://orcid.org/0000-0001-2312-3123'

        # Return an email that will work
        orcid_details.return_value = {'emails': [self.user_email]}

        data = {
            'code': '12345',
            'state': self.state_login,
        }
        response = self.client.get('/login/orcid/', data, follow=True)
        self.assertIn((self.next_url_raw, 302), response.redirect_chain)

    @patch('core.views.orcid.get_orcid_record_details')
    @patch('core.views.orcid.retrieve_tokens')
    @override_settings(ENABLE_ORCID=True)
    def test_action_login_failure_redirects_with_next(
        self,
        retrieve_tokens,
        orcid_details,
    ):
        # Change ORCID so it doesn't work
        retrieve_tokens.return_value = 'https://orcid.org/0000-0001-2312-3123'

        orcid_details.return_value = {'emails': []}
        data = {
            'code': '12345',
            'state': self.state_login,
        }
        response = self.client.get('/login/orcid/', data, follow=True)
        self.assertIn(
            self.next_url_query_string,
            response.redirect_chain[0][0],
        )

    @patch('core.views.orcid.retrieve_tokens')
    @override_settings(ENABLE_ORCID=True)
    def test_action_register_redirects_with_next(self, retrieve_tokens):
        retrieve_tokens.return_value = self.user_orcid_uri
        data = {
            'code': '12345',
            'next': self.next_url_raw,
            'action': 'register',
        }
        response = self.client.get('/login/orcid/', data, follow=True)
        self.assertIn(
            self.next_url_query_string,
            response.redirect_chain[0][0],
        )


class GetResetTokenTests(CoreViewTestsWithData):

    @patch('core.views.logic.start_reset_process')
    def test_start_reset_redirects_with_next(self, _start_reset):
        data = {
            'email_address': self.user_email,
            'next': self.next_url_raw,
        }
        response = self.client.post('/reset/step/1/', data, follow=True)
        self.assertIn((self.core_login_with_next, 302), response.redirect_chain)


class ResetPasswordTests(CoreViewTestsWithData):

    @patch('core.views.logic.password_policy_check')
    def test_reset_password_form_valid_redirects_with_next(self, password_check):
        password_check.return_value = None
        data = {
            'password_1': 'qsX1roLama3ADotEopfq',
            'password_2': 'qsX1roLama3ADotEopfq',
            'next': self.next_url_raw,
        }
        reset_step_2_path = f'/reset/step/2/{self.reset_token.token}/'
        response = self.client.post(reset_step_2_path, data, follow=True)
        self.assertIn((self.core_login_with_next, 302), response.redirect_chain)


class RegisterTests(CoreViewTestsWithData):

    @patch('core.views.logic.password_policy_check')
    @override_settings(CAPTCHA_TYPE='')
    @override_settings(ENABLE_ORCID=True)
    def test_register_email_form_valid_redirects_with_next(self, password_check):
        password_check.return_value = None
        data = {
            'email': 'kjhsaqccxf7qfwirhqia@example.org',
            'password_1': 'qsX1roLama3ADotEopfq',
            'password_2': 'qsX1roLama3ADotEopfq',
            'first_name': 'New',
            'last_name': 'User',
            'next': self.next_url_raw,
        }
        response = self.client.post('/register/step/1/', data, follow=True)
        self.assertIn((self.core_login_with_next, 302), response.redirect_chain)

    @patch('core.views.orcid.get_orcid_record_details')
    @patch('core.views.logic.password_policy_check')
    @override_settings(CAPTCHA_TYPE='')
    @override_settings(ENABLE_ORCID=True)
    def test_register_orcid_form_valid_redirects_to_next(
        self,
        password_check,
        get_orcid_details
    ):
        get_orcid_details.return_value = {
            'first_name': 'New',
            'last_name': 'User',
            'emails': ['kjhsaqccxf7qfwirhqia@example.org'],
            'orcid': self.user_orcid,
            'uri': self.user_orcid_uri,
        }
        password_check.return_value = None
        data = {
            'first_name': 'New',
            'last_name': 'User',
            'email': 'kjhsaqccxf7qfwirhqia@example.org',
            'orcid': self.user_orcid,
            'password_1': 'qsX1roLama3ADotEopfq',
            'password_2': 'qsX1roLama3ADotEopfq',
            'next': self.next_url_raw,
        }
        post_url = f'/register/step/1/{self.orcid_token_uuid}/'
        response = self.client.post(post_url, data, follow=True)
        self.assertIn((self.next_url_raw, 302), response.redirect_chain)


    @patch('core.views.orcid.get_orcid_record_details')
    @patch('core.views.logic.password_policy_check')
    @override_settings(CAPTCHA_TYPE='')
    @override_settings(ENABLE_ORCID=True)
    def test_register_orcid_form_valid_redirects_to_next(
        self,
        password_check,
        get_orcid_details
    ):
        get_orcid_details.return_value = {
            'first_name': 'New',
            'last_name': 'User',
            'emails': ['kjhsaqccxf7qfwirhqia@example.org'],
            'orcid': self.user_orcid,
            'uri': self.user_orcid_uri,
        }
        password_check.return_value = None
        data = {
            'first_name': 'New',
            'last_name': 'User',
            'email': 'kjhsaqccxf7qfwirhqia@example.org',
            'password_1': 'qsX1roLama3ADotEopfq',
            'password_2': 'qsX1roLama3ADotEopfq',
            'next': self.next_url_raw,
        }
        post_url = f'/register/step/1/{self.orcid_token_uuid}/'
        response = self.client.post(post_url, data, follow=True)
        self.assertIn((self.next_url_raw, 302), response.redirect_chain)


class OrcidRegistrationTests(CoreViewTestsWithData):

    def test_login_link_has_next(self):
        data = {
            'next': self.next_url_raw,
        }
        orcid_registration_path = f'/register/step/orcid/{self.orcid_token_uuid}/'
        response = self.client.get(orcid_registration_path, data)
        self.assertIn(
            f'/login/?next={self.next_url_encoded}',
            response.content.decode(),
        )

    def test_forgot_password_link_has_next(self):
        data = {
            'next': self.next_url_raw,
        }
        orcid_registration_path = f'/register/step/orcid/{self.orcid_token_uuid}/'
        response = self.client.get(orcid_registration_path, data)
        self.assertIn(
            f'/reset/step/1/?next={self.next_url_encoded}',
            response.content.decode(),
        )

    def test_register_link_has_next(self):
        data = {
            'next': self.next_url_raw,
        }
        orcid_registration_path = f'/register/step/orcid/{self.orcid_token_uuid}/'
        response = self.client.get(orcid_registration_path, data)
        self.assertIn(
            f'/register/step/1/{self.orcid_token_uuid}/?next={self.next_url_encoded}',
            response.content.decode(),
        )


class ActivateAccountTests(CoreViewTestsWithData):

    @patch('core.views.models.Account.objects.get')
    def test_activate_success_redirects_to_next(self, objects_get):
        objects_get.return_value = self.user
        data = {
            'next': self.next_url_raw,
        }
        response = self.client.post('/register/step/2/12345/', data, follow=True)
        self.assertIn((self.core_login_with_next, 302), response.redirect_chain)

    @patch('core.views.models.Account.objects.get')
    def test_login_link_has_next(self, objects_get):
        objects_get.return_value = None
        data = {
            'next': self.next_url_raw,
        }
        response = self.client.get('/register/step/2/12345/', data)
        self.assertIn(
            self.core_login_with_next,
            response.content.decode(),
        )


class ReturnURLTests(CoreViewTestsWithData):
    """
    These tests check that the url_with_return
    template tag is present in public-facing templates where
    the user has an option to log in or register.
    """

    def test_journal_homepage_account_links_have_return(self):
        for theme in self.themes:
            response = self.client.get('/', data={'theme': theme})
            content = response.content.decode()
            self.assertIn('/login/?next=/', content)
            self.assertNotIn('"/login/"', content)
            self.assertIn('/register/step/1/?next=/', content)
            self.assertNotIn('"/register/step/1/"', content)

    def test_journal_submissions_account_links_have_return(self):
        for theme in self.themes:
            response = self.client.get('/submissions/', data={'theme': theme})
            content = response.content.decode()
            self.assertIn('/login/?next=/submissions/', content)
            self.assertNotIn('"/login/"', content)
            self.assertIn('/register/step/1/?next=/submissions/', content)
            self.assertNotIn('"/register/step/1/"', content)

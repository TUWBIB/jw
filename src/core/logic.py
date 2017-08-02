__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


import os
from PIL import Image
import uuid
from importlib import import_module

from django.conf import settings
from django.utils.translation import get_language
from django.contrib.auth import logout
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from core import models, files, plugin_installed_apps
from utils.function_cache import cache
from review import models as review_models
from utils import render_template, notify_helpers, setting_handler
from submission import models as submission_models


def send_reset_token(request, reset_token):
    context = {'reset_token': reset_token}
    if not request.journal:
        message = render_template.get_message_content(request, context, request.press.password_reset_text,
                                                      template_is_setting=True)
    else:
        message = render_template.get_message_content(request, context, 'password_reset')
    notify_helpers.send_email_with_body_from_user(request, 'subject_password_reset', reset_token.account.email, message)


def send_confirmation_link(request, new_user):
    context = {'user': new_user}
    if not request.journal:
        message = render_template.get_message_content(request, context, request.press.registration_text,
                                                      template_is_setting=True)
    else:
        message = render_template.get_message_content(request, context, 'new_user_registration')
    notify_helpers.send_slack(request, 'New registration: {0}'.format(new_user.full_name()), ['slack_admins'])
    notify_helpers.send_email_with_body_from_user(request, 'subject_new_user_registration', new_user.email, message)


def resize_and_crop(img_path, size, crop_type='middle'):
    """
    Resize and crop an image to fit the specified size.
    """

    # If height is higher we resize vertically, if not we resize horizontally
    img = Image.open(img_path)

    # Get current and desired ratio for the images
    img_ratio = img.size[0] / float(img.size[1])
    ratio = size[0] / float(size[1])
    # The image is scaled/cropped vertically or horizontally depending on the ratio
    if ratio > img_ratio:
        img = img.resize((size[0], int(size[0] * img.size[1] // img.size[0])),
                         Image.ANTIALIAS)
        # Crop in the top, middle or bottom
        if crop_type == 'top':
            box = (0, 0, img.size[0], size[1])
        elif crop_type == 'middle':
            box = (0, (img.size[1] - size[1]) // 2, img.size[0], (img.size[1] + size[1]) // 2)
        elif crop_type == 'bottom':
            box = (0, img.size[1] - size[1], img.size[0], img.size[1])
        else:
            raise ValueError('ERROR: invalid value for crop_type')
        img = img.crop(box)

    elif ratio < img_ratio:
        img = img.resize((size[0], int(size[0] * img.size[1] // img.size[0])), Image.ANTIALIAS)
        # Crop in the top, middle or bottom
        if crop_type == 'top':
            box = (0, 0, size[0], img.size[1])
        elif crop_type == 'middle':
            horizontal_padding = (size[0] - img.size[0]) // 2
            vertical_padding = (size[1] - img.size[1]) // 2

            offset_tuple = (horizontal_padding, vertical_padding)

            final_thumb = Image.new(mode='RGBA', size=size, color=(255, 255, 255, 0))
            final_thumb.paste(img, offset_tuple)  # paste the thumbnail into the full sized image

            final_thumb.save(img_path)
            return
        elif crop_type == 'bottom':
            box = (img.size[0] - size[0], 0, img.size[0], img.size[1])
        else:
            raise ValueError('ERROR: invalid value for crop_type')

        img = img.crop(box)
    else:
        img = img.resize((size[0], size[1]), Image.ANTIALIAS)

    img.save(img_path)


def settings_for_context(request):
    if request.journal:
        return cached_settings_for_context(request.journal, get_language())
    else:
        return {}


@cache(600)
def cached_settings_for_context(journal, language):
    setting_groups = ['general', 'crosscheck']
    _dict = {group: {} for group in setting_groups}

    for group in setting_groups:
        settings = models.Setting.objects.filter(group__name=group)

        for setting in settings:
            _dict[group][setting.name] = setting_handler.get_setting(group, setting.name, journal,
                                                                     fallback=True).value

    return _dict


def process_setting_list(settings_to_get, type, journal):
    settings = []
    for setting in settings_to_get:
        settings.append({
            'name': setting,
            'object': setting_handler.get_setting(type, setting, journal),
        })

    return settings


def get_settings_to_edit(group, journal):

    review_form_choices = list()
    for form in review_models.ReviewForm.objects.filter(journal=journal):
        review_form_choices.append([form.pk, form])

    if group == 'submission':
        settings = [
            {'name': 'copyright_notice',
             'object': setting_handler.get_setting('general', 'copyright_notice', journal)
             },
            {'name': 'submission_checklist',
             'object': setting_handler.get_setting('general', 'submission_checklist', journal)
             },
            {'name': 'publication_fees',
             'object': setting_handler.get_setting('general', 'publication_fees', journal)
             },
            {'name': 'editors_for_notification',
             'object': setting_handler.get_setting('general', 'editors_for_notification', journal),
             'choices': journal.editor_pks()
             },
            {'name': 'limit_manuscript_types',
             'object': setting_handler.get_setting('general', 'limit_manuscript_types', journal),
             },
            {'name': 'submission_competing_interests',
             'object': setting_handler.get_setting('general', 'submission_competing_interests', journal),
             },
            {'name': 'focus_and_scope',
             'object': setting_handler.get_setting('general', 'focus_and_scope', journal),
             },
            {'name': 'publication_cycle',
             'object': setting_handler.get_setting('general', 'publication_cycle', journal),
             },
            {'name': 'peer_review_info',
             'object': setting_handler.get_setting('general', 'peer_review_info', journal),
             }
        ]
        setting_group = 'general'

    elif group == 'review':
        settings = [
            {
                'name': 'reviewer_guidelines',
                'object': setting_handler.get_setting('general', 'reviewer_guidelines', journal),
            },
            {
                'name': 'default_review_visibility',
                'object': setting_handler.get_setting('general', 'default_review_visibility', journal),
                'choices': review_models.review_visibilty()
            },
            {
                'name': 'default_review_days',
                'object': setting_handler.get_setting('general', 'default_review_days', journal),
            },
            {
                'name': 'enable_one_click_access',
                'object': setting_handler.get_setting('general', 'enable_one_click_access', journal),
            },
            {
                'name': 'draft_decisions',
                'object': setting_handler.get_setting('general', 'draft_decisions', journal),
            },
            {
                'name': 'default_review_form',
                'object': setting_handler.get_setting('general', 'default_review_form', journal),
                'choices': review_form_choices
            }
        ]
        setting_group = 'general'

    elif group == 'crossref':
        xref_settings = [
            'use_crossref', 'crossref_test', 'crossref_username', 'crossref_password', 'crossref_email',
            'crossref_name', 'crossref_prefix', 'crossref_registrant', 'doi_display_prefix', 'doi_display_suffix',
            'doi_pattern'
        ]

        settings = process_setting_list(xref_settings, 'Identifiers', journal)
        setting_group = 'Identifiers'

    elif group == 'crosscheck':
        xref_settings = [
            'enable', 'username', 'password'
        ]

        settings = process_setting_list(xref_settings, 'crosscheck', journal)
        setting_group = 'crosscheck'

    elif group == 'journal':
        journal_settings = [
            'journal_name', 'journal_issn', 'journal_theme', 'journal_description', 'is_secure',
            'enable_editorial_display', 'mulit_page_editorial', 'enable_editorial_images', 'main_contact', 'publisher_name', 'publisher_url',
            'maintenance_mode', 'maintenance_message', 'auto_signature', 'slack_logging', 'slack_webhook',
            'twitter_handle', 'switch_language', 'google_analytics_code'
        ]

        settings = process_setting_list(journal_settings, 'general', journal)
        settings[2]['choices'] = get_theme_list()
        setting_group = 'general'

    else:
        settings = []
        setting_group = None

    return settings, setting_group


def get_theme_list():
    path = os.path.join(settings.BASE_DIR, "themes")
    root, dirs, files = next(os.walk(path))

    return [[dir, dir] for dir in dirs if dir not in ['admin', 'press', '__pycache__']]


def handle_default_thumbnail(request, journal, attr_form):
    if request.FILES.get('default_thumbnail'):
        new_file = files.save_file_to_journal(request, request.FILES.get('default_thumbnail'), 'Default Thumb',
                                              'default')

        if journal.thumbnail_image:
            journal.thumbnail_image.unlink_file(journal=journal)

        journal.thumbnail_image = new_file
        journal.save()

        return new_file

    return None


def handle_press_override_image(request, journal, attr_form):
    if request.FILES.get('press_image_override'):
        new_file = files.save_file_to_journal(request, request.FILES.get('press_image_override'), 'Press Override',
                                              'default')
        if journal.press_image_override:
            journal.press_image_override.unlink_file(journal=journal)

        journal.press_image_override = new_file
        journal.save()

        return new_file

    return None


def article_file(uploaded_file, article, request):
    new_file = files.save_file_to_article(uploaded_file, article, request.user)
    new_file.label = 'Banner image'
    new_file.description = 'Banner image'
    new_file.privacy = 'public'
    new_file.save()
    return new_file


def handle_article_large_image_file(uploaded_file, article, request):
    if not article.large_image_file:
        new_file = article_file(uploaded_file, article, request)

        article.large_image_file = new_file
        article.save()
    else:
        new_file = files.overwrite_file(uploaded_file, article, article.large_image_file)
        article.large_image_file = new_file
        article.save()

    resize_and_crop(new_file.self_article_path(), [750, 324], 'middle')


def handle_article_thumb_image_file(uploaded_file, article, request):
    if not article.thumbnail_image_file:
        new_file = article_file(uploaded_file, article, request)

        article.thumbnail_image_file = new_file
        article.save()
    else:
        new_file = files.overwrite_file(uploaded_file, article, article.thumbnail_image_file)
        article.thumbnail_image_file = new_file
        article.save()


def handle_email_change(request, email_address):
    request.user.email = email_address
    request.user.is_active = False
    request.user.confirmation_code = uuid.uuid4()
    request.user.save()

    context = {'user': request.user}
    message = render_template.get_message_content(request, context, 'user_email_change')
    notify_helpers.send_email_with_body_from_user(request, 'subject_user_email_change', request.user.email, message)

    logout(request)


def handle_add_users_to_role(users, role, request):
    role = models.Role.objects.get(pk=role)
    users = models.Account.objects.filter(pk__in=users)

    if not users:
        messages.add_message(request, messages.WARNING, 'No users selected')

    if not role:
        messages.add_message(request, messages.WARNING, 'No role selected.')

    for user in users:
        user.add_account_role(role.slug, request.journal)
        messages.add_message(request, messages.INFO, '{0} added to {1}'.format(user.full_name(), role.name))


def clear_active_elements(elements, workflow, plugins):
    elements_to_remove = list()
    for element in elements:
        if workflow.elements.filter(handshake_url=element.get('handshake_url')):
            elements_to_remove.append(element)

    for element in elements_to_remove:
        elements.remove(element)

    return elements


def get_available_elements(workflow):
    plugins = plugin_installed_apps.load_plugin_apps()
    our_elements = list()
    elements = models.BASE_ELEMENTS

    for element in elements:
        our_elements.append(element)

    for plugin in plugins:
        module_name = "{0}.plugin_settings".format(plugin)
        plugin_settings = import_module(module_name)

        if hasattr(plugin_settings, 'IS_WORKFLOW_PLUGIN') and hasattr(plugin_settings, 'HANDSHAKE_URL'):
            if plugin_settings.IS_WORKFLOW_PLUGIN:
                our_elements.append(
                    {'name': plugin_settings.PLUGIN_NAME, 'handshake_url': plugin_settings.HANDSHAKE_URL,
                     'stage': plugin_settings.STAGE}
                )
    return clear_active_elements(our_elements, workflow, plugins)


def handle_element_post(workflow, element_name, request):
    for element in get_available_elements(workflow):
        if element['name'] == element_name:
            element_obj, created = models.WorkflowElement.objects.get_or_create(journal=request.journal,
                                                                                element_name=element_name,
                                                                                handshake_url=element['handshake_url'],
                                                                                stage=element['stage'])

            return element_obj


def latest_articles(carousel, object_type):
    if object_type == 'journal':
        carousel_objects = submission_models.Article.objects.filter(
            journal=carousel.journal,
            date_published__isnull=False
        ).order_by("-date_published")
    else:
        carousel_objects = submission_models.Article.objects.all().order_by("-date_published")

    return carousel_objects


def selected_articles(carousel):
    carousel_objects = carousel.articles.all().order_by("-date_published")

    return carousel_objects


def news_items(carousel, object_type, press=None):
    if object_type == 'journal':
        object_id = carousel.journal.pk
    else:
        object_id = carousel.press.pk

    if press and press.carousel_news_items.all():
        return press.carousel_news_items.all()

    carousel_objects = models.NewsItem.objects.filter(
        (Q(content_type__model=object_type) & Q(object_id=object_id)) &
        (Q(start_display__lte=timezone.now()) | Q(start_display=None)) &
        (Q(end_display__gte=timezone.now()) | Q(end_display=None))
    ).order_by('-posted')

    return carousel_objects


def sort_mixed(article_objects, news_objects):
    carousel_objects = []

    for news_item in news_objects:
        for article in article_objects:
            if article.date_published > news_item.posted:
                carousel_objects.append(article)
        carousel_objects.append(news_item)

    # add any articles that were not inserted during the above sort procedure
    for article in article_objects:
        if article not in carousel_objects:
            carousel_objects.append(article)

    return carousel_objects


def get_unpinned_articles(request, pinned_articles):
    articles_pinned = [pin.article.pk for pin in pinned_articles]
    return submission_models.Article.objects.filter(journal=request.journal).exclude(pk__in=articles_pinned)


def order_pinned_articles(request, pinned_articles):
    ids = [int(_id) for _id in request.POST.getlist('orders[]')]

    for pin in pinned_articles:
        pin.sequence = ids.index(pin.pk)
        pin.save()


def password_policy_check(request):
    """
    Takes a given string and tests it against the password policy of the press.
    :param request:  HTTPRequest object
    :return: An empty list or a list of errors.
    """
    password = request.POST.get('password_1')

    rules = [
        lambda s: len(password) >= request.press.password_length or 'length'
    ]

    if request.press.password_upper:
        rules.append(lambda password: any(x.isupper() for x in password) or 'upper')

    if request.press.password_number:
        rules.append(lambda password: any(x.isdigit() for x in password) or 'digit')

    problems = [p for p in [r(password) for r in rules] if p != True]

    print(problems)  # ['digit', 'length']
    return problems
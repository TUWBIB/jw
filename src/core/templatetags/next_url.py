from django import template
from django.urls import reverse
from core.logic import reverse_with_next
from urllib.parse import quote

register = template.Library()

@register.simple_tag(takes_context=True)
def url_with_next(context, url_name, *args, **kwargs):
    """
    A template tag to use instead of 'url' when you want
    the reversed URL to include the same 'next' parameter that
    already exists in the GET or POST data of the request,
    or you want to introduce a new next url by Django URL name.
    """
    request = context.get('request')
    next_url = request.GET.get('next', '')
    return reverse_with_next(url_name, next_url, args=args, kwargs=kwargs)


@register.simple_tag(takes_context=True)
def url_with_return(context, url_name, *args, **kwargs):
    """
    A template tag to use instead of 'url' when you want
    the reversed URL to include a new 'next' parameter that
    contains the full and query string path of the current request.
    """
    request = context.get('request')
    if request.journal or request.repository:
        next_url = request.get_full_path()
    else:
        # This is the only way to refer to press URLs
        next_url = request.build_absolute_uri()

    return reverse_with_next(url_name, next_url, args=args, kwargs=kwargs)

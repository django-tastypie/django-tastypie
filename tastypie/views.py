"""
WARNING!

Tastypie doesn't provide much here (just the API browser). The place you're
likely looking for is ``tastypie.api.Api`` or ``tastypie.resources.Resource``.
Both of those classes provide most of the view that comprise the API
functionality.
"""
from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import Http404
from django.shortcuts import render_to_response


def browser(request, api_name):
    try:
        api_top_level = reverse('api_%s_top_level' % api_name, kwargs={
            'api_name': api_name,
        })
    except NoReverseMatch:
        raise Http404("No such API exists.")

    return render_to_response('tastypie/api_browser.html', {
        'MEDIA_URL': settings.MEDIA_URL,
        'api_top_level': api_top_level,
    })

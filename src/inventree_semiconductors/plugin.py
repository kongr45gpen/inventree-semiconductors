# -*- coding: utf-8 -*-
"""sample implementation for ActionPlugin"""
from plugin import InvenTreePlugin
from django.template import loader
from plugin.mixins import NavigationMixin, PanelMixin, UrlsMixin, ActionMixin, AppMixin
from django.urls import re_path
from django.http import HttpResponse
from pathlib import Path
from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from . import api

class SemiconductorPlugin(NavigationMixin, PanelMixin, UrlsMixin, ActionMixin, AppMixin, InvenTreePlugin):

    NAME = "SemiconductorPlugin"
    SLUG = "semiconductor"
    DESCRIPTION = "A very basic plugin with one mixin"

    NAVIGATION = [
        {'name': 'SampleIntegration', 'link': 'plugin:semiconductor:increase-level', 'icon': 'fas fa-box'},
        {'name': 'Digikey API', 'link': 'plugin:semiconductor:api-digikey-fetch', 'icon': 'fas fa-box'},
    ]

    NAVIGATION_TAB_NAME = "Sample Nav"
    NAVIGATION_TAB_ICON = 'fas fa-microchip'

    def __init__(self):
        super().__init__()

    def setup_urls(self):
        return [
            re_path(r'^digikey/', self.view_test, name='increase-level'),
            re_path(r'^api/digikey/', api.DigikeyFetch.as_view(), name='api-digikey-fetch')
        ]

    def get_custom_panels(self, view, request):
        panels = [
            {
                # Simple panel without any actual content
                'title': 'No Content',
            }
        ]

        return panels
    
    def view_test(self, request):
        """Very basic view."""

        template = loader.get_template(Path(__file__).parent / 'templates' / 'digikey.html')

        return HttpResponse(template.render({}, request))
    
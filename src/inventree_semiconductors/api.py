from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import renderer_classes, api_view, permission_classes
from django.http import HttpResponse
from rest_framework import permissions
from .suppliers.digikey_api import *
from django.views.decorators.csrf import csrf_exempt

@api_view(('POST',))
@renderer_classes([JSONRenderer])
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def digikey_fetch(request):
    """Return a digikey"""

    info = fetch_part_info(request.data['part'])

    return Response(info)
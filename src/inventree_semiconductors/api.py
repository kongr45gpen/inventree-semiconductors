from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from django.http import HttpResponse
from rest_framework import permissions
from rest_framework.schemas import AutoSchema
import coreapi
import coreschema

from .suppliers.digikey_api import *
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

class CsrfExemptMixin(object):
    """Exempts the view from CSRF requirements."""

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        """Overwrites dispatch to be extempt from csrf checks."""
        return super().dispatch(*args, **kwargs)

class DigikeyFetch(APIView, CsrfExemptMixin):
    #renderer_classes = [JSONRenderer]
    permission_classes = [permissions.AllowAny]

    schema = AutoSchema(
            manual_fields=[
                coreapi.Field("part",required=True,
            location="form",
            schema=coreschema.String()),
            ]
        )

    def post(self, request):
        """Return a digikey"""

        

        info = fetch_part_info(request.data['part'])

        return Response(info)

# @api_view(('POST',))
# @renderer_classes([JSONRenderer])
# @permission_classes((permissions.AllowAny,))
# @csrf_exempt
# def digikey_fetch(request, part, *args, **kwargs):
#     """Return a digikey"""

#     info = fetch_part_info(part)

#     return Response(info)
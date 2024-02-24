from django.http import JsonResponse
from django.shortcuts import render

from djapy.v2.openapi import openapi


def get_openapi(request):
    return JsonResponse(openapi.dict())


def render_swagger_ui(request):
    return render(request, 'djapy/swagger_cdn.html')

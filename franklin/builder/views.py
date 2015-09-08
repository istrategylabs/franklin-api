import os

import requests

from django.shortcuts import render
from django.http import HttpResponse

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from github.serializers import GithubWebhookSerializer
from users.models import User

# Create your views here.


@api_view(['POST'])
def build_status(request):
    if request.method == 'POST':
        # Github webhooks contain special headers we can check for
        event_type = request.META.get("HTTP_X_GITHUB_EVENT")
        # Possibly useful for validation/security 
        # request.META.get("HTTP_X_GITHUB_DELIVERY")

        if event_type and event_type == "push":
            # For now, we only support push to branch events
            # TODO - We should also only support pushes to specific branches

            updated_site = GithubWebhookSerializer(data=request.data)
            if updated_site.is_valid():
                updated_site.save(build=True)
                return Response(status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from django.shortcuts import redirect
from urllib.parse import urlencode
import requests
import os

from littlebooks_API.models import Variables


TIKTOK_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"

CLIENT_KEY = os.environ.get('TIKTOK_CLIENT_KEY')
CLIENT_SECRET = os.environ.get('TIKTOK_CLIENT_SECRET')
REDIRECT_URI = os.environ.get('TIKTOK_REDIRECT_URI')


class TiktokViewSet(GenericViewSet):
    queryset = []
    serializer_class = None

    @action(detail=False, methods=['get'])
    def hello_world(self, request):
        return Response({"message": "hello world"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def login(self, request):
        params = urlencode({
            'client_key': CLIENT_KEY,
            'scope': 'user.info.basic,video.upload',
            'response_type': 'code',
            'redirect_uri': REDIRECT_URI,
        })
        return redirect(f"{TIKTOK_AUTH_URL}?{params}")

    @action(detail=False, methods=['get'])
    def callback(self, request):
        code = request.query_params.get('code')
        if not code:
            return Response({"error": "No code provided"}, status=status.HTTP_400_BAD_REQUEST)

        response = requests.post(TIKTOK_TOKEN_URL, data={
            'client_key': CLIENT_KEY,
            'client_secret': CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
        })

        if response.status_code != 200:
            return Response({"error": "Failed to get token", "detail": response.json()}, status=status.HTTP_400_BAD_REQUEST)

        data = response.json()
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')

        Variables.objects.update_or_create(name='tiktok_access_token', defaults={'value': access_token})
        Variables.objects.update_or_create(name='tiktok_refresh_token', defaults={'value': refresh_token})

        return Response({"message": "Tokens saved successfully"}, status=status.HTTP_200_OK)

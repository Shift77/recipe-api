'''
Views for the user API.
'''
from rest_framework import generics
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from .serializers import UserSerializer, TokenAuthSerializer


class CreateUserView(generics.CreateAPIView):
    '''View to create a new user.'''
    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    '''View to create auth token for a user.'''
    serializer_class = TokenAuthSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES  # Browsable Api

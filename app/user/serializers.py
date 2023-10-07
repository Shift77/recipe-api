'''
Serializers for user API view.
'''

from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext as _
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    '''Serializer for user object.'''
    class Meta:
        model = get_user_model()
        fields = ['email', 'password', 'name']
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 8}
        }

    def create(self, validated_data):
        '''create and return a user with encrypted password.'''
        return get_user_model().objects.create_user(**validated_data)


class TokenAuthSerializer(serializers.Serializer):
    '''Serializer for the user auth token.'''
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
    )

    def validate(self, attrs):
        '''Validate and authenticate the user.'''
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            email=email,        # This may cause an error as it's default value
                                # is username and we have changed it to email
                                # as we have our custom user model that uses
                                # 'email' instead of username.
            password=password,
        )
        if not user:
            msg = _('Unable to authenticate with provided credentials.')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs

import logging

from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework_social_oauth2 import views as social_oauth_views
from social.pipeline.partial import partial

logger = logging.getLogger(__name__)


class ConvertTokenView(social_oauth_views.ConvertTokenView, APIView):
    """ Login user """
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        """ 
        Exchange social token for franklin oAuth access token
        ---
        type:
            access_token:
                type: string
                required: true
                description: Required for all other API calls
            expires_in:
                type: string
                required: true
            token_type:
                type: string
                required: true
                description: Bearer
            scope:
                type: string
                required: true
            refresh_token:
                type: string
                required: true
        parameters_strategy:
            form: replace
        parameters:
            - name: Content-Type
              paramType: header
              required: true
              description: application/x-www-form-urlencoded
            - name: grant_type
              type: string
              required: true
              description: Must have the value `convert_token`
            - name: backend
              type: string
              required: true
              description: Must have the value `github`
            - name: client_id
              type: string
              required: true
              description: provided by Franklin admin
            - name: client_secret
              type: string
              required: true
              description: secret key complimenting client_id
            - name: token
              type: string
              required: true
              description: Github oAuth token obtained from user social signin 
        """
        return super(ConvertTokenView, self).post(request, *args, **kwargs)


@api_view(('GET',))
def health(request):
    return Response('Healthy!')

@partial
def save_oauth(strategy, details, user=False, *args, **kwargs):
    # TODO django-rest-framework-social-oauth2 has a bug in it (11/2015)
    # It doesn't save the access_token, so we do it here manually
    request = kwargs.get('request', None)
    if user and request:
        access_token = request.get('token', None)
        social = user.social_auth.get(provider='github')
        social.extra_data['access_token'] = access_token
        social.save()
        return { 'is_new': False, 'user': user }
    return { 'is_new': True, 'user': None }

        

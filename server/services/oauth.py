# server/services/oauth.py

from flask import current_app
from authlib.integrations.flask_client import OAuth

class OAuthService:
    def __init__(self, config):
        self.app = current_app._get_current_object()
        self.oauth = OAuth(self.app)

        # Register Google
        self.oauth.register(
            name='google',
            client_id=config['GOOGLE_CLIENT_ID'],
            client_secret=config['GOOGLE_CLIENT_SECRET'],
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'},
            nonce_storage=None
        )

        # Register Facebook
        self.oauth.register(
            name='facebook',
            client_id=config['FACEBOOK_CLIENT_ID'],
            client_secret=config['FACEBOOK_CLIENT_SECRET'],
            api_base_url='https://graph.facebook.com/v18.0',
            access_token_url='https://graph.facebook.com/v18.0/oauth/access_token',
            authorize_url='https://www.facebook.com/v18.0/dialog/oauth',
            client_kwargs={
                'scope': 'email public_profile',
                'display': 'popup',
                'auth_type': 'rerequest',
                'response_type': 'code'
            } 
        )

        # # Register Apple
        # # Apple is a bit more involved because of private keys, etc.
        # # For brevity, an example (but you will need to add your Apple details properly)
        # self.oauth.register(
        #     name='apple',
        #     client_id=config['APPLE_CLIENT_ID'],
        #     client_secret=config['APPLE_CLIENT_SECRET'],  # or dynamic generation
        #     server_metadata_url='https://appleid.apple.com/.well-known/openid-configuration',
        #     client_kwargs={'scope': 'name email'}
        # )

    def get_google_oauth(self):
        return self.oauth.google

    def get_facebook_oauth(self):
        return self.oauth.facebook

    # def get_apple_oauth(self):
    #     return self.oauth.apple
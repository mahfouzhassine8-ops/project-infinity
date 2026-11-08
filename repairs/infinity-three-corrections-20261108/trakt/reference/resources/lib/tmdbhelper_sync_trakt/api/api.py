from threading import local
from jurialmunkey.ftools import cached_property
from tmdbhelper.lib.api.request import NoCacheRequestAPI
from tmdbhelper_sync_trakt.api.keys import CLIENT_ID
from tmdbhelper_sync_trakt.api.credentials import TraktTokenHandler
from tmdbhelper_sync_trakt.api.authenticator import TraktAuthenticator
from tmdbhelper_sync_trakt.api.profile import TraktProfile


API_URL = 'https://api.trakt.tv'
OAUTH_DEVICE_CODE_URL = 'https://auth.trakt.tv/oauth/device/code'
OAUTH_DEVICE_TOKEN_URL = 'https://auth.trakt.tv/oauth/device/token'
OAUTH_REVOKE_URL = 'https://auth.trakt.tv/oauth/revoke'
OAUTH_TOKEN_URL = 'https://auth.trakt.tv/oauth/token'


class TraktAPI(NoCacheRequestAPI):

    client_id = CLIENT_ID
    user_token = None

    def __init__(
            self,
            client_id=None,
            user_token=None,
            login_if_required=False,
            force=False):
        super(TraktAPI, self).__init__(req_api_url=API_URL, req_api_name='TraktAPI', timeout=20)

        self.client_id = client_id or self.client_id
        self.user_token = user_token if user_token is not None else TraktTokenHandler()
        self.login_if_required = login_if_required
        self.request_state = local()
        if force:
            self.login()

    @property
    def headers_base(self):
        return {
            'trakt-api-version': '2',
            'trakt-api-key': self.client_id,
            'Content-Type': 'application/json'
        }

    @property
    def headers(self):
        return self.get_headers(self.access_token)

    def get_headers(self, access_token=None):
        headers = {}
        headers.update(self.headers_base)
        headers.update({'Authorization': f'Bearer {access_token}'} if access_token else {})
        return headers

    @headers.setter
    def headers(self, value):
        """ Ignore base class req_api attempting to set headers """
        return

    @property
    def access_token(self):
        return self.authenticator.access_token

    @cached_property
    def authenticator(self):
        return TraktAuthenticator(self)

    def refresh_authenticator(self):
        self.authenticator = TraktAuthenticator(self)

    def get_simple_api_request(self, request=None, postdata=None, headers=None, method=None):
        authorization = (headers or {}).get('Authorization', '')
        authenticated = (
            request is not None
            and request.startswith(f'{API_URL}/')
            and authorization.startswith('Bearer '))
        if not authenticated or getattr(self.request_state, 'active', False):
            return super().get_simple_api_request(request, postdata, headers, method)
        # The inherited connection retry re-enters this method. Only the outer call recovers auth.
        self.request_state.active = True
        try:
            return self.get_authenticated_response(request, postdata, headers, method)
        finally:
            self.request_state.active = False

    def get_authenticated_response(self, request, postdata, headers, method):
        response = super().get_simple_api_request(request, postdata, headers, method)
        if response is None or response.status_code != 401:
            return response
        response.close()
        token = self.authenticator.trakt_stored_access_token
        authorization = token.recover(rejected_token=headers['Authorization'][7:])
        if not authorization:
            return
        headers = dict(headers, Authorization=f"Bearer {authorization['access_token']}")
        response = super().get_simple_api_request(request, postdata, headers, method)
        if response is None or response.status_code != 401:
            return response
        response.close()
        token.reject_authorization(authorization['access_token'])

    def get_device_code(self):
        return self.get_api_request_json(
            OAUTH_DEVICE_CODE_URL, headers=self.headers_base, method='json',
            postdata={'client_id': self.client_id})

    def get_authorisation_token(self, device_code):
        return self.get_api_request_json(
            OAUTH_DEVICE_TOKEN_URL, headers=self.headers_base, method='json',
            postdata={'code': device_code, 'client_id': self.client_id})

    def del_authorisation_token(self, access_token):
        return self.get_api_request(
            OAUTH_REVOKE_URL, headers=self.headers_base, method='json',
            postdata={'token': access_token, 'client_id': self.client_id})

    def set_authorisation_token(self, refresh_token):
        # Preserve OAuth error bodies so recovery can distinguish rejection from an outage.
        return self.get_simple_api_request(
            OAUTH_TOKEN_URL, headers=self.headers_base, method='json',
            postdata={
                'refresh_token': refresh_token,
                'client_id': self.client_id,
                'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
                'grant_type': 'refresh_token'
            })

    @property
    def is_authorized(self):
        return self.authorize(forced=True)

    def authorize(self, forced=False):
        return self.authenticator.authorize(forced or self.login_if_required)

    def logout(self):
        self.refresh_authenticator()
        return self.authenticator.logout()

    def login(self):
        self.refresh_authenticator()
        return self.authenticator.login()

    @cached_property
    def profile(self):
        return TraktProfile(self)

    def delete_response(self, *args, **kwargs):
        return self.get_simple_api_request(
            self.get_request_url(*args, **kwargs),
            headers=self.headers,
            method='delete')

    def post_response(self, *args, postdata=None, response_method='post', **kwargs):
        from tmdbhelper.lib.files.futils import json_dumps as data_dumps
        return self.get_simple_api_request(
            self.get_request_url(*args, **kwargs),
            headers=self.headers,
            postdata=data_dumps(postdata) if postdata else None,
            method=response_method)

    def get_response(self, *args, **kwargs):
        return self.get_api_request(self.get_request_url(*args, **kwargs), headers=self.headers)

    def get_response_json(self, *args, **kwargs):
        try:
            return self.get_response(*args, **kwargs).json()
        except ValueError:
            return {}
        except AttributeError:
            return {}

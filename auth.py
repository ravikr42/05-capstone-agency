import os
import json
from flask import request, _request_ctx_stack, abort
from jose import jwt
from functools import wraps
from urllib.request import urlopen
from dotenv import load_dotenv
# basedir = os.path.abspath(os.path.dirname(__file__))

load_dotenv()


# AUTH0_DOMAIN = 'gs-prod.auth0.com'
# AUTH0_ALGORITHMS = ['RS256']
# AUTH0_AUDIENCE = 'casting'
AUTH0_DOMAIN = os.environ['AUTH0_DOMAIN']
AUTH0_ALGORITHMS = os.environ['AUTH0_ALGORITHMS']
AUTH0_AUDIENCE = os.environ['AUTH0_AUDIENCE']

print('❌ os.environ', os.getenv('AUTH0_AUDIENCE'))

# AuthError Exception handler
class AuthError(Exception):
    '''
    AuthError Exception
    A standardized way to communicate auth failure modes
    '''
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# Auth Header

'''
    get_token_auth_header() method
    it should attempt to get the header from the request
        it should raise an AuthError if no header is present
    it should attempt to split bearer and the token
        it should raise an AuthError if the header is malformed
    return the token part of the header
'''


def get_token_auth_header():
    """Grab Access Token from the Authorization Header in request"""
    auth = request.headers.get('Authorization', None)
    if auth:
        print('🚩auth exists in headers:')
    if not auth:  # ensures auth has a truthy value
        print('authorization_header_missing')
        raise AuthError({
            'code': 'authorization_header_missing',
            'description': 'Authorization header is expected.'
        }, 401)

    parts = auth.split()
    if parts[0].lower() != 'bearer':
        print('invalid_header')
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must start with "Bearer".'
        }, 401)

    elif len(parts) == 1:
        print('Token not found.')
        raise AuthError({
            # assumes token is not in header
            'code': 'invalid_header',
            'description': 'Token not found.'
        }, 401)

    elif len(parts) > 2:  # if header has more than two items
        print('Authorization header must be bearer token.')
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must be bearer token.'
        }, 401)

    token = parts[1]  # return only the token from parts
    if token:
        print('✅ found token in header:')
    return token


'''
    verify_decode_jwt(token) method
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload

    !!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
'''


def verify_decode_jwt(token):
    """Uses the Auth0 secret to decode then verify the provided token"""
    # print('verifying...')
    jsonurl = urlopen("https://{}/.well-known/jwks.json".format(AUTH0_DOMAIN))
    # print('jsonurl', jsonurl)
    jwks = json.loads(jsonurl.read())
    # print('jwks', jwks)
    unverified_header = jwt.get_unverified_header(token)
    # print('unverified_header', unverified_header)
    rsa_key = {}
    if 'kid' not in unverified_header:
        print("'kid' not in unverified_header")
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            # print('checking rsa key', rsa_key)
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=AUTH0_ALGORITHMS,
                audience=AUTH0_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )
            # print('✅ rsa key found', payload)
            return payload

        except jwt.ExpiredSignatureError:
            print('🚩 payload token_expired')
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            print('🚩 payload invalid_claims')
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)
        except Exception:
            print('🚩 payload invalid_header')
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
    print('🚩 payload unable to find key')
    raise AuthError({
        'code': 'invalid_header',
        'description': 'Unable to find the appropriate key.'
    }, 400)


'''
    check_permissions(permission, payload) method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    it should raise an AuthError if permissions are not included in the payload
        !!NOTE check your RBAC settings in Auth0
    it should raise an AuthError if the requested permission string is not in the payload permissions array
    return true otherwise
'''


def check_permissions(permission, payload):
    """Checks for permission in JWT"""
    if 'permissions' not in payload:
        # look for permissions in payload
        print("❌ 'permissions' not in payload for:", permission)
        raise AuthError({
            'code': 'invalid_claims',
            'description': 'Permission not included in JWT.'
        }, 400)
    if permission not in payload['permissions']:
        # look for permission in payload properties
        print(
            "❌ matching permission not found in payload['permissions'] for:", permission)
        raise AuthError({
            'code': 'unauthorized',
            'description': 'Permission not found.'
        }, 401)
    return True

'''
    @requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims and check the requested permission
    return the decorator which passes the decoded payload to the decorated method
'''


def requires_auth(permission=''):  # defaults permission to empty string
    """Defines a decorator specifically used for Authentication"""
    def requires_auth_decorator(f):  # wraps auth decorator
        @wraps(f)
        def wrapper(*args, **kwargs):
            # validate token
            # print('🚧 validating token in header')
            token = get_token_auth_header()
            # print('verifying header payload')
            payload = verify_decode_jwt(token)
            # print('payload', payload)
            # check permissions
            print('🧐 checking permission for', permission)
            check_permissions(permission, payload)
            print('permitted')
            return f(payload, *args, **kwargs)
        return wrapper
    return requires_auth_decorator

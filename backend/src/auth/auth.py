import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'starbucks-app.eu.auth0.com'
# LOGIN_LINK = 'https://starbucks-app.eu.auth0.com/authorize?audience=coffee&response_type=token&client_id=V8xmrrNFex1m39dEn0Iup5544Q0K3mMd&redirect_uri=https://127.0.0.1:8080/login-results'
# LOGIN_LINK = 'https://starbucks-app.eu.auth0.com.auth0.com/authorize?audience=coffee&response_type=token&client_id=V8xmrrNFex1m39dEn0Iup5544Q0K3mMd&redirect_uri=http://localhost:8100/tabs/user-page'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffee'


#---------------------------------------#
# Auth Exception function
#---------------------------------------#

'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


#---------------------------------------#
# Auth functions
#---------------------------------------#


def get_token_auth_header():

    authorization_header = request.headers.get('Authorization', None)

    if authorization_header is None:
        raise AuthError({
        'code': 401,
        'description': 'Missing authorization header.'
        }, 401)
    
    auth_header_components = authorization_header.split()

    if auth_header_components[0].lower() != 'bearer':
        raise AuthError({
            'code': 401,
            'description': 'Authorization header must start with "Bearer".'
        }, 401)

    # Raise error if "Authorization" contains more than other than 2 components
    elif len(auth_header_components) != 2:
        raise AuthError({
            'code': 402,
            'description': 'Invalid form of autherization token'
        }, 401)

    # When everyhting is fine, get the token which is the second component of the Authorization Header & return it
    return auth_header_components[1]


'''
    check_permissions(permission, payload) method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    it should raise an AuthError if permissions are not included in the payload
    it should raise an AuthError if the requested permission string is not in the payload permissions array
    return true otherwise
'''
def check_permissions(permission, payload):

    if 'permissions' not in payload:
        raise AuthError('Permissions not included in JWT', 400)

    if permission not in payload['permissions']:
        raise AuthError({
            'code': 401,
            'description': 'Unautherized to use the service.'
            }, 401)
    
    return True


'''
    verify_decode_jwt(token) method
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload
'''
def verify_decode_jwt(token):

    jsonJWKS = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonJWKS.read())
    unverified_header = jwt.get_unverified_header(token)

    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 401,
            'description': 'Missing argument.'
        }, 401)
    
    RSA_key = {} # empty dictionary

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            RSA_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }

    if RSA_key:
        try:
            # Construct the payload
            payload = jwt.decode(
                token,
                RSA_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer="https://"+AUTH0_DOMAIN+"/"
            )
            return payload
        
        # Token has expired and no long valid
        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 401,
                'description': 'Token has expired.'
            }, 401)
        
        # Wrong audience
        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 401,
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)

        # In all other Error cases, give generic error message
        except Exception as error:
            raise AuthError({
                'code': 400,
                'description': 'Unable to parse authentication token.'
            }, 400)

    # If no payload has been returned yet, raise error.
    raise AuthError({
                'code': 400,
                'description': 'No token was provided.'
            }, 400) 



'''
    requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims and check the requested permission
    return the decorator which passes the decoded payload to the decorated method
'''
def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
                
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator
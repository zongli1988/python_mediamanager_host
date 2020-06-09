
import json
from six.moves.urllib.request import urlopen
from functools import wraps
import azure.functions as func
from flask import Flask, request, jsonify, _request_ctx_stack
from flask_cors import cross_origin
from jose import jwt

import urllib.request

import os

AUTH0_DOMAIN = 'djb.eu.auth0.com'
API_AUDIENCE = "http://localhost:7071"
ALGORITHMS = ["RS256"]

APP = Flask(__name__)

# Error handler


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


@APP.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

# Format error response and append status code


def get_token_auth_header(request):
    """Obtains the Access Token from the Authorization Header
    """
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError({"code": "authorization_header_missing",
                         "description":
                         "Authorization header is expected"}, 401)

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError({"code": "invalid_header",
                         "description":
                         "Authorization header must start with"
                         " Bearer"}, 401)
    elif len(parts) == 1:
        raise AuthError({"code": "invalid_header",
                         "description": "Token not found"}, 401)
    elif len(parts) > 2:
        raise AuthError({"code": "invalid_header",
                         "description":
                         "Authorization header must be"
                         " Bearer token"}, 401)

    token = parts[1]
    return token


def requires_auth_decorator(f):
    def requires_auth_ref(req):
        token = get_token_auth_header(req)
        auth0Domain = os.environ["Auth0Domain"] + "/userinfo"
        headers = {
            'Authorization': "Bearer " + token
        }
        authReq = urllib.request.Request(auth0Domain, headers=headers)
        try:
            with urllib.request.urlopen(authReq) as response:
                userJsonString = response.read()
                userJson = json.loads(userJsonString)
                req.userInfo = userJson
                return f(req)
        except urllib.error.HTTPError:
            res = func.HttpResponse("Unauthorised",
                                    status_code=401
                                    )
            return res

    return requires_auth_ref


def requires_auth_jwt(request):
    token = get_token_auth_header(request)
    jsonurl = urlopen("https://"+AUTH0_DOMAIN+"/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer="https://"+AUTH0_DOMAIN+"/"
            )
        except jwt.ExpiredSignatureError:
            raise AuthError({"code": "token_expired",
                             "description": "token is expired"}, 401)
        except jwt.JWTClaimsError:
            raise AuthError({"code": "invalid_claims",
                             "description":
                             "incorrect claims,"
                             "please check the audience and issuer"}, 401)
        except Exception:
            raise AuthError({"code": "invalid_header",
                             "description":
                             "Unable to parse authentication"
                             " token."}, 401)

        # _request_ctx_stack.top.current_user = payload
        return
    raise AuthError({"code": "invalid_header",
                     "description": "Unable to find appropriate key"}, 401)

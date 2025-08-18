import os
import uuid
from functools import wraps
from urllib.parse import urlencode

import jwt
import requests
from flask import g, redirect, render_template, request, session, url_for
from flask_dance.consumer import (
    OAuth2ConsumerBlueprint,
    oauth_authorized,
    oauth_error,
)
from flask_dance.consumer.storage import BaseStorage
from flask_login import current_user, login_user, logout_user
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError
from sqlalchemy.exc import NoResultFound
from werkzeug.local import LocalProxy

from src.core.app import db

# OAuth model temporarily disabled for compatibility
# from src.core.models import OAuth, User
try:
    from src.core.models import OAuth, User
except ImportError:
    # Fallback for environments without OAuth model
    class OAuth:
        pass
    class User:
        pass


class UserSessionStorage(BaseStorage):
    def get(self, blueprint):  # type: ignore
        try:
            oauth_record = (
                db.session.query(OAuth)
                .filter_by(
                    user_id=current_user.get_id(),
                    browser_session_key=g.browser_session_key,
                    provider=blueprint.name,
                )
                .one()
            )
            return oauth_record.token
        except NoResultFound:
            return None

    def set(self, blueprint, token):
        db.session.query(OAuth).filter_by(
            user_id=current_user.get_id(),
            browser_session_key=g.browser_session_key,
            provider=blueprint.name,
        ).delete()
        new_model = OAuth()
        new_model.user_id = current_user.get_id()
        new_model.browser_session_key = g.browser_session_key
        new_model.provider = blueprint.name
        new_model.token = token
        db.session.add(new_model)
        db.session.commit()

    def delete(self, blueprint):
        db.session.query(OAuth).filter_by(
            user_id=current_user.get_id(),
            browser_session_key=g.browser_session_key,
            provider=blueprint.name,
        ).delete()
        db.session.commit()


def make_replit_blueprint():
    try:
        repl_id = os.environ["REPL_ID"]
    except KeyError:
        raise SystemExit("the REPL_ID environment variable must be set") from None

    issuer_url = os.environ.get("ISSUER_URL", "https://replit.com/oidc")

    replit_bp = OAuth2ConsumerBlueprint(
        "replit_auth",
        __name__,
        client_id=repl_id,
        client_secret=None,
        base_url=issuer_url,
        authorization_url_params={
            "prompt": "login consent",
        },
        token_url=issuer_url + "/token",
        token_url_params={
            "auth": (),
            "include_client_id": True,
        },
        auto_refresh_url=issuer_url + "/token",
        auto_refresh_kwargs={
            "client_id": repl_id,
        },
        authorization_url=issuer_url + "/auth",
        use_pkce=True,
        code_challenge_method="S256",
        scope=["openid", "profile", "email", "offline_access"],
        storage=UserSessionStorage(),
    )

    @replit_bp.before_app_request
    def set_applocal_session():
        if "_browser_session_key" not in session:
            session["_browser_session_key"] = uuid.uuid4().hex
        session.modified = True
        g.browser_session_key = session["_browser_session_key"]
        g.flask_dance_replit = replit_bp.session

    @replit_bp.route("/logout")
    def logout():
        del replit_bp.token
        logout_user()

        end_session_endpoint = issuer_url + "/session/end"
        encoded_params = urlencode(
            {
                "client_id": repl_id,
                "post_logout_redirect_uri": request.url_root,
            }
        )
        logout_url = f"{end_session_endpoint}?{encoded_params}"

        return redirect(logout_url)

    @replit_bp.route("/error")
    def error():
        return render_template("403.html"), 403

    return replit_bp


def get_jwt_public_keys(issuer_url):
    """Fetch public keys for JWT verification from OIDC issuer."""
    try:
        # Get well-known configuration
        well_known_url = f"{issuer_url}/.well-known/openid-configuration"
        config_response = requests.get(well_known_url, timeout=10)
        config_response.raise_for_status()
        config = config_response.json()

        # Get public keys
        jwks_url = config["jwks_uri"]
        keys_response = requests.get(jwks_url, timeout=10)
        keys_response.raise_for_status()
        return keys_response.json()
    except (requests.RequestException, KeyError, ValueError) as e:
        raise ValueError(f"Failed to fetch JWT public keys: {str(e)}") from e


def verify_jwt_token(token, issuer_url, client_id):
    """Verify JWT token signature and claims."""
    try:
        # Get public keys
        jwks_data = get_jwt_public_keys(issuer_url)

        # Get the header to find the key ID
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        if not kid:
            raise ValueError("JWT token missing 'kid' in header")

        # Find the matching key
        key_data = None
        for key in jwks_data.get("keys", []):
            if key.get("kid") == kid:
                key_data = key
                break

        if not key_data:
            raise ValueError(f"Public key not found for kid: {kid}")

        # Convert JWKS key to PyJWT format
        from jwt.algorithms import RSAAlgorithm

        public_key = RSAAlgorithm.from_jwk(key_data)  # type: ignore

        # Decode token with verification
        user_claims = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],  # Replit uses RS256
            audience=client_id,
            issuer=issuer_url,
            options={
                "verify_signature": True,
                "verify_aud": True,
                "verify_iss": True,
                "verify_exp": True,
            },
        )
        return user_claims
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid JWT token: {str(e)}") from e
    except Exception as e:
        raise ValueError(f"JWT verification error: {str(e)}") from e


def save_user(user_claims):
    user = User()
    user.id = user_claims["sub"]
    user.email = user_claims.get("email")
    user.first_name = user_claims.get("first_name")
    user.last_name = user_claims.get("last_name")
    user.profile_image_url = user_claims.get("profile_image_url")
    merged_user = db.session.merge(user)
    db.session.commit()
    return merged_user


@oauth_authorized.connect
def logged_in(blueprint, token):
    try:
        issuer_url = os.environ.get("ISSUER_URL", "https://replit.com/oidc")
        client_id = os.environ.get("REPL_ID")
        user_claims = verify_jwt_token(token["id_token"], issuer_url, client_id)
        user = save_user(user_claims)
        login_user(user)
        blueprint.token = token
        next_url = session.pop("next_url", None)
        if next_url is not None:
            return redirect(next_url)
        # Default redirect to home page
        return redirect(url_for("main.index"))
    except ValueError as e:
        # Log the error and redirect to error page
        print(f"JWT verification failed: {e}")
        return redirect(url_for("replit_auth.error"))


@oauth_error.connect
def handle_error(blueprint, error, error_description=None, error_uri=None):
    return redirect(url_for("replit_auth.error"))


def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            session["next_url"] = get_next_navigation_url(request)
            return redirect(url_for("replit_auth.login"))

        expires_in = replit.token.get("expires_in", 0)
        if expires_in < 0:
            issuer_url = os.environ.get("ISSUER_URL", "https://replit.com/oidc")
            refresh_token_url = issuer_url + "/token"
            try:
                token = replit.refresh_token(
                    token_url=refresh_token_url, client_id=os.environ["REPL_ID"]
                )
            except InvalidGrantError:
                # If the refresh token is invalid, the users needs to re-login.
                session["next_url"] = get_next_navigation_url(request)
                return redirect(url_for("replit_auth.login"))
            replit.token_updater(token)

        return f(*args, **kwargs)

    return decorated_function


def get_next_navigation_url(request):
    is_navigation_url = (
        request.headers.get("Sec-Fetch-Mode") == "navigate"
        and request.headers.get("Sec-Fetch-Dest") == "document"
    )
    if is_navigation_url:
        return request.url
    return request.referrer or request.url


replit = LocalProxy(lambda: g.flask_dance_replit)

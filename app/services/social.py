"""
Social media API connectors — Instagram Basic Display API + TikTok Research API.

Usage:
    from app.services.social import verify_instagram, verify_tiktok

Both return a dict with {followers, bio, verified=True/False, error=None|str}.
Credentials are read from app config / env vars.
"""
import requests
from flask import current_app


def verify_instagram(username: str) -> dict:
    """
    Lookup Instagram profile via Meta Graph API (scraping-free path).

    Requires INSTAGRAM_ACCESS_TOKEN in config — a long-lived user access token
    with pages_read_engagement + instagram_basic scopes.
    Graph API v19+: GET /me?fields=username,followers_count,biography
    """
    token = current_app.config.get('INSTAGRAM_ACCESS_TOKEN', '')
    if not token:
        return _stub('instagram', username,
                     'INSTAGRAM_ACCESS_TOKEN not configured — set in .env')

    url = 'https://graph.instagram.com/me'
    params = {'fields': 'username,biography,followers_count', 'access_token': token}
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if 'error' in data:
            return _stub('instagram', username, data['error'].get('message', 'API error'))
        return {
            'platform':  'instagram',
            'username':  data.get('username', username),
            'followers': data.get('followers_count', 0),
            'bio':       data.get('biography', ''),
            'verified':  True,
            'error':     None,
        }
    except (requests.RequestException, ValueError) as e:
        # ValueError covers a non-JSON response body (r.json() decode failure).
        return _stub('instagram', username, str(e))


def verify_tiktok(username: str) -> dict:
    """
    Lookup TikTok profile via TikTok Research API.

    Requires TIKTOK_CLIENT_KEY + TIKTOK_CLIENT_SECRET in config.
    Authenticates via client-credentials OAuth2 and calls /research/user/info/.
    """
    client_key    = current_app.config.get('TIKTOK_CLIENT_KEY', '')
    client_secret = current_app.config.get('TIKTOK_CLIENT_SECRET', '')
    if not client_key or not client_secret:
        return _stub('tiktok', username,
                     'TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET not configured — set in .env')

    token = _tiktok_token(client_key, client_secret)
    if not token:
        return _stub('tiktok', username, 'Failed to obtain TikTok access token')

    url     = 'https://open.tiktokapis.com/v2/research/user/info/'
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    payload = {'username': username, 'fields': ['follower_count', 'bio_description']}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        data = r.json()
        if data.get('error', {}).get('code') not in (0, 'ok', None, ''):
            return _stub('tiktok', username,
                         data['error'].get('message', 'TikTok API error'))
        user = data.get('data', {}).get('user_info', {})
        return {
            'platform':  'tiktok',
            'username':  username,
            'followers': user.get('follower_count', 0),
            'bio':       user.get('bio_description', ''),
            'verified':  True,
            'error':     None,
        }
    except (requests.RequestException, ValueError) as e:
        # ValueError covers a non-JSON response body (r.json() decode failure).
        return _stub('tiktok', username, str(e))


def _tiktok_token(client_key: str, client_secret: str) -> str | None:
    url     = 'https://open.tiktokapis.com/v2/oauth/token/'
    payload = {
        'client_key':    client_key,
        'client_secret': client_secret,
        'grant_type':    'client_credentials',
    }
    try:
        r = requests.post(url, data=payload,
                          headers={'Content-Type': 'application/x-www-form-urlencoded'},
                          timeout=10)
        return r.json().get('access_token')
    except Exception:
        return None


def _stub(platform: str, username: str, error: str) -> dict:
    return {
        'platform':  platform,
        'username':  username,
        'followers': 0,
        'bio':       '',
        'verified':  False,
        'error':     error,
    }

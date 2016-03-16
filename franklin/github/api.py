import os
import yaml

from django.core.urlresolvers import reverse

from rest_framework import status

from core.helpers import make_rest_delete_call, make_rest_get_call, \
        make_rest_post_call

repo_base_url = 'https://api.github.com/repo'
repos_base_url = 'https://api.github.com/repos'


def get_auth_header(user):
    social = user.social_auth.get(provider='github')
    token = social.extra_data['access_token']
    # TODO - Confirm that a header token is the best/most secure way to go
    headers = {
                'content-type': 'application/json',
                'Authorization': 'token ' + token
              }
    return headers


def build_repo_url(owner, repo, endpoint=''):
    return '{0}/{1}/{2}/{3}'.format(repo_base_url, owner, repo, endpoint)


def build_repos_url(owner, repo, endpoint=''):
    return '{0}/{1}/{2}/{3}'.format(repos_base_url, owner, repo, endpoint)


def build_repos_root_url(owner, repo):
    return '{0}/{1}/{2}'.format(repos_base_url, owner, repo)


def get_franklin_config(site, user):
    url = build_repos_url(site.owner.name, site.name, 'contents/.franklin.yml')
    # TODO - This will fetch the file from the default master branch
    headers = get_auth_header(user)
    config_metadata = make_rest_get_call(url, headers)

    if status.is_success(config_metadata.status_code):
        download_url = config_metadata.json().get('download_url', None)
        config_payload = make_rest_get_call(download_url, None)
        if status.is_success(config_payload.status_code):
            # TODO - validation and cleanup needed here similar to:
            # http://stackoverflow.com/a/22231372
            franklin_config = yaml.load(config_payload.text)
            return franklin_config
        else:
            return config_payload
    return config_metadata


def create_repo_deploy_key(site, user):
    # TODO - check for existing and update if needed (or skip)
    url = build_repos_url(site.owner.name, site.name, 'keys')
    headers = get_auth_header(user)
    body = {
                'title': 'franklin',
                'key': site.deploy_key,
                'read_only': True
            }
    return make_rest_post_call(url, headers, body)


def delete_deploy_key(site, user):
    if site.deploy_key_id:
        endpoint = 'keys/' + site.deploy_key_id
        url = build_repos_url(site.owner.name, site.name, endpoint)
        headers = get_auth_header(user)
        return make_rest_delete_call(url, headers)
    return None


def create_repo_webhook(site, user):
    # TODO - check for existing webhook and update if needed (or skip)
    url = build_repos_url(site.owner.name, site.name, 'hooks')
    headers = get_auth_header(user)
    body = {
                'name': 'web',
                'events': ['push'],
                'active': True,
                'config': {
                    'url': os.environ['API_BASE_URL'] + reverse('webhook'),
                    'content_type': 'json',
                    'secret': os.environ['GITHUB_SECRET']
                }
            }
    return make_rest_post_call(url, headers, body)


def delete_webhook(site, user):
    if site.webhook_id:
        endpoint = 'hooks/' + site.webhook_id
        url = build_repos_url(site.owner.name, site.name, endpoint)
        headers = get_auth_header(user)
        return make_rest_delete_call(url, headers)
    return None


def get_access_token(request):
    """
    Converts a temporary auth token for an OAuth access token from Github
    """
    url = 'https://github.com/login/oauth/access_token'
    headers = {
        'content-type': 'application/json',
        'accept': 'application/json'
    }
    params = {
        "code": request.data.get('code'),
        "client_id": request.data.get('clientId'),
        "redirect_uri": request.data.get('redirectUri'),
        "client_secret": os.environ['SOCIAL_AUTH_GITHUB_SECRET']
    }
    return make_rest_post_call(url, headers, params)


def get_user_orgs(user):
    url = 'https://api.github.com/user/orgs'
    headers = get_auth_header(user)
    result = make_rest_get_call(url, headers)
    if status.is_success(result.status_code):
        return result.json()
    return None


def get_all_repos(user):
    url = 'https://api.github.com/user/repos?per_page=100'
    headers = get_auth_header(user)
    have_next_page = True
    repos = []

    while have_next_page:
        result = None
        have_next_page = False  # when in doubt, leave the loop after 1
        result = make_rest_get_call(url, headers)
        if status.is_success(result.status_code):
            # Add all of the repos to our list
            for repo in result.json():
                repos.append(repo)

            # If the header has a paging link called 'next', update our url
            # and continue with the while loop
            if result.links and result.links.get('next', None):
                url = result.links['next']['url']
                have_next_page = True
    return repos


def get_repo(owner, repo, user):
    url = build_repos_root_url(owner, repo)
    headers = get_auth_header(user)
    return make_rest_get_call(url, headers)


def get_default_branch(site, user):
    result = get_repo(site.owner.name, site.name, user)

    if status.is_success(result.status_code):
        return result.json().get('default_branch', None)
    return ''


def get_repo_permissions(owner, repo, user):
    result = get_repo(owner, repo, user)

    if status.is_success(result.status_code):
        return result.json().get('permissions', None)
    return ''


def get_branch_details(site, user, branch):
    url = build_repos_url(site.owner.name, site.name, 'branches/' + branch)
    headers = get_auth_header(user)
    result = make_rest_get_call(url, headers)
    if (status.is_success(result.status_code) and
            result.json().get('commit', None)):
        return result.json()['commit'].get('sha', None)
    return ''

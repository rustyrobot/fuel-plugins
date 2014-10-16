#!/usr/bin/env python

import requests
import yaml
import json

keystone = '10.20.0.2:5000'
# keystone = '0.0.0.0:8001'

master = '10.20.0.2:8000'
# master = '0.0.0.0:8001'

class KeystoneClient(object):
    """Simple keystone authentification client

    :param str username: is user name
    :param str password: is user password
    :param str auth_url: authentification url
    :param str tenant_name: tenant name
    """

    def __init__(self, username=None, password=None,
                 auth_url=None, tenant_name=None):
        self.auth_url = auth_url
        self.tenant_name = tenant_name
        self.username = username
        self.password = password

    @property
    def request(self):
        """Creates authentification session if required

        :returns: :class:`requests.Session` object
        """
        session = requests.Session()
        token = self.get_token()
        if token:
            session.headers.update({'X-Auth-Token': token})

        return session

    def get_token(self):
        try:
            resp = requests.post(
                self.auth_url,
                headers={'content-type': 'application/json'},
                data=json.dumps({
                    'auth': {
                        'tenantName': self.tenant_name,
                        'passwordCredentials': {
                            'username': self.username,
                            'password': self.password}}})).json()

            return (isinstance(resp, dict) and
                    resp.get('access', {}).get('token', {}).get('id'))
        except (ValueError, requests.exceptions.RequestException) as exc:
            print('Cannot authenticate in keystone: {0}'.format(exc))

        return None


keystone_client = KeystoneClient(
    username='admin',
    password='admin',
    auth_url='http://{0}/v2.0/tokens'.format(keystone),
    tenant_name='admin')


def add_env_attrs(release, plugin_name, attrs):
    """NOTE(eli): Add `attributes_metadata` to in seralizer
    """
    #release['attributes_metadata']['editable']['Plugins'] = {}
    #del release['attributes_metadata']['editable']['Plugins']
    #del release['attributes_metadata']['editable']['plugin_name']

    # TODO(eli): this stuff should be autogenerated by nailgun
    metadata = {
        'metadata': {
            'weight': 70,
            'label': plugin_name,
            'toggleable': True,
            'enabled': False}}

    release['attributes_metadata']['editable'][plugin_name] = \
            dict(metadata.items() + attrs.items())

def add_repos(release, repo_name, repo_path):
    release.setdefault('orchestrator_data', {})
    release['orchestrator_data'].setdefault('repo_metadata', {})
    release['orchestrator_data']['repo_metadata'][repo_name] = repo_path


def get_release(rel_id):
    print 'http://{0}/api/v1/releases/{1}'.format(master, rel_id)
    print requests.get(
        'http://{0}/api/v1/releases/{1}'.format(master, rel_id)).status_code

    print '*' * 40
    return keystone_client.request.get(
        'http://{0}/api/v1/releases/{1}'.format(master, rel_id)).json()


def update_release(rel_id, data):
    response = keystone_client.request.put(
        'http://{0}/api/v1/releases/{1}'.format(master, rel_id),
        json.dumps(data))

    print data
    print response.text
    print response.status_code
    return response


def register_plugin(plugin_name):
    centos_id = 1

    release = get_release(centos_id)
    print json.dumps(release)
    add_env_attrs(
        release,
        plugin_name,
        yaml.load(open('environment_config.yaml'))['attributes'])
    add_repos(
        release,
        plugin_name,
        'http://{0}/2014.1.1-5.1/centos/x86_64'.format(master))
    update_release(centos_id, release)


if __name__ == '__main__':
    import sys
    plugin_name = sys.argv[1]
    register_plugin(plugin_name)

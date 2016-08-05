# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import functools
import json

from keystoneclient.auth import token_endpoint
from keystoneclient import session
import mock
import requests
from requests_mock.contrib import fixture
import six
from six.moves.urllib import parse
from testscenarios import load_tests_apply_scenarios as load_tests  # noqa
import testtools
from testtools import matchers
import types

import bileanclient
from bileanclient.common import http
from bileanclient.tests.unit import utils


def original_only(f):
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self.client, 'log_curl_request'):
            self.skipTest('Skip logging tests for session client')

        return f(self, *args, **kwargs)


class TestClient(testtools.TestCase):

    scenarios = [
        ('httpclient', {'create_client': '_create_http_client'}),
        ('session', {'create_client': '_create_session_client'})
    ]

    def _create_http_client(self):
        return http.HTTPClient(self.endpoint, token=self.token)

    def _create_session_client(self):
        auth = token_endpoint.Token(self.endpoint, self.token)
        sess = session.Session(auth=auth)
        return http.SessionClient(sess)

    def setUp(self):
        super(TestClient, self).setUp()
        self.mock = self.useFixture(fixture.Fixture())

        self.endpoint = 'http://example.com:8770'
        self.ssl_endpoint = 'https://example.com:8770'
        self.token = u'abc123'

        self.client = getattr(self, self.create_client)()

    def test_identity_headers_and_token(self):
        identity_headers = {
            'X-Auth-Token': 'auth_token',
            'X-User-Id': 'user',
            'X-Tenant-Id': 'tenant',
            'X-Roles': 'roles',
            'X-Identity-Status': 'Confirmed',
            'X-Service-Catalog': 'service_catalog',
        }
        # with token
        kwargs = {'token': u'fake-token',
                  'identity_headers': identity_headers}
        http_client_object = http.HTTPClient(self.endpoint, **kwargs)
        self.assertEqual('auth_token', http_client_object.auth_token)
        self.assertTrue(http_client_object.identity_headers.
                        get('X-Auth-Token') is None)

    def test_identity_headers_and_no_token_in_header(self):
        identity_headers = {
            'X-User-Id': 'user',
            'X-Tenant-Id': 'tenant',
            'X-Roles': 'roles',
            'X-Identity-Status': 'Confirmed',
            'X-Service-Catalog': 'service_catalog',
        }
        # without X-Auth-Token in identity headers
        kwargs = {'token': u'fake-token',
                  'identity_headers': identity_headers}
        http_client_object = http.HTTPClient(self.endpoint, **kwargs)
        self.assertEqual(u'fake-token', http_client_object.auth_token)
        self.assertTrue(http_client_object.identity_headers.
                        get('X-Auth-Token') is None)

    def test_identity_headers_and_no_token_in_session_header(self):
        # Tests that if token or X-Auth-Token are not provided in the kwargs
        # when creating the http client, the session headers don't contain
        # the X-Auth-Token key.
        identity_headers = {
            'X-User-Id': 'user',
            'X-Tenant-Id': 'tenant',
            'X-Roles': 'roles',
            'X-Identity-Status': 'Confirmed',
            'X-Service-Catalog': 'service_catalog',
        }
        kwargs = {'identity_headers': identity_headers}
        http_client_object = http.HTTPClient(self.endpoint, **kwargs)
        self.assertIsNone(http_client_object.auth_token)
        self.assertNotIn('X-Auth-Token', http_client_object.session.headers)

    def test_identity_headers_are_passed(self):
        # Tests that if token or X-Auth-Token are not provided in the kwargs
        # when creating the http client, the session headers don't contain
        # the X-Auth-Token key.
        identity_headers = {
            'X-User-Id': b'user',
            'X-Tenant-Id': b'tenant',
            'X-Roles': b'roles',
            'X-Identity-Status': b'Confirmed',
            'X-Service-Catalog': b'service_catalog',
        }
        kwargs = {'identity_headers': identity_headers}
        http_client = http.HTTPClient(self.endpoint, **kwargs)

        path = '/users/user_id'
        self.mock.get(self.endpoint + path)
        http_client.get(path)

        headers = self.mock.last_request.headers
        for k, v in six.iteritems(identity_headers):
            self.assertEqual(v, headers[k])

    def test_language_header_passed(self):
        kwargs = {'language_header': 'nb_NO'}
        http_client = http.HTTPClient(self.endpoint, **kwargs)

        path = '/users/user_id'
        self.mock.get(self.endpoint + path)
        http_client.get(path)

        headers = self.mock.last_request.headers
        self.assertEqual(kwargs['language_header'], headers['Accept-Language'])

    def test_language_header_not_passed_no_language(self):
        kwargs = {}
        http_client = http.HTTPClient(self.endpoint, **kwargs)

        path = '/1/users/user_id'
        self.mock.get(self.endpoint + path)
        http_client.get(path)

        headers = self.mock.last_request.headers
        self.assertTrue('Accept-Language' not in headers)

    def test_connection_timeout(self):
        """Should receive an InvalidEndpoint if connection timeout."""
        def cb(request, context):
            raise requests.exceptions.Timeout

        path = '/users'
        self.mock.get(self.endpoint + path, text=cb)
        comm_err = self.assertRaises(bileanclient.exc.InvalidEndpoint,
                                     self.client.get,
                                     '/users')
        self.assertIn(self.endpoint, comm_err.message)

    def test_connection_refused(self):
        """Should receive a CommunicationError if connection refused.

        And the error should list the host and port that refused the
        connection
        """
        def cb(request, context):
            raise requests.exceptions.ConnectionError()

        path = '/events?limit=20'
        self.mock.get(self.endpoint + path, text=cb)

        comm_err = self.assertRaises(bileanclient.exc.CommunicationError,
                                     self.client.get,
                                     '/events?limit=20')

        self.assertIn(self.endpoint, comm_err.message)

    def test_http_encoding(self):
        path = '/users'
        text = 'Ok'
        self.mock.get(self.endpoint + path, text=text,
                      headers={"Content-Type": "text/plain"})

        headers = {"test": u'ni\xf1o'}
        resp, body = self.client.get(path, headers=headers)
        self.assertEqual(text, resp.text)

    def test_headers_encoding(self):
        if not hasattr(self.client, 'encode_headers'):
            self.skipTest('Cannot do header encoding check on SessionClient')

        value = u'ni\xf1o'
        headers = {"test": value, "none-val": None}
        encoded = self.client.encode_headers(headers)
        self.assertEqual(b"ni\xc3\xb1o", encoded[b"test"])
        self.assertNotIn("none-val", encoded)

    def test_raw_request(self):
        """Verify the path being used for HTTP requests reflects accurately."""
        headers = {"Content-Type": "text/plain"}
        text = 'Ok'
        path = '/users'

        self.mock.get(self.endpoint + path, text=text, headers=headers)

        resp, body = self.client.get('/users', headers=headers)
        self.assertEqual(headers, resp.headers)
        self.assertEqual(text, resp.text)

    def test_parse_endpoint(self):
        endpoint = 'http://example.com:8770'
        test_client = http.HTTPClient(endpoint, token=u'adc123')
        actual = test_client.parse_endpoint(endpoint)
        expected = parse.SplitResult(scheme='http',
                                     netloc='example.com:8770', path='',
                                     query='', fragment='')
        self.assertEqual(expected, actual)

    def test_get_connections_kwargs_http(self):
        endpoint = 'http://example.com:8770'
        test_client = http.HTTPClient(endpoint, token=u'adc123')
        self.assertEqual(test_client.timeout, 600.0)

    def test_http_chunked_request(self):
        text = "Ok"
        data = six.StringIO(text)
        path = '/users'
        self.mock.post(self.endpoint + path, text=text)

        headers = {"test": u'chunked_request'}
        resp, body = self.client.post(path, headers=headers, data=data)
        self.assertIsInstance(self.mock.last_request.body, types.GeneratorType)
        self.assertEqual(text, resp.text)

    def test_http_json(self):
        data = {"test": "json_request"}
        path = '/users'
        text = 'OK'
        self.mock.post(self.endpoint + path, text=text)

        headers = {"test": u'chunked_request'}
        resp, body = self.client.post(path, headers=headers, data=data)

        self.assertEqual(text, resp.text)
        self.assertIsInstance(self.mock.last_request.body, six.string_types)
        self.assertEqual(data, json.loads(self.mock.last_request.body))

    def test_http_chunked_response(self):
        data = "TEST"
        path = '/users/'
        self.mock.get(self.endpoint + path, body=six.StringIO(data),
                      headers={"Content-Type": "application/octet-stream"})

        resp, body = self.client.get(path)
        self.assertIsInstance(body, types.GeneratorType)
        self.assertEqual([data], list(body))

    @original_only
    def test_log_http_response_with_non_ascii_char(self):
        try:
            response = 'Ok'
            headers = {"Content-Type": "text/plain",
                       "test": "value1\xa5\xa6"}
            fake = utils.FakeResponse(headers, six.StringIO(response))
            self.client.log_http_response(fake)
        except UnicodeDecodeError as e:
            self.fail("Unexpected UnicodeDecodeError exception '%s'" % e)

    @original_only
    def test_log_curl_request_with_non_ascii_char(self):
        try:
            headers = {'header1': 'value1\xa5\xa6'}
            body = 'examplebody\xa5\xa6'
            self.client.log_curl_request('GET', '/api/\xa5', headers, body,
                                         None)
        except UnicodeDecodeError as e:
            self.fail("Unexpected UnicodeDecodeError exception '%s'" % e)

    @original_only
    @mock.patch('bileanclient.common.http.LOG.debug')
    def test_log_curl_request_with_body_and_header(self, mock_log):
        hd_name = 'header1'
        hd_val = 'value1'
        headers = {hd_name: hd_val}
        body = 'examplebody'
        self.client.log_curl_request('GET', '/api/', headers, body, None)
        self.assertTrue(mock_log.called, 'LOG.debug never called')
        self.assertTrue(mock_log.call_args[0],
                        'LOG.debug called with no arguments')
        hd_regex = ".*\s-H\s+'\s*%s\s*:\s*%s\s*'.*" % (hd_name, hd_val)
        self.assertThat(mock_log.call_args[0][0],
                        matchers.MatchesRegex(hd_regex),
                        'header not found in curl command')
        body_regex = ".*\s-d\s+'%s'\s.*" % body
        self.assertThat(mock_log.call_args[0][0],
                        matchers.MatchesRegex(body_regex),
                        'body not found in curl command')

    def _test_log_curl_request_with_certs(self, mock_log, key, cert, cacert):
        headers = {'header1': 'value1'}
        http_client_object = http.HTTPClient(self.ssl_endpoint, key_file=key,
                                             cert_file=cert, cacert=cacert,
                                             token='fake-token')
        http_client_object.log_curl_request('GET', '/api/', headers, None,
                                            None)
        self.assertTrue(mock_log.called, 'LOG.debug never called')
        self.assertTrue(mock_log.call_args[0],
                        'LOG.debug called with no arguments')

        needles = {'key': key, 'cert': cert, 'cacert': cacert}
        for option, value in six.iteritems(needles):
            if value:
                regex = ".*\s--%s\s+('%s'|%s).*" % (option, value, value)
                self.assertThat(mock_log.call_args[0][0],
                                matchers.MatchesRegex(regex),
                                'no --%s option in curl command' % option)
            else:
                regex = ".*\s--%s\s+.*" % option
                self.assertThat(mock_log.call_args[0][0],
                                matchers.Not(matchers.MatchesRegex(regex)),
                                'unexpected --%s option in curl command' %
                                option)

    @mock.patch('bileanclient.common.http.LOG.debug')
    def test_log_curl_request_with_all_certs(self, mock_log):
        self._test_log_curl_request_with_certs(mock_log, 'key1', 'cert1',
                                               'cacert2')

    @mock.patch('bileanclient.common.http.LOG.debug')
    def test_log_curl_request_with_some_certs(self, mock_log):
        self._test_log_curl_request_with_certs(mock_log, 'key1', 'cert1', None)

    @mock.patch('bileanclient.common.http.LOG.debug')
    def test_log_curl_request_with_insecure_param(self, mock_log):
        headers = {'header1': 'value1'}
        http_client_object = http.HTTPClient(self.ssl_endpoint, insecure=True,
                                             token='fake-token')
        http_client_object.log_curl_request('GET', '/api/', headers, None,
                                            None)
        self.assertTrue(mock_log.called, 'LOG.debug never called')
        self.assertTrue(mock_log.call_args[0],
                        'LOG.debug called with no arguments')
        self.assertThat(mock_log.call_args[0][0],
                        matchers.MatchesRegex('.*\s-k\s.*'),
                        'no -k option in curl command')

    @mock.patch('bileanclient.common.http.LOG.debug')
    def test_log_curl_request_with_token_header(self, mock_log):
        fake_token = 'fake-token'
        headers = {'X-Auth-Token': fake_token}
        http_client_object = http.HTTPClient(self.endpoint,
                                             identity_headers=headers)
        http_client_object.log_curl_request('GET', '/api/', headers, None,
                                            None)
        self.assertTrue(mock_log.called, 'LOG.debug never called')
        self.assertTrue(mock_log.call_args[0],
                        'LOG.debug called with no arguments')
        token_regex = '.*%s.*' % fake_token
        self.assertThat(mock_log.call_args[0][0],
                        matchers.Not(matchers.MatchesRegex(token_regex)),
                        'token found in LOG.debug parameter')

    def test_expired_token_has_changed(self):
        # instantiate client with some token
        fake_token = b'fake-token'
        http_client = http.HTTPClient(self.endpoint,
                                      token=fake_token)
        path = '/users/user_id'
        self.mock.get(self.endpoint + path)
        http_client.get(path)
        headers = self.mock.last_request.headers
        self.assertEqual(fake_token, headers['X-Auth-Token'])
        # refresh the token
        refreshed_token = b'refreshed-token'
        http_client.auth_token = refreshed_token
        http_client.get(path)
        headers = self.mock.last_request.headers
        self.assertEqual(refreshed_token, headers['X-Auth-Token'])
        # regression check for bug 1448080
        unicode_token = u'ni\xf1o'
        http_client.auth_token = unicode_token
        http_client.get(path)
        headers = self.mock.last_request.headers
        self.assertEqual(b'ni\xc3\xb1o', headers['X-Auth-Token'])

# Copyright 2013 IBM Corp.
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

from bileanclient.common import utils
from bileanclient.v1.resources import ResourceManager

import mock
import testtools

FAKE_ID = 'FAKE_ID'
fake_resource = {'id': FAKE_ID}

class ResourceManagerTest(testtools.TestCase):

    def setUp(self):
        super(ResourceManagerTest, self).setUp()
        self.mgr = ResourceManager(None)

    @mock.patch.object(ResourceManager, '_list')
    def test_list_resource(self, mock_list):
        mock_list.return_value = [fake_resource]
        result = self.mgr.list()
        self.assertEqual(fake_resource, result.next())
        # Make sure url is correct.
        mock_list.assert_called_once_with('/resources?', 'resources')

    @mock.patch.object(ResourceManager, '_list')
    def test_list_resource_with_kwargs(self, mock_list):
        mock_list.return_value = [fake_resource]
        kwargs = {'limit': 2,
                  'marker': FAKE_ID,
                  'filters': {
                      'resource_type': 'os.nova.server',
                      'user_id': FAKE_ID}}
        result = self.mgr.list(**kwargs)
        self.assertEqual(fake_resource, result.next())
        # Make sure url is correct.
        self.assertEqual(1, mock_list.call_count)
        args = mock_list.call_args
        self.assertEqual(2, len(args[0]))
        url, param = args[0]
        self.assertEqual('resources', param)
        base_url, query_params = utils.parse_query_url(url)
        self.assertEqual('/resources', base_url)
        expected_query_dict = {'limit': ['2'],
                               'marker': [FAKE_ID],
                               'resource_type': ['os.nova.server'],
                               'user_id': [FAKE_ID]}
        self.assertEqual(expected_query_dict, query_params)

    @mock.patch.object(ResourceManager, '_get')
    def test_get_resource(self, mock_get):
        self.mgr.get(FAKE_ID)
        mock_get.assert_called_once_with('/resources/%s' % FAKE_ID, 'resource')

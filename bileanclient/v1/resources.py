# -*- coding: utf-8 -*-
#
# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

import six
from six.moves.urllib import parse

from bileanclient.openstack.common.apiclient import base


class BileanResource(base.Resource):
    def __repr__(self):
        return "<Resource %s>" % self._info


class ResourceManager(base.BaseManager):
    resource_class = BileanResource

    def _list(self, url, response_key, obj_class=None, body=None):
        resp, body = self.client.get(url)

        if obj_class is None:
            obj_class = self.resource_class

        data = body[response_key]
        return ([obj_class(self, res, loaded=True) for res in data if res],
                resp)

    def list(self, **kwargs):
        """Retrieve a list of resources.

        :rtype: list of :class:`Resource`.
        """
        def paginate(params):
            '''Paginate resources, even if more than API limit.'''
            current_limit = int(params.get('limit') or 0)
            url = '/resources?%s' % parse.urlencode(params, True)
            resources, resp = self._list(url, 'resources')
            for resource in resources:
                yield resource

            num_resources = len(resources)
            remaining_limit = current_limit - num_resources
            if remaining_limit > 0 and num_resources > 0:
                params['limit'] = remaining_limit
                params['marker'] = resource.id
                for resource in paginate(params):
                    yield resource

        params = {}
        if 'filters' in kwargs:
            filters = kwargs.pop('filters')
            params.update(filters)

        for key, value in six.iteritems(kwargs):
            if value:
                params[key] = value

        return paginate(params)

    def get(self, resource_id):
        """Get the details for a specific resource.

        :param resource_id: ID of the resource
        """
        url = '/resources/%s' % parse.quote(str(resource_id))
        resp, body = self.client.get(url)
        return self.resource_class(self, body.get('resource'), loaded=True)

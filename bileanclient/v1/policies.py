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


class Policy(base.Resource):
    def __repr__(self):
        return "<Policy %s>" % self._info


class PolicyManager(base.BaseManager):
    resource_class = Policy

    def _list(self, url, response_key, obj_class=None, body=None):
        resp, body = self.client.get(url)

        if obj_class is None:
            obj_class = self.resource_class

        data = body[response_key]
        return ([obj_class(self, res, loaded=True) for res in data if res],
                resp)

    def list(self, **kwargs):
        """Retrieve a list of policies.

        :rtype: list of :class:`policy`.
        """
        def paginate(params):
            '''Paginate policies, even if more than API limit.'''
            current_limit = int(params.get('limit') or 0)
            url = '/policies?%s' % parse.urlencode(params, True)
            policies, resq = self._list(url, 'policies')
            for policy in policies:
                yield policy

            num_policies = len(policies)
            remaining_limit = current_limit - num_policies
            if remaining_limit > 0 and num_policies > 0:
                params['limit'] = remaining_limit
                params['marker'] = policy.id
                for policy in paginate(params):
                    yield policy

        params = {}
        if 'filters' in kwargs:
            filters = kwargs.pop('filters')
            params.update(filters)

        for key, value in six.iteritems(kwargs):
            if value:
                params[key] = value

        return paginate(params)

    def create(self, **kwargs):
        """Create a new policy."""
        resq, body = self.client.post(url, data=kwargs)
        return self.resource_class(self, body.get('policy'), loaded=True)

    def get(self, policy_id):
        """Get a specific policy."""
        url = '/policies/%s' % parse.quote(str(policy_id))
        resq, body = self.client.get(url)
        return self.resource_class(self, body.get('policy'), loaded=True)

    def action(self, policy_id, **kwargs):
        """Perform specified action on a policy."""
        url = '/policies/%s/action' % parse.quote(str(policy_id))
        resq, body = self.client.post(url, data=kwargs)
        return self.resource_class(self, body.get('policy'), loaded=True)

    def delete(self, policy_id):
        """Delete a specific policy."""
        return self._delete('/policies/%s' % parse.quote(str(policy_id)))

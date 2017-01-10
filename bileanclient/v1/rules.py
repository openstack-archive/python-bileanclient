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


class Rule(base.Resource):
    def __repr__(self):
        return "<Rule %s>" % self._info


class RuleManager(base.BaseManager):
    resource_class = Rule

    def _list(self, url, response_key, obj_class=None, body=None):
        resp, body = self.client.get(url)

        if obj_class is None:
            obj_class = self.resource_class

        data = body[response_key]
        return ([obj_class(self, res, loaded=True) for res in data if res],
                resp)

    def list(self, **kwargs):
        """Retrieve a list of rules.

        :rtype: list of :class:`Rule`.
        """
        def paginate(params):
            '''Paginate rules, even if more than API limit.'''
            current_limit = int(params.get('limit') or 0)
            url = '/rules?%s' % parse.urlencode(params, True)
            rules, resp = self._list(url, 'rules')
            for rule in rules:
                yield rule

            num_rules = len(rules)
            remaining_limit = current_limit - num_rules
            if remaining_limit > 0 and num_rules > 0:
                params['limit'] = remaining_limit
                params['marker'] = rule.id
                for rule in paginate(params):
                    yield rule

        return_request_id = kwargs.get('return_req_id', None)
        params = {}
        if 'filters' in kwargs:
            filters = kwargs.pop('filters')
            params.update(filters)

        for key, value in six.iteritems(kwargs):
            if value:
                params[key] = value

        return paginate(params)

    def create(self, **kwargs):
        """Create a rule by given data."""
        url = '/rules'
        resp, body = self.client.post(url, data=kwargs)
        rule = body.get('rule')
        return self.resource_class(self, rule, loaded=True)

    def get(self, rule_id):
        """Get a specific rule.

        :param rule_id: Id of the rule to get
        """
        url = '/rules/%s' % parse.quote(str(rule_id))
        resp, body = self.client.get(url)
        data = body.get('rule')
        return self.resource_class(self, data, loaded=True)

    def delete(self, rule_id):
        """Delete a specific rule.

        :param rule_id: Id of the rule to delete
        """
        return self._delete('/rules/%s' % parse.quote(str(rule_id)))

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

OS_REQ_ID_HDR = 'x-openstack-request-id'


class User(base.Resource):
    def __repr__(self):
        return "<User %s>" % self._info


class UserManager(base.BaseManager):
    resource_class = User

    def _list(self, url, response_key, obj_class=None, body=None):
        resp, body = self.client.get(url)

        if obj_class is None:
            obj_class = self.resource_class

        data = body[response_key]
        return ([obj_class(self, res, loaded=True) for res in data if res],
                resp)

    def list(self, **kwargs):
        """Retrieve a list of users.

        :rtype: list of :class:`User`.
        """
        def paginate(params, return_request_id=None):
            '''Paginate users, even if more than API limit.'''
            current_limit = int(params.get('limit') or 0)
            url = '/users?%s' % parse.urlencode(params, True)
            users, resp = self._list(url, 'users')
            for user in users:
                yield user

            if return_request_id is not None:
                return_request_id.append(resp.headers.get(OS_REQ_ID_HDR, None))

            num_users = len(users)
            remaining_limit = current_limit - num_users
            if remaining_limit > 0 and num_users > 0:
                params['limit'] = remaining_limit
                params['marker'] = user.id
                for user in paginate(params):
                    yield user

        return_request_id = kwargs.get('return_req_id', None)
        params = {}
        if 'filters' in kwargs:
            filters = kwargs.pop('filters')
            params.update(filters)

        for key, value in six.iteritems(kwargs):
            if value:
                params[key] = value

        return paginate(params, return_request_id)

    def get(self, user_id, return_request_id=None):
        """Get the details for a specific user.

        :param user_id: ID of the user
        :param return_request_id: If an empty list is provided, populate this
                              list with the request ID value from the header
                              x-openstack-request-id
        """
        resp, body = self.client.get('/users/%s' % parse.quote(str(user_id)))
        if return_request_id is not None:
            return_request_id.append(resp.headers.get(OS_REQ_ID_HDR, None))
        data = body.get('user')
        return self.resource_class(self, data, loaded=True)

    def action(self, user_id, **kwargs):
        """Perform specified action on user.

        :param user_id: ID of the user
        """
        url = '/users/%s/action' % parse.quote(str(user_id))
        return_request_id = kwargs.pop('return_req_id', None)
        resp, body = self.client.post(url, data=kwargs)
        if return_request_id is not None:
            return_request_id.append(resp.headers.get(OS_REQ_ID_HDR, None))
        return self.resource_class(self, body.get('user'), loaded=True)

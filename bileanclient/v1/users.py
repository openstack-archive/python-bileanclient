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

from bileanclient.common import utils
from bileanclient.openstack.common.apiclient import base


class User(base.Resource):
    def __repr__(self):
        return "<User %s>" % self._info


class UserManager(base.BaseManager):
    resource_class = User

    def list(self, **kwargs):
        """Retrieve a list of users.

        :rtype: list of :class:`User`.
        """
        def paginate(params):
            '''Paginate users, even if more than API limit.'''
            current_limit = int(params.get('limit') or 0)
            url = '/users?%s' % parse.urlencode(params, True)
            users = self._list(url, 'users')
            for user in users:
                yield user

            num_users = len(users)
            remaining_limit = current_limit - num_users
            if remaining_limit > 0 and num_users > 0:
                params['limit'] = remaining_limit
                params['marker'] = user.id
                for user in paginate(params):
                    yield user

        params = {}
        if 'filters' in kwargs:
            filters = kwargs.pop('filters')
            params.update(filters)

        for key, value in six.iteritems(kwargs):
            if value:
                params[key] = value

        return paginate(params)

    def get(self, user_id):
        """Get the details for a specific user.

        :param user_id: ID of the user
        """
        return self._get('/users/%s' % user_id, 'user')

    def action(self, user_id, **kwargs):
        """Perform specified action on user."""
        url = '/users/%s/action' % user_id
        return self._post(url, json=kwargs, response_key='user')

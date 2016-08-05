# -*- coding: utf-8 -*-
#
# Copyright 2012 OpenStack LLC.
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

from bileanclient.common import http
from bileanclient.v1 import policies
from bileanclient.v1 import resources
from bileanclient.v1 import rules
from bileanclient.v1 import users


class Client(object):
    """Client for the Bilean v1 API.

    :param string endpoint: A user-supplied endpoint URL for the bilean
                            service.
    :param function token: Provides token for authentication.
    :param integer timeout: Allows customization of the timeout for client
                            http requests. (optional)
    """

    def __init__(self, *args, **kwargs):
        """Initialize a new client for the Bilean v1 API."""
        self.http_client = http.get_http_client(*args, **kwargs)
        self.users = users.UserManager(self.http_client)
        self.rules = rules.RuleManager(self.http_client)
        self.policies = policies.PolicyManager(self.http_client)
        self.resources = resources.ResourceManager(self.http_client)

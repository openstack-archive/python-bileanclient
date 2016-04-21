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

from __future__ import print_function

import hashlib
import logging
import textwrap

from oslo_serialization import jsonutils
from oslo_utils import encodeutils
from oslo_utils import importutils
import prettytable
import re
import six
from six.moves.urllib import parse
import sys
import yaml

from bileanclient import exc
from bileanclient.openstack.common._i18n import _
from bileanclient.openstack.common._i18n import _LE
from bileanclient.openstack.common import cliutils

LOG = logging.getLogger(__name__)

SENSITIVE_HEADERS = ('X-Auth-Token', )

# Using common methods from oslo cliutils
arg = cliutils.arg
env = cliutils.env
print_list = cliutils.print_list


def link_formatter(links):
    def format_link(l):
        if 'rel' in l:
            return "%s (%s)" % (l.get('href', ''), l.get('rel', ''))
        else:
            return "%s" % (l.get('href', ''))
    return '\n'.join(format_link(l) for l in links or [])


def json_formatter(js):
    return jsonutils.dumps(js, indent=2, ensure_ascii=False,
                           separators=(', ', ': '))


def yaml_formatter(js):
    return yaml.safe_dump(js, default_flow_style=False)


def text_wrap_formatter(d):
    return '\n'.join(textwrap.wrap(d or '', 55))


def newline_list_formatter(r):
    return '\n'.join(r or [])


def print_dict(d, formatters=None):
    formatters = formatters or {}
    pt = prettytable.PrettyTable(['Property', 'Value'],
                                 caching=False, print_empty=False)
    pt.align = 'l'

    for field in d.keys():
        if field in formatters:
            pt.add_row([field, formatters[field](d[field])])
        else:
            pt.add_row([field, d[field]])
    print(pt.get_string(sortby='Property'))


def skip_authentication(f):
    """Function decorator used to indicate a caller may be unauthenticated."""
    f.require_authentication = False
    return f


def is_authentication_required(f):
    """Checks to see if the function requires authentication.

    Use the skip_authentication decorator to indicate a caller may
    skip the authentication step.
    """
    return getattr(f, 'require_authentication', True)


def import_versioned_module(version, submodule=None):
    module = 'bileanclient.v%s' % version
    if submodule:
        module = '.'.join((module, submodule))
    return importutils.import_module(module)


def exit(msg='', exit_code=1):
    if msg:
        print_err(msg)
    sys.exit(exit_code)


def print_err(msg):
    print(encodeutils.safe_decode(msg), file=sys.stderr)


def safe_header(name, value):
    if value is not None and name in SENSITIVE_HEADERS:
        h = hashlib.sha1(value)
        d = h.hexdigest()
        return name, "{SHA1}%s" % d
    else:
        return name, value


def debug_enabled(argv):
    if bool(env('BILEANCLIENT_DEBUG')) is True:
        return True
    if '--debug' in argv or '-d' in argv:
        return True
    return False


def strip_version(endpoint):
    """Strip version from the last component of endpoint if present."""
    # NOTE(flaper87): This shouldn't be necessary if
    # we make endpoint the first argument. However, we
    # can't do that just yet because we need to keep
    # backwards compatibility.
    if not isinstance(endpoint, six.string_types):
        raise ValueError("Expected endpoint")

    version = None
    # Get rid of trailing '/' if present
    endpoint = endpoint.rstrip('/')
    url_parts = parse.urlparse(endpoint)
    (scheme, netloc, path, __, __, __) = url_parts
    path = path.lstrip('/')
    # regex to match 'v1' or 'v2.0' etc
    if re.match('v\d+\.?\d*', path):
        version = float(path.lstrip('v'))
        endpoint = scheme + '://' + netloc
    return endpoint, version


def format_parameters(params, parse_semicolon=True):
    '''Reformat parameters into dict of format expected by the API.'''

    if not params:
        return {}

    if parse_semicolon:
        # expect multiple invocations of --parameters but fall back
        # to ; delimited if only one --parameters is specified
        if len(params) == 1:
            params = params[0].split(';')

    parameters = {}
    for p in params:
        try:
            (n, v) = p.split(('='), 1)
        except ValueError:
            msg = _('Malformed parameter(%s). Use the key=value format.') % p
            raise exc.CommandError(msg)

        if n not in parameters:
            parameters[n] = v
        else:
            if not isinstance(parameters[n], list):
                parameters[n] = [parameters[n]]
            parameters[n].append(v)

    return parameters


def get_response_body(resp):
    body = resp.content
    if 'application/json' in resp.headers.get('content-type', ''):
        try:
            body = resp.json()
        except ValueError:
            LOG.error(_LE('Could not decode response body as JSON'))
    else:
        body = None
    return body


def parse_query_url(url):
    base_url, query_params = url.split('?')
    return base_url, parse.parse_qs(query_params)


def get_spec_content(filename):
    with open(filename, 'r') as f:
        try:
            data = yaml.load(f)
        except Exception as ex:
            raise exc.CommandError(_('The specified file is not a valid '
                                     'YAML file: %s') % six.text_type(ex))
    return data


def format_nested_dict(d, fields, column_names):
    if d is None:
        return ''
    pt = prettytable.PrettyTable(caching=False, print_empty=False,
                                 header=True, field_names=column_names)
    for n in column_names:
        pt.align[n] = 'l'

    keys = sorted(d.keys())
    for field in keys:
        value = d[field]
        if not isinstance(value, six.string_types):
            value = jsonutils.dumps(value, indent=2, ensure_ascii=False)
        pt.add_row([field, value.strip('"')])

    return pt.get_string()


def nested_dict_formatter(d, column_names):
    return lambda o: format_nested_dict(o, d, column_names)

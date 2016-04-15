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

import logging
import textwrap

from oslo_serialization import jsonutils
from oslo_utils import importutils
import prettytable
import six
import yaml

from bileanclient import exc
from bileanclient.openstack.common._i18n import _
from bileanclient.openstack.common._i18n import _LE
from bileanclient.openstack.common import cliutils

LOG = logging.getLogger(__name__)


supported_formats = {
    "json": lambda x: jsonutils.dumps(x, indent=2),
    "yaml": yaml.safe_dump
}

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


def event_log_formatter(events):
    """Return the events in log format."""
    event_log = []
    log_format = ("%(event_time)s "
                  "[%(rsrc_name)s]: %(rsrc_status)s  %(rsrc_status_reason)s")
    for event in events:
        event_time = getattr(event, 'event_time', '')
        log = log_format % {
            'event_time': event_time.replace('T', ' '),
            'rsrc_name': getattr(event, 'resource_name', ''),
            'rsrc_status': getattr(event, 'resource_status', ''),
            'rsrc_status_reason': getattr(event, 'resource_status_reason', '')
        }
        event_log.append(log)

    return "\n".join(event_log)


def import_versioned_module(version, submodule=None):
    module = 'bileanclient.v%s' % version
    if submodule:
        module = '.'.join((module, submodule))
    return importutils.import_module(module)


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


def get_spec_content(filename):
    with open(filename, 'r') as f:
        try:
            data = yaml.load(f)
        except Exception as ex:
            raise exc.CommandError(_('The specified file is not a valid '
                                     'YAML file: %s') % six.text_type(ex))
    return data


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

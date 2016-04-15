# -*- coding: utf-8 -*-
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

from bileanclient.common import utils
import bileanclient.exc as exc
from bileanclient.openstack.common._i18n import _

logger = logging.getLogger(__name__)


@utils.arg('id', metavar='<id>', help="ID of user to show.")
def do_user_show(bc, args):
    """Show detailed information for a user."""
    fields = {'user_id': args.id}
    try:
        user = bc.users.get(**fields)
    except exc.HTTPNotFound:
        raise exc.CommandError(_('User not found: %s') % args.id)
    else:
        formatters = {
            'status_reason': utils.text_wrap_formatter,
        }
        utils.print_dict(user.to_dict(), formatters=formatters) 


@utils.arg('-s', '--show-deleted', default=False, action="store_true",
           help=_('Include soft-deleted users in the user listing.'))
@utils.arg('-f', '--filters', metavar='<KEY1=VALUE1;KEY2=VALUE2...>',
           help=_('Filter parameters to apply on returned users. '
                  'This can be specified multiple times, or once with '
                  'parameters separated by a semicolon.'),
           action='append')
@utils.arg('-l', '--limit', metavar='<LIMIT>',
           help=_('Limit the number of users returned.'))
@utils.arg('-m', '--marker', metavar='<ID>',
           help=_('Only return users that appear after the given user ID.'))
@utils.arg('-k', '--sort-keys', metavar='<KEY1;KEY2...>',
           help=_('List of keys for sorting the returned users. '
                  'This can be specified multiple times or once with keys '
                  'separated by semicolons. Valid sorting keys include '
                  '"balance", "status", "created_at", "updated_at".'),
           action='append')
@utils.arg('-d', '--sort-dir', metavar='[asc|desc]',
           help=_('Sorting direction (either "asc" or "desc") for the sorting '
                  'keys.'))
def do_user_list(bc, args):
    """List users."""
    kwargs = {}
    fields = ['id', 'name', 'balance', 'credit', 'rate', 'status']
    sort_keys = ['name', 'balance', 'status', 'created_at', 'updated_at']

    sortby_index = 3
    if args:
        kwargs = {'limit': args.limit,
                  'marker': args.marker,
                  'filters': utils.format_parameters(args.filters),
                  'show_deleted': args.show_deleted}

        if args.sort_keys:
            keys = []
            for k in args.sort_keys:
                if ';' in k:
                    keys.extend(k.split(';'))
                else:
                    keys.append(k)
            for key in keys:
                if key not in sort_keys:
                    err = _("Sorting key '%(key)s' not one of the supported "
                            "keys: %(keys)s") % {'key': key, "keys": sort_keys}
                    raise exc.CommandError(err)
            kwargs['sort_keys'] = keys
            sortby_index = None

        if args.sort_dir:
            if args.sort_dir not in ('asc', 'desc'):
                raise exc.CommandError(_("Sorting direction must be one of "
                                         "'asc' and 'desc'"))
            kwargs['sort_dir'] = args.sort_dir

    users = bc.users.list(**kwargs)
    utils.print_list(users, fields, sortby_index=sortby_index)


@utils.arg('id',
           metavar='<id>',
           help='Id of user to recharge.')
@utils.arg('-v', '--value',
           metavar='<value>',
           type=float,
           help='Value of money to recharge for user.')
def do_user_recharge(bc, args):
    """Recharge for a user."""
    try:
        kwargs = {'recharge': {'value': args.value}}
        user = bc.users.action(args.id, **kwargs)
    except exc.HTTPNotFound:
        raise exc.CommandError(_('User not found: %s') % args.id)
    else:
        formatters = {
            'status_reason': utils.text_wrap_formatter,
        }
        utils.print_dict(user.to_dict(), formatters=formatters) 


@utils.arg('id',
           metavar='<id>',
           help='Id of user to attach policy.')
@utils.arg('policy',
           metavar='<policy>',
           help='Id of policy to attach to user.')
def do_user_attach_policy(bc, args):
    """Attach a specified policy to user."""
    try:
        kwargs = {'attach_policy': {'policy': args.policy}}
        user = bc.users.action(args.id, **kwargs)
    except exc.HTTPNotFound:
        raise exc.CommandError(_('User not found: %s') % args.id)
    else:
        formatters = {
            'status_reason': utils.text_wrap_formatter,
        }
        utils.print_dict(user.to_dict(), formatters=formatters) 


@utils.arg('-s', '--show-deleted', default=False, action="store_true",
           help=_('Include soft-deleted rules in the rule listing.'))
@utils.arg('-f', '--filters', metavar='<KEY1=VALUE1;KEY2=VALUE2...>',
           help=_('Filter parameters to apply on returned rules. '
                  'This can be specified multiple times, or once with '
                  'parameters separated by a semicolon.'),
           action='append')
@utils.arg('-l', '--limit', metavar='<LIMIT>',
           help=_('Limit the number of rules returned.'))
@utils.arg('-m', '--marker', metavar='<ID>',
           help=_('Only return rules that appear after the given rule ID.'))
@utils.arg('-k', '--sort-keys', metavar='<KEY1;KEY2...>',
           help=_('List of keys for sorting the returned rules. '
                  'This can be specified multiple times or once with keys '
                  'separated by semicolons. Valid sorting keys include '
                  '"balance", "status", "created_at", "updated_at".'),
           action='append')
@utils.arg('-d', '--sort-dir', metavar='[asc|desc]',
           help=_('Sorting direction (either "asc" or "desc") for the sorting '
                  'keys.'))

def do_rule_list(bc, args):
    """List rules."""
    kwargs = {}
    fields = ['id', 'name', 'type', 'created_at']
    sort_keys = ['name', 'type', 'created_at']

    sortby_index = None if args.sort_keys else 1
    if args:
        kwargs = {'limit': args.limit,
                  'marker': args.marker,
                  'filters': utils.format_parameters(args.filters),
                  'show_deleted': args.show_deleted}

        if args.sort_keys:
            keys = []
            for k in args.sort_keys:
                if ';' in k:
                    keys.extend(k.split(';'))
                else:
                    keys.append(k)
            for key in keys:
                if key not in sort_keys:
                    err = _("Sorting key '%(key)s' not one of the supported "
                            "keys: %(keys)s") % {'key': key, "keys": sort_keys}
                    raise exc.CommandError(err)
            kwargs['sort_keys'] = keys

        if args.sort_dir:
            if args.sort_dir not in ('asc', 'desc'):
                raise exc.CommandError(_("Sorting direction must be one of "
                                         "'asc' and 'desc'"))
            kwargs['sort_dir'] = args.sort_dir

    rules = bc.rules.list(**kwargs)
    utils.print_list(rules, fields, sortby_index=sortby_index)


@utils.arg('-s', '--spec-file', metavar='<SPEC FILE>', required=True,
           help=_('The spec file used to create the rule.'))
@utils.arg('-M', '--metadata', metavar='<KEY1=VALUE1;KEY2=VALUE2...>',
           help=_('Metadata values to be attached to the rule. '
                  'This can be specified multiple times, or once with '
                  'key-value pairs separated by a semicolon.'),
           action='append')
@utils.arg('name', metavar='<PROFILE_NAME>',
           help=_('Name of the rule to create.'))
def do_rule_create(bc, args):
    """Create a rule."""

    spec = utils.get_spec_content(args.spec_file)
    type_name = spec.get('type', None)
    type_version = spec.get('version', None)
    properties = spec.get('properties', None)
    if type_name is None:
        raise exc.CommandError(_("Missing 'type' key in spec file."))
    if type_version is None:
        raise exc.CommandError(_("Missing 'version' key in spec file."))
    if properties is None:
        raise exc.CommandError(_("Missing 'properties' key in spec file."))

    params = {
        'rule': { 
            'name': args.name,
            'spec': spec,
            'metadata': utils.format_parameters(args.metadata),
        }
    }

    rule = bc.rules.create(**params)
    _show_rule(bc, rule=rule)


@utils.arg('id', metavar='<RULE>',
           help=_('ID of rule to show.'))
def do_rule_show(bc, args):
    """Show the rule details."""
    _show_rule(bc, rule_id=args.id)


@utils.arg('id', metavar='<RULE>', nargs='+',
           help=_('ID of rule(s) to delete.'))
def do_rule_delete(bc, args):
    """Delete rule(s)."""
    failure_count = 0

    for rid in args.id:
        try:
            bc.rules.delete(rid)
        except Exception as ex:
            failure_count +=1
            print(ex)
    if failure_count > 0:
        msg = _('Failed to delete some of the specified rule(s).')
        raise exc.CommandError(msg)
    print('Rule deleted: %s' % args.id)


def _show_rule(bc, rule=None, rule_id=None):
    if rule is None:
        try:
            rule = bc.rules.get(rule_id)
        except exc.HTTPNotFound:
            raise exc.CommandError(_('Rule not found: %s') % rule_id)

    formatters = {
        'metadata': utils.json_formatter,
    }

    formatters['spec'] = utils.nested_dict_formatter(
        ['type', 'version', 'properties'],
        ['property', 'value'])

    utils.print_dict(rule.to_dict(), formatters=formatters)


@utils.arg('-s', '--show-deleted', default=False, action="store_true",
           help=_('Include soft-deleted policies in the policy listing.'))
@utils.arg('-f', '--filters', metavar='<KEY1=VALUE1;KEY2=VALUE2...>',
           help=_('Filter parameters to apply on returned policies. '
                  'This can be specified multiple times, or once with '
                  'parameters separated by a semicolon.'),
           action='append')
@utils.arg('-l', '--limit', metavar='<LIMIT>',
           help=_('Limit the number of policies returned.'))
@utils.arg('-m', '--marker', metavar='<ID>',
           help=_('Only return policies that appear after the given policy ID.'))
@utils.arg('-k', '--sort-keys', metavar='<KEY1;KEY2...>',
           help=_('List of keys for sorting the returned policies. '
                  'This can be specified multiple times or once with keys '
                  'separated by semicolons. Valid sorting keys include '
                  '"balance", "status", "created_at", "updated_at".'),
           action='append')
@utils.arg('-d', '--sort-dir', metavar='[asc|desc]',
           help=_('Sorting direction (either "asc" or "desc") for the sorting '
                  'keys.'))

def do_policy_list(bc, args):
    """List policies."""
    kwargs = {}
    fields = ['id', 'name', 'is_default', 'created_at']
    sort_keys = ['name', 'created_at']

    sortby_index = None if args.sort_keys else 1
    if args:
        kwargs = {'limit': args.limit,
                  'marker': args.marker,
                  'filters': utils.format_parameters(args.filters),
                  'show_deleted': args.show_deleted}

        if args.sort_keys:
            keys = []
            for k in args.sort_keys:
                if ';' in k:
                    keys.extend(k.split(';'))
                else:
                    keys.append(k)
            for key in keys:
                if key not in sort_keys:
                    err = _("Sorting key '%(key)s' not one of the supported "
                            "keys: %(keys)s") % {'key': key, "keys": sort_keys}
                    raise exc.CommandError(err)
            kwargs['sort_keys'] = keys

        if args.sort_dir:
            if args.sort_dir not in ('asc', 'desc'):
                raise exc.CommandError(_("Sorting direction must be one of "
                                         "'asc' and 'desc'"))
            kwargs['sort_dir'] = args.sort_dir

    policies = bc.policies.list(**kwargs)
    utils.print_list(policies, fields, sortby_index=sortby_index)


@utils.arg('name', metavar='<PROFILE_NAME>',
           help=_('Name of the policy to create.'))
@utils.arg('-r', '--rule', metavar='<RULE>', nargs='+',
           help=_('ID of rule(s) attached to the policy.'))
@utils.arg('-M', '--metadata', metavar='<KEY1=VALUE1;KEY2=VALUE2...>',
           help=_('Metadata values to be attached to the policy. '
                  'This can be specified multiple times, or once with '
                  'key-value pairs separated by a semicolon.'),
           action='append')
def do_policy_create(bc, args):
    """Create a policy."""
    params = {
        'policy': { 
            'name': args.name,
            'rules': args.rule,
            'metadata': utils.format_parameters(args.metadata),
        }
    }

    policy = bc.policies.create(**params)
    _show_policy(bc, policy=policy)


@utils.arg('id', metavar='<id>',
           help='Id of policy.')
@utils.arg('-r', '--rule', metavar='<RULE>', nargs='+',
           help=_('ID of rule(s) to add to the policy.'))
def do_policy_add_rules(bc, args):
    kwargs = {'add_rules': {'rules': args.rule}}
    policy = bc.policies.action(args.id, **kwargs)
    _show_policy(bc, policy=policy)


def _show_policy(bc, policy=None, policy_id=None):
    if policy is None:
        try:
            policy = bc.policies.get(policy_id)
        except exc.HTTPNotFound:
            raise exc.CommandError(_('policy not found: %s') % policy_id)

    formatters = {
        'metadata': utils.json_formatter,
    }

    utils.print_dict(policy.to_dict(), formatters=formatters)


@utils.arg('id', metavar='<POLICY>',
           help=_('ID of policy to show.'))
def do_policy_show(bc, args):
    """Show the policy details."""
    _show_policy(bc, policy_id=args.id)

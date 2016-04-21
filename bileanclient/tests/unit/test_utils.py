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
import collections
import mock
from six import moves
import sys
import testtools

from bileanclient.common import utils
from bileanclient import exc


class ShellTest(testtools.TestCase):

    def test_format_parameter_none(self):
        self.assertEqual({}, utils.format_parameters(None))

    def test_format_parameters(self):
        p = utils.format_parameters(['name=bilean_user;status=ACTIVE'])
        self.assertEqual({'name': 'bilean_user',
                          'status': 'ACTIVE'}, p)

    def test_format_parameters_split(self):
        p = utils.format_parameters([
            'name=bilean_user',
            'status=ACTIVE'])
        self.assertEqual({'name': 'bilean_user',
                          'status': 'ACTIVE'}, p)
 
    def test_format_parameters_multiple_semicolon_values(self):
        p = utils.format_parameters([
            'status=ACTIVE',
            'name=bilean;user'])
        self.assertEqual({'name': 'bilean;user',
                          'status': 'ACTIVE'}, p)
 
    def test_format_parameters_parse_semicolon_false(self):
        p = utils.format_parameters(
            ['name=bilean;a=b'],
            parse_semicolon=False)
        self.assertEqual({'name': 'bilean;a=b'}, p)
 
    def test_format_parameters_multiple_values_per_pamaters(self):
        p = utils.format_parameters([
            'status=ACTIVE',
            'status=FREE'])
        self.assertIn('status', p)
        self.assertIn('ACTIVE', p['status'])
        self.assertIn('FREE', p['status'])
 
    def test_format_parameter_bad_parameter(self):
        params = ['name=bilean_user;statusACTIVE']
        ex = self.assertRaises(exc.CommandError,
                               utils.format_parameters, params)
        self.assertEqual('Malformed parameter(statusACTIVE). '
                         'Use the key=value format.', str(ex))
 
    def test_format_multiple_bad_parameter(self):
        params = ['name=bilean_user', 'statusACTIVE']
        ex = self.assertRaises(exc.CommandError,
                               utils.format_parameters, params)
        self.assertEqual('Malformed parameter(statusACTIVE). '
                         'Use the key=value format.', str(ex))
 
    def test_link_formatter(self):
        self.assertEqual('', utils.link_formatter(None))
        self.assertEqual('', utils.link_formatter([]))
        self.assertEqual(
            'http://foo.example.com\nhttp://bar.example.com',
            utils.link_formatter([
                {'href': 'http://foo.example.com'},
                {'href': 'http://bar.example.com'}]))
        self.assertEqual(
            'http://foo.example.com (a)\nhttp://bar.example.com (b)',
            utils.link_formatter([
                {'href': 'http://foo.example.com', 'rel': 'a'},
                {'href': 'http://bar.example.com', 'rel': 'b'}]))
        self.assertEqual(
            '\n',
            utils.link_formatter([
                {'hrf': 'http://foo.example.com'},
                {}]))

    def test_json_formatter(self):
        self.assertEqual('null', utils.json_formatter(None))
        self.assertEqual('{}', utils.json_formatter({}))
        self.assertEqual('{\n  "foo": "bar"\n}',
                         utils.json_formatter({"foo": "bar"}))
        self.assertEqual(u'{\n  "Uni": "test\u2665"\n}',
                         utils.json_formatter({"Uni": u"test\u2665"}))

    def test_yaml_formatter(self):
        self.assertEqual('null\n...\n', utils.yaml_formatter(None))
        self.assertEqual('{}\n', utils.yaml_formatter({}))
        self.assertEqual('foo: bar\n',
                         utils.yaml_formatter({"foo": "bar"}))

    def test_text_wrap_formatter(self):
        self.assertEqual('', utils.text_wrap_formatter(None))
        self.assertEqual('', utils.text_wrap_formatter(''))
        self.assertEqual('one two three',
                         utils.text_wrap_formatter('one two three'))
        self.assertEqual(
            'one two three four five six seven eight nine ten eleven\ntwelve',
            utils.text_wrap_formatter(
                ('one two three four five six seven '
                 'eight nine ten eleven twelve')))

    def test_newline_list_formatter(self):
        self.assertEqual('', utils.newline_list_formatter(None))
        self.assertEqual('', utils.newline_list_formatter([]))
        self.assertEqual('one\ntwo',
                         utils.newline_list_formatter(['one', 'two']))


class CaptureStdout(object):
    """Context manager for capturing stdout from statements in its block."""
    def __enter__(self):
        self.real_stdout = sys.stdout
        self.stringio = moves.StringIO()
        sys.stdout = self.stringio
        return self

    def __exit__(self, *args):
        sys.stdout = self.real_stdout
        self.stringio.seek(0)
        self.read = self.stringio.read


class PrintListTestCase(testtools.TestCase):

    def test_print_list_with_list(self):
        Row = collections.namedtuple('Row', ['foo', 'bar'])
        to_print = [Row(foo='fake_foo1', bar='fake_bar2'),
                    Row(foo='fake_foo2', bar='fake_bar1')]
        with CaptureStdout() as cso:
            utils.print_list(to_print, ['foo', 'bar'])
        # Output should be sorted by the first key (foo)
        self.assertEqual("""\
+-----------+-----------+
| foo       | bar       |
+-----------+-----------+
| fake_foo1 | fake_bar2 |
| fake_foo2 | fake_bar1 |
+-----------+-----------+
""", cso.read())

    def test_print_list_with_None_data(self):
        Row = collections.namedtuple('Row', ['foo', 'bar'])
        to_print = [Row(foo='fake_foo1', bar='None'),
                    Row(foo='fake_foo2', bar='fake_bar1')]
        with CaptureStdout() as cso:
            utils.print_list(to_print, ['foo', 'bar'])
        # Output should be sorted by the first key (foo)
        self.assertEqual("""\
+-----------+-----------+
| foo       | bar       |
+-----------+-----------+
| fake_foo1 | None      |
| fake_foo2 | fake_bar1 |
+-----------+-----------+
""", cso.read())

    def test_print_list_with_list_sortby(self):
        Row = collections.namedtuple('Row', ['foo', 'bar'])
        to_print = [Row(foo='fake_foo1', bar='fake_bar2'),
                    Row(foo='fake_foo2', bar='fake_bar1')]
        with CaptureStdout() as cso:
            utils.print_list(to_print, ['foo', 'bar'], sortby_index=1)
        # Output should be sorted by the first key (bar)
        self.assertEqual("""\
+-----------+-----------+
| foo       | bar       |
+-----------+-----------+
| fake_foo2 | fake_bar1 |
| fake_foo1 | fake_bar2 |
+-----------+-----------+
""", cso.read())

    def test_print_list_with_list_no_sort(self):
        Row = collections.namedtuple('Row', ['foo', 'bar'])
        to_print = [Row(foo='fake_foo2', bar='fake_bar1'),
                    Row(foo='fake_foo1', bar='fake_bar2')]
        with CaptureStdout() as cso:
            utils.print_list(to_print, ['foo', 'bar'], sortby_index=None)
        # Output should be in the order given
        self.assertEqual("""\
+-----------+-----------+
| foo       | bar       |
+-----------+-----------+
| fake_foo2 | fake_bar1 |
| fake_foo1 | fake_bar2 |
+-----------+-----------+
""", cso.read())

    def test_print_list_with_generator(self):
        Row = collections.namedtuple('Row', ['foo', 'bar'])

        def gen_rows():
            for row in [Row(foo='fake_foo1', bar='fake_bar2'),
                        Row(foo='fake_foo2', bar='fake_bar1')]:
                yield row
        with CaptureStdout() as cso:
            utils.print_list(gen_rows(), ['foo', 'bar'])
        self.assertEqual("""\
+-----------+-----------+
| foo       | bar       |
+-----------+-----------+
| fake_foo1 | fake_bar2 |
| fake_foo2 | fake_bar1 |
+-----------+-----------+
""", cso.read())


class PrintDictTestCase(testtools.TestCase):

    def test_print_dict(self):
        data = {'foo': 'fake_foo', 'bar': 'fake_bar'}
        with CaptureStdout() as cso:
            utils.print_dict(data)
        # Output should be sorted by the Property
        self.assertEqual("""\
+----------+----------+
| Property | Value    |
+----------+----------+
| bar      | fake_bar |
| foo      | fake_foo |
+----------+----------+
""", cso.read())

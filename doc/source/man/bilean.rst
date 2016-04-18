======
bilean
======

.. program:: bilean

SYNOPSIS
========

  `bilean` [options] <command> [command-options]

  `bilean help`

  `bilean help` <command>


DESCRIPTION
===========

`bilean` is a command line client for controlling OpenStack Bilean.

Before the `bilean` command is issued, ensure the environment contains
the necessary variables so that the CLI can pass user credentials to
the server.
See `Getting Credentials for a CLI`  section of `OpenStack CLI Guide`
for more info.


OPTIONS
=======

To get a list of available commands and options run::

    bilean help

To get usage and options of a command run::

    bilean help <command>


EXAMPLES
========

Get information about rule-create command::

    bilean help rule-create

List available rules::

    bilean rule-list

List available policies::

    bilean policy-list

Create a rule::

    bilean rule-create rule_name -s rule.spec

View rule information::

    bilean rule-show rule_id

Delete a rule:: 

    bilean rule-delete rule_id

BUGS
====

Bilean client is hosted in Launchpad so you can view current bugs
at https://bugs.launchpad.net/python-bileanclient/.

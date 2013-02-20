dns-python
==========

a small intercepting server

This small piece of software depends on:

* dnspython http://www.dnspython.org/
* python
* yaml

it creates a simple DNS server listening on a configurable port that can answer to some queries from a config file and others
by asking a defined nameserver. If the mappings are redefined, you can send a SIGUSR1 to the process and it will reload its configuration.

Usage:

    python server.py


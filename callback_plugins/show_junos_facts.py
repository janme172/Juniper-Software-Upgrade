from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import collections
import os
import time
import pprint
import json
from six import iteritems

from ansible.plugins.callback import CallbackBase
from ansible import constants as C

class CallbackModule(CallbackBase):
  """
  This callback add extra logging for the module junos_jsnapy .
  """
  CALLBACK_VERSION = 2.0
  CALLBACK_TYPE = 'aggregate'
  CALLBACK_NAME = 'show_junos_facts'

## useful links regarding Callback
## https://github.com/ansible/ansible/blob/devel/lib/ansible/plugins/callback/__init__.py

  def __init__(self):
    self._pp = pprint.PrettyPrinter(indent=4)
    self._results = {}

    super(CallbackModule, self).__init__()

  def v2_runner_on_ok(self, result):
    super(CallbackModule, self).v2_runner_on_ok(result)
    """
    Collect test results for all tests executed if module is junos_jsnapy
    """
    self._display.display(str(result._result))
    return
    #self._display.display("-----------Invoked v2_runner_on_ok----------------------")
    ## Extract module name
    module_name = ''
    module_args = {}
    #self._display.display(str(result._result))
    if 'invocation' in result._result:
      if 'module_name' in result._result['invocation']:
        module_name = result._result['invocation']['module_name']
      module_args = result._result['invocation']['module_args']

    ## Check if dic return has all valid information
    #if module_name == '' or module_args == {}:                  # Commented because it is not coming in Juniper_junos_jsnapy module output
    #    return None
    if 'action' not in module_args:
        return None
    # Extra check added so that it only runs for juniper_junos_jsnapy module only
    if  module_args['action'] not in ('snapcheck', 'check') or not ('test_files' in module_args or 'config_file' in module_args):
        return None
    # Added the <''> because module name not coming in results in case of juniper_junos_jsnapy module. Only module args are available.
    if module_name in ('juniper_junos_jsnapy', 'junos_jsnapy', '') and (module_args['action'] in ('snapcheck', 'check')):

      ## Check if dict entry already exist for this host
      host = result._host.name
      if not host in self._results.keys():
        self._results[host] = []

      self._results[host].append(result)


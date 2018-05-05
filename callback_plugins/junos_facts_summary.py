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
  CALLBACK_NAME = 'junos_facts_summary'

  def __init__(self):
    self._pp = pprint.PrettyPrinter(indent=4)
    self._results = {}

    super(CallbackModule, self).__init__()

  def v2_runner_on_ok(self, result):
    """
    This Modules prints out the some of the facts for Juniper devices one collected.
    """
    super(CallbackModule, self).v2_runner_on_ok(result)
    module_args = {}
    #self._display.display(str(result._result))
    if 'invocation' in result._result:
      module_args = result._result['invocation']['module_args']
    if 'ansible_facts' not in result._result:
        return
    ansible_facts = result._result['ansible_facts']
    if 'junos' not in ansible_facts:
        return
    junos_dict = ansible_facts['junos']
    if 'has_2RE' not in junos_dict:
        return
    host = module_args['host']
    junos_has_2RE = junos_dict['has_2RE']
    software_ver_re0 = junos_dict['version_RE0']
    software_ver_re1 = junos_dict['version_RE1']
    re_display_info_keys = ['status', 'model', 'mastership_state']
    banner_text = ' Device: {} '.format(host)
    self._display.display('{:#^100}'.format(banner_text))
    if junos_has_2RE:
        self._display.display('Device has 2 Routing engines. Please find details below:', color='purple')
    else:
        self._display.display('Device has only 1 Routing engine. Please find details below:', color='purple')
    self._display.display('\tMASTER RE: {0}\t\tMODEL: {1}'.format(junos_dict['master'], junos_dict['model'], ), color='blue')
    #self._display.display('\tSERIAL NUMBER: {}'.format(junos_dict['serialnumber']), color='blue')   
    #self._display.display('\tMASTER RE: {}'.format(junos_dict['master']), color=C.COLOR_ERROR)
    #self._display.display('\tMODEL: {}'.format(junos_dict['model']), color='blue')
    #self._display.display('\tSWITCH STYLE: {}'.format(junos_dict['switch_style']), color='blue')
#    if 'RE0' in junos_dict:
#        self._display.display('\tRouting Engine RE0:', color='purple')
#        self._display.display('\t\tSOFTWARE VERSION: {0}'.format(software_ver_re0), color='blue')
#        for key, val in junos_dict['RE0'].items():
#            if key.lower() in re_display_info_keys: 
#                self._display.display('\t\t{0}: {1}'.format(key.upper().replace('_', ' '), val), color='blue')    
#    if 'RE1' in junos_dict and junos_has_2RE:
#        self._display.display('\tRouting Engine RE1:', color='purple')
#        self._display.display('\t\tSOFTWARE VERSION: {0}'.format(software_ver_re1), color='blue')
#        for key, val in junos_dict['RE1'].items():
#            if key.lower() in re_display_info_keys:
#                self._display.display('\t\t{0}: {1}'.format(key.upper().replace('_', ' '), val), color='blue')
    self._display.display('{:#^100}'.format(''))

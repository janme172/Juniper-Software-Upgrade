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
  CALLBACK_NAME = 'jsnapyfull'

  def __init__(self):
    self._pp = pprint.PrettyPrinter(indent=4)
    self._results = {}

    super(CallbackModule, self).__init__()

  def v2_runner_on_ok(self, result):
    """
    Collect test results for all tests executed if module is junos_jsnapy
    """
    module_name = ''
    module_args = {}
    #self._display.display(str(result._result))
    if 'invocation' in result._result:
      if 'module_name' in result._result['invocation']:
        module_name = result._result['invocation']['module_name']
      module_args = result._result['invocation']['module_args']

    if 'action' not in module_args:
        return None
    # Extra check added so that it only runs for juniper_junos_jsnapy module only
    if  module_args['action'] not in ('snapcheck', 'check') or not ('test_files' in module_args or 'config_file' in module_args):
        return None
    # Added the <''> because module name not coming in results in case of juniper_junos_jsnapy module. Only module args are available.
    if module_name in ('juniper_junos_jsnapy', 'junos_jsnapy', '') and (module_args['action'] in ('snapcheck', 'check')):
      self.print_test_result(result)

  def print_test_result(self, result):
          host = result._host.name
          has_printed_banner = False
          res = result._result
          test_status = "Unknown"
          try:
            test_status = res['final_result']
          except:
            pass
          for command_or_rpc, test_results in iteritems(res['test_results']):
            has_printed_test_name = False
            node_name = ''
            for testlet in test_results:
                if len(testlet) == 1:
                    continue
                test_name = testlet['test_name']
                failed_test_count = testlet['count']['fail']
                passed_test_count = testlet['count']['pass']
                node_name = testlet['node_name']
                try:
                    expected_node_value = testlet['expected_node_value']
                except:
                    expected_node_value = False
                test_operation = testlet['testoperation']
                xpath = testlet['xpath']
                if not has_printed_banner:
                  self._display.banner("JSNAPy Results for Device: {}".format(host))
                  has_printed_banner = True
                if not has_printed_test_name:
	            self._display.display("Test name: {}".format(test_name))
                    has_printed_test_name = True
                node_name = testlet['node_name']
                self._display.display("\tNode name: {0}".format(node_name))
                self._display.display("\tFailed: {0}".format(failed_test_count))
                self._display.display("\tPassed: {0}".format(passed_test_count))
                for test in testlet['passed']:
                  data = ''
                  if 'post' in test:
                      data = test['post']
                  else:
                      data = test
                  try:
                    pass_message = test['message']
                  except:
                    pass_message = "Value of '{0}' '{1}' at '{2}'".format(str(testlet['node_name']), str(testlet['testoperation']), str(testlet['xpath']))
                if  len(testlet['failed']) == 0:
                    if expected_node_value:
                        pass_message = "All '{0}' '{1}' '{4}' at '{2}'. [{3} matched]".format(node_name, test_operation, xpath, passed_test_count, expected_node_value)
                    else:
                        pass_message = "All '{0}' '{1}' at '{2}'. [{3} matched]".format(node_name, test_operation, xpath, passed_test_count)
                else:
                    if expected_node_value:
                        pass_message = "'{0}' '{1}' at '{4}' '{2}'. [{3} matched]".format(node_name, test_operation, xpath, passed_test_count, expected_node_value)
                    else:
                        pass_message = "'{0}' '{1}' at '{2}'. [{3} matched]".format(node_name, test_operation, xpath, passed_test_count)

                self._display.display("\tPass: {0}".format(pass_message), color='green')
                  
#                 self._display.display("\t\tAnsible Output: Value of '{0}' '{1}' at '{2}' with {3}".format(str(testlet['node_name']), str(testlet['testoperation']), str(testlet['xpath']), json.dumps(data)), color='green')


                for test in testlet['failed']:
                  data = ''
                  if 'post' in test:
                      data = test['post']
                  else:
                      data = test
                  try:
                    fail_message = test['message']
                  except:
                    fail_message = "Value of '{0}' not '{1}' at '{2}' with {3}".format(str(testlet['node_name']), str(testlet['testoperation']), str(testlet['xpath']), json.dumps(data))
                  self._display.display(
                    "\tFail: {0}".format(fail_message), color=C.COLOR_ERROR
                  )
#                  self._display.display("\t\tAnsible Output: Value of '{0}' not '{1}' at '{2}' with {3}".format(str(testlet['node_name']), str(testlet['testoperation']), str(testlet['xpath']), json.dumps(data)), color=C.COLOR_ERROR)



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
#    return
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

          tests_total = 0
          tests_failed = 0
          tests_passed = 0
          
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
                test_operation = testlet['testoperation']
                xpath = testlet['xpath']
                try:
                    expected_node_value = testlet['expected_node_value']
                except:
                    expected_node_value = ''
                if not has_printed_banner:
                    self._display.banner("JSNAPy Results for Device: {}".format(host), color='purple')
                    #self._display.display("JSNAPy Results for Device: {:#^200}".format(host))
                    has_printed_banner = True
                if not has_printed_test_name:
	            self._display.display("Test name: {}".format(test_name))
                    self._display.display("Command/RPC: {}".format(command_or_rpc))
                    has_printed_test_name = True
                node_name = testlet['node_name']
#                self._display.display("\tNode name: {0}".format(node_name))
#                self._display.display("\tFailed: {0}".format(failed_test_count))
#                self._display.display("\tPassed: {0}".format(passed_test_count))
                   
                custom_message = ''
                tests_total += 1
                if failed_test_count == 0:
                    tests_passed += 1
                    if test_operation.lower() == 'is-equal':
                        custom_message = "'{2}/{0}'s/es are equal to '{1}'".format(node_name, expected_node_value, xpath)
                    elif test_operation.lower() == 'no-diff':
                        custom_message = "'{2}/{0}'s/es are same in PRE and POST snapshots at '{2}'".format(node_name, expected_node_value, xpath)
                    elif test_operation.lower() == 'list-not-less':
                        custom_message = "'{1}/{0}'s/es present in POST Snapshot are also present in PRE Snapshot".format(node_name, xpath)
                    elif test_operation.lower() == 'list-not-more':
                        custom_message = "'{1}/{0}'s/es present in PRE Snapshot are also present in POST Snapshot".format(node_name, xpath)
                    elif test_operation.lower() == 'delta':
                        custom_message = "'{1}/{0}' value changes were within defined thresholds between PRE and POST Snapshot".format(node_name, xpath)
                    elif test_operation.lower() == 'all-same':
                        custom_message = "'{1}/{0}' values are same".format(node_name, xpath)
                    all_pass_message = "All {0}. [{1} matched]".format(custom_message, passed_test_count)
                    self._display.display("\tPASS: {0}".format(all_pass_message), color='green')
                else:
                    tests_failed += 1
                    if test_operation.lower() == 'is-equal':
                        custom_message = "'{2}/{0}'s/es are not equal to '{1}'".format(node_name, expected_node_value, xpath)
                    elif test_operation.lower() == 'no-diff':
                        custom_message = "'{2}/{0}'s/es are not same in PRE and POST snapshots at '{2}'".format(node_name, expected_node_value, xpath)
                    elif test_operation.lower() == 'list-not-less':
                        custom_message = "'{1}/{0}'s/es present in POST Snapshot are not present in PRE Snapshot".format(node_name, xpath)
                    elif test_operation.lower() == 'list-not-more':
                        custom_message = "'{1}/{0}'s/es present in PRE Snapshot are not present in POST Snapshot".format(node_name, xpath)
                    elif test_operation.lower() == 'delta':
                        custom_message = "'{1}/{0}' value changes were not within defined thresholds between PRE and POST Snapshot".format(node_name, xpath)
                    elif test_operation.lower() == 'all-same':
                        custom_message = "'{1}/{0}' values are not same".format(node_name, xpath)
                    all_fail_message = "All {0}. [{1} matched/{2} failed]".format(custom_message, passed_test_count, failed_test_count)
                    self._display.display("\tFAIL: {0}".format(all_fail_message), color=C.COLOR_ERROR)

                if failed_test_count != 0: 
                    for test in testlet['failed']:
                        data = ''
                        if 'post' in test:
                            data = test['post']
                        else:
                            data = test
                        if test_operation.lower() == 'list-not-more':
                            test_operation = '[Missing before]'
                        elif test_operation.lower() == 'list-not-less':
                            test_operation = '[Available now]'
                        try:
                            fail_message = test['message']
                        except:
                            fail_message = "Value of '{0}' not '{1}' at '{2}' with {3}".format(node_name, test_operation, xpath, json.dumps(data))
                        self._display.display("\t\tFAIL: {0}".format(fail_message), color=C.COLOR_ERROR)
#                  self._display.display("\t\tAnsible Output: Value of '{0}' not '{1}' at '{2}' with {3}".format(str(testlet['node_name']), str(testlet['testoperation']), str(testlet['xpath']), json.dumps(data)), color=C.COLOR_ERROR)
          overall_status = "Failed"
          if tests_failed == 0:
              overall_status = "Passed"
          self._display.display("\nTests Summary:\n\tTotal Tests: {0}\n\tTests Passed: {1}\n\tTests Failed: {2}\n\tOverall Status: {3}".format(tests_total, tests_passed, tests_failed, overall_status))

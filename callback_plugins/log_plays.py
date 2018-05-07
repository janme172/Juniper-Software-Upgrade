# (C) 2012, Michael DeHaan, <michael.dehaan@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import datetime, os, paramiko, json
DOCUMENTATION = '''
    callback: log_plays
    type: notification
    short_description: write playbook output to log file
    version_added: historical
    description:
      - This callback writes playbook output to a file per host in the `/var/log/ansible/hosts` directory
      - "TODO: make this configurable"
    requirements:
     - Whitelist in configuration
     - A writeable /var/log/ansible/hosts directory by the user executing Ansible on the controller
'''
RE_STRS = ['RE0', 'RE1']
import os
import time
import json
from collections import MutableMapping

from ansible.module_utils._text import to_bytes
from ansible.plugins.callback import CallbackBase


# NOTE: in Ansible 1.2 or later general logging is available without
# this plugin, just set ANSIBLE_LOG_PATH as an environment variable
# or log_path in the DEFAULTS section of your ansible configuration
# file.  This callback is an example of per hosts logging for those
# that want it.


class CallbackModule(CallbackBase):
    """
    logs playbook results, per host, in /var/log/ansible/hosts
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'log_plays'
#    CALLBACK_NEEDS_WHITELIST = True

    TIME_FORMAT = "%b %d %Y %H:%M:%S"
    MSG_FORMAT = "Task Name: %(task_name)s\nTimestamp: %(now)s\nTask Status:%(category)s\n%(data)s\n"

    def __init__(self):
        self.play_start_datetime = datetime.datetime.now()
        self._parent_log_path = '/home/ansible/Logs/RouterSoftwareUpgrade/remotelogs/'
        self.log_dir = None
        self._log_host = '62.243.147.45'
        self._log_host_user = 'ansible'
        self._log_host_pass = 'ansible'
        self.sftp = None
        self.create_sftp_to_log_server()
        self.create_log_dir()
        super(CallbackModule, self).__init__()

        if not os.path.exists(self._parent_log_path):
            os.makedirs(self._parent_log_path)
 
    def create_sftp_to_log_server(self):
        if self._log_host and self._log_host_user and self._log_host_pass:
            transport = paramiko.Transport(("62.243.147.45", 22))
            transport.connect(username = "ansible", password = "ansible")
            self.sftp = paramiko.SFTPClient.from_transport(transport)
 
    def create_log_dir(self):
        date_str = self.play_start_datetime.strftime("%m-%d-%Y")
        time_str = self.play_start_datetime.strftime("%H%M%S")
        date_time_str = '{0}_{1}'.format(date_str, time_str)
        remote_log_dir = os.path.join(self._parent_log_path, date_time_str)
        try:
            self.sftp.stat(os.path.join(remote_log_dir))
        except IOError:
            self.sftp.mkdir(remote_log_dir)
        self.log_dir = remote_log_dir
        
        
    def append_log_file(self, file_path, log_text):
        f = self.sftp.open(file_path, "a+")
        f.write(log_text)
        f.close()

    def log(self, host, category, data):
        if isinstance(data, MutableMapping):
            if '_ansible_verbose_override' in data:
                # avoid logging extraneous data
                data = 'omitted'
            else:
                data = data.copy()
                invocation = data.pop('invocation', None)
                data = json.dumps(data, indent=2)
                #data = json.loads(data)
                #if invocation is not None:
                #    data = json.dumps(invocation, indent=2) #+ " => %s " % data

        file_path = os.path.join(self.log_dir, host)
        task_name = self.task_name
        task_status = category
        task_timestamp = time.strftime(self.TIME_FORMAT, time.localtime())
        task_json_response = data
        response = '\n'+'-'*100
        response += '\nTask Name: {0}\nTask Status: {1}\nTask Start Time: {2}\n'.format(task_name, task_status, task_timestamp)
 
        if task_status.strip().upper() != 'SKIPPED':
            task_dict = json.loads(task_json_response)
        if task_name.strip().strip('.') == 'Set the play start date and time variables':
            if task_status.upper().strip() == 'OK':
                response = 'Playbook started at {0} on {1}.'.format(task_dict['ansible_facts']['play_start_time'], task_dict['ansible_facts']['play_start_date'])
        elif task_name.strip().strip('.') == 'Gather facts from Junos devices without configuration':
            if task_status.upper().strip() == 'OK':
                ansible_facts = task_dict['ansible_facts']
                junos = ansible_facts['junos']
                serial_number = junos['serialnumber']
                model = junos['model']
                master_re = junos['master']
                switch_style = junos['switch_style']
                response += '''
######################### Device Information #########################
Serial Number: {0}
Model: {1}
Master RE: {2}
Switch Style: {3}'''.format(serial_number, model, master_re, switch_style)
                has_2_re = 'Yes' if junos['has_2RE'] else 'No'
                response += '\nDual RE: {}'.format(has_2_re)
                for RE in RE_STRS:
                    if junos[RE]:
                        response += '\nDetail for Routing Engine {}:'.format(RE)
                        for key, val in junos[RE].iteritems():
                            response += '\n\t{0}: {1}'.format(key.strip().replace('_', ' ').title(), val)
        elif task_name.strip().strip('.') == 'Create the log directories':
            if task_status.upper().strip() == 'OK':
                results = task_dict['results']
                for result in results:
                    pass
                response += ''
        elif task_name.strip().strip('.').startswith('Aborting -'):
            if task_status.upper().strip() == 'FAILED':
                response += 'Message: {}'.format(task_dict['msg'].encode('utf-8'))
            if task_status.upper().strip() == 'SKIPPED':
                response += 'Message: Play will continue...'
        elif task_name.strip().strip('.') == 'Get the Master RE before RE Switchover':
            if task_status.upper().strip() == 'OK':
                response += 'Current Master RE: {}'.format(task_dict['ansible_facts']['master_re_before_switchover'])
        elif task_name.strip().strip('.') == 'Get the Master RE after RE Switchover':
            if task_status.upper().strip() == 'OK':
                response += 'Current Master RE: {}'.format(task_dict['ansible_facts']['master_re_after_switchover'])
        elif task_name.strip().strip('.').startswith('Take PRE Snapshot -'):
            if task_status.upper().strip() == 'OK':
                response += 'Message: PRE Snapshot taken successfully.'
            else:
                response += 'Message: Issue while taking PRE Snapshot.'
        elif task_name.strip().strip('.').startswith('Take POST snapshot -'):
            if task_status.upper().strip() == 'OK':
                response += 'Message: POST Snapshot taken successfully.'
            else:
                response += 'Message: Issue while taking POST Snapshot.'
        elif task_name.strip().strip('.') == 'Check if RE has changed':
            if task_status.upper().strip() == 'OK':
               response += 'Message: RE has changed successfully.'
            if task_status.upper().strip() == 'FAILED':
               response += 'Message: RE has not changed'
        elif task_name.strip().strip('.') == 'Perform RE Switchover':
            response += 'Message: Performing RE Switchover'
            
        elif task_name.strip().strip('.').startswith('Compare PRE and POST Snapshots -') or task_name.strip().strip('.').startswith('Validate -'):
            if task_status.upper().strip() == 'OK':
                host = task_dict['device']
                has_printed_banner = False
                test_status = "Unknown"
                tests_total = 0
                tests_failed = 0
                tests_passed = 0
                for command_or_rpc, test_results in task_dict['test_results'].iteritems():
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
                            response += "\nJSNAPy Results for Device: {}".format(host)
                            #self._display.display("JSNAPy Results for Device: {:#^200}".format(host))
                            has_printed_banner = True
                        if not has_printed_test_name:
                            response += "\nTest name: {}".format(test_name)
                            response += "\nCommand/RPC: {}".format(command_or_rpc)
                            has_printed_test_name = True
                        node_name = testlet['node_name']
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
                            response += "\n\tPASS: {0}".format(all_pass_message)
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
                            response += "\n\tFAIL: {0}".format(all_fail_message)
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
                                response += "\n\t\tFAIL: {0}".format(fail_message)
                overall_status = "Failed"
                if tests_failed == 0:
                    overall_status = "Passed"
                response += "\nTests Summary:\n\tTotal Tests: {0}\n\tTests Passed: {1}\n\tTests Failed: {2}\n\tOverall Status: {3}".format(tests_total, tests_passed, tests_failed, overall_status)
        else:
            response += task_json_response
        response += '\n'+'-'*100
        self.append_log_file(file_path, response)


        #now = time.strftime(self.TIME_FORMAT, time.localtime())
        
        #msg = to_bytes(self.MSG_FORMAT % dict(now=now, category=category, data=data, task_name=self.task_name))
        #with open(pathhost, "ab") as fd:
        #    fd.write('#####-----Task Start-----#####\n')
         #   fd.write(msg)
         #   fd.write('#####-----Task End-----#####\n')

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.task_name = task.get_name()
        #self.play_start_datetime = datetime.datetime.now()

    def runner_on_failed(self, host, res, ignore_errors=False):
        self.log(host, 'FAILED', res)

    def runner_on_ok(self, host, res):
        self.log(host, 'OK', res)

    def runner_on_skipped(self, host, item=None):
        self.log(host, 'SKIPPED', '...')

    def runner_on_unreachable(self, host, res):
        self.log(host, 'UNREACHABLE', res)

    def runner_on_async_failed(self, host, res, jid):
        self.log(host, 'ASYNC_FAILED', res)

    def playbook_on_import_for_host(self, host, imported_file):
        self.log(host, 'IMPORTED', imported_file)

    def playbook_on_not_import_for_host(self, host, missing_file):
        self.log(host, 'NOTIMPORTED', missing_file)

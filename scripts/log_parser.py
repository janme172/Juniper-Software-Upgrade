
import paramiko
import os
import json
 
LOG_DIR = '/home/ansible/Logs/RouterSoftwareUpgrade/logs/'
REMOTE_LOG_DIR = '/home/ansible/Logs/RouterSoftwareUpgrade/remotelogs/'
RE_STRS = ['RE0', 'RE1']


def create_log_file(file_name, log_text):
    transport = paramiko.Transport(("62.243.147.45", 22))
    transport.connect(username = "ansible", password = "ansible")
    sftp = paramiko.SFTPClient.from_transport(transport)
    try:
        sftp.stat(REMOTE_LOG_DIR)  # test if remote_dir exists
    except IOError:
        sftp.mkdir(REMOTE_LOG_DIR)
        sftp.stat(REMOTE_LOG_DIR)
    f = sftp.open(os.path.join(REMOTE_LOG_DIR, file_name), "w")
    f.write(log_text)
    f.close()

def parse_task_json(task_name, task_status, task_timestamp, task_json_response):
    response = '\n'+'-'*200
    response += '\nTask Name: {0}\nTask Status: {1}\nTask Start Time: {2}\n'.format(task_name, task_status, task_timestamp)
    print task_name, task_status
    task_dict = ''
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
                        tests_passed += 1
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
#                  self._display.display("\t\tAnsible Output: Value of '{0}' not '{1}' at '{2}' with {3}".format(str(testlet['node_name']), str(testlet['testoperation']), str(testlet['xpath']), json.dumps(data)), color=C.COLOR_ERROR)
            overall_status = "Failed"
            if tests_failed == 0:
                overall_status = "Passed"
            response += "\nTests Summary:\n\tTotal Tests: {0}\n\tTests Passed: {1}\n\tTests Failed: {2}\n\tOverall Status: {3}".format(tests_total, tests_passed, tests_failed, overall_status)


    
    else:
        response += task_json_response
    response += '\n'+'-'*200
    return response        
        
for file_name in os.listdir(LOG_DIR): 
    file_path = os.path.join(LOG_DIR, file_name)
    if not os.path.isfile(file_path):
        continue

    with open(file_path, 'r') as logfile:
        task_name = None
        task_status = None
        task_timestamp = None
        task_json_response = ''
        log_text = ''
        for line in logfile:
            if '#####-----Task Start-----#####' in line:
                task_name = None
                task_status = None
                task_timestamp = None
                task_json_response = ''
                continue

            if '#####-----Task End-----#####' in line:
                if task_name and task_status:
                    log_text +=  '{}\n\n'.format(parse_task_json(task_name, task_status, task_timestamp ,task_json_response))
                #create_log_file(file_name, log_text)
                continue
        
            if 'Task Name' in line:
               try:
                   task_name = line.split(':', 1)[1].strip()
               except:
                   task_name = 'Could not retrieve task name from logs'
               continue
            elif 'Task Status' in line:
               try:
                   task_status = line.split(':', 1)[1].strip()
               except:
                   task_status = 'Could not retrieve task status from logs'
               continue
            elif 'Timestamp' in line:
               try:
                   task_timestamp = line.split(':', 1)[1].strip()
               except:
                   task_timestamp = 'Could not retrieve task timestamp from logs'
               continue
            else:
                if line.strip() != '':
                    task_json_response += line
                continue
    #print log_text
    create_log_file(file_name, log_text)



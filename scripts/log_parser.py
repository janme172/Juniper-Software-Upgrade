
with open('/home/ansible/Logs/RouterSoftwareUpgrade/logs/', 'r') as logfile:
    
    for line in logfile:
        task_name = None
        task_status = None
        task_timestamp = None
        if 'Task Name' in line:
           try:
               task_name = line.split(':')[1].strip()
           except:
               task_name = 'Could not retrieve task name from logs'
        elif 'Task Status' in line:
           try:
               task_status = line.split(':')[1].strip()
           except:
               task_status = 'Could not retrieve task status from logs'
        elif 'Task Timestamp' in line:
           try:
               task_status = line.split(':')[1].strip()
           except:
               task_status = 'Could not retrieve task timestamp from logs'
        


import paramiko

transport = paramiko.Transport(("62.243.147.45", 22))
transport.connect(username = "ansible", password = "ansible")
sftp = paramiko.SFTPClient.from_transport(transport)
f = sftp.open("/home/ansible/Logs/RouterSoftwareUpgrade/janme_test.log", "w")
f.write("hello,world")
f.close()

with open('/tmp/Touch_test_file.log', 'w') as f:
    f.write('Janmejay')


sftp.put('/tmp/Touch_test_file.log', '/home/ansible/Logs/RouterSoftwareUpgrade/')


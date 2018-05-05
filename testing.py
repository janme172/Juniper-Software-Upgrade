from pprint import pprint
from jnpr.junos import Device

'''
Create a new device object. This represents the SRX we are going to connect to.
The hostname/IP, username, and password are required.
'''
dev = Device(host='test2nqe30', user='ansible')

'''
Creates a Netconf session to the SRX
'''
dev.open()

'''
Prints out the output of the show version command
'''
#print dev.cli("request routing-engine login backup")
print dev.rpc.request_routing_engine_login(backup=True)

#print dev.cli("show chassis hardware")
print dev.rpc.get_chassis_inventory()

'''
Closes the netconf connection to the SRX
'''
dev.close()

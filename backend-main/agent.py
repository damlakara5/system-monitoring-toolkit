import os
import psutil
import time
import requests
import json
import subprocess
import socket
import threading
import platform

class enumerated_info:
    
    def __init__(self):
        if not self.is_root():
            raise Exception("Script must be run with root privileges.")
    
    def is_root(self):
        return os.geteuid() == 0
    
    def getHostName(self):
        self.hostName = socket.gethostname()
        return str(self.hostName)
    
    def cpu_usage(self):
        return psutil.cpu_percent(interval=1)
    
    def ram_usage(self):
        svmem = psutil.virtual_memory()
        return svmem.percent
        
        
    def kernel_version(self):
        kernel_version = platform.uname().release
        return kernel_version
    
    def storage_usage(self):
        storageUsage = psutil.disk_usage("/")
        #storage usage percent
        return str(storageUsage[3])
        
    def get_running_services(self):
        cmd = ['systemctl', '--no-pager', 'list-units', '--type=service', '--state=running', '--plain', '--no-legend']
        output = subprocess.check_output(cmd, universal_newlines=True)
        running_services = [line.split()[0] for line in output.splitlines()]
        services_string = ", ".join(running_services)
        return services_string
        
    def get_last_reboot_time(self):
        with open('/proc/uptime', 'r') as uptime_file:
            uptime_seconds = float(uptime_file.readline().split()[0])
            last_reboot_timestamp = time.time() - uptime_seconds
            last_reboot_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_reboot_timestamp))
            return last_reboot_time

    
    def execute_command(self, command):
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        return result.stdout.decode('utf-8'), result.stderr.decode('utf-8')
    
# Create an instance of the enumerated_info class
info = enumerated_info()


# Define the endpoint URLs
data_url = "http://localhost:5000/insertStatistics"
command_url = "http://localhost:5000/get/command/" +  info.getHostName()
print(command_url)

while True:
    # Get the latest commands
    command_output, command_error = "",""
    response = requests.get(command_url, headers={'Content-Type': 'application/json', 'x-access-key':'second_public_key'})
    if response.status_code == 200:
        commands = response.json()
        cmd = commands['command']
      #  for command in commands:
        command_output, command_error = info.execute_command(cmd)

    else:
        commands = []

    
    # Execute the commands
    #get kernel version
    kernel_version = info.kernel_version()
    
    #get running services 
    
    running_services = info.get_running_services()
    
    #get last reboot time
    
    last_reboot_time = info.get_last_reboot_time()
    
    #get hostname
    hostname = info.getHostName()
    print("Host name: {}%".format(hostname))
    
    # Get the CPU usage
    cpu_usage = info.cpu_usage()
    print("CPU usage: {}%".format(cpu_usage))
    
    # Get the RAM usage
    ram_usage = info.ram_usage()
   # print("RAM usage: {}% ({} GB)".format(ram_usage[0], ram_usage[1]))
    
    # Get the storage usage
    storage_usage = info.storage_usage()
    #for partition in storage_usage:
     #   print("Partition {} usage: {}% ({} GB)".format(partition[0], partition[1], partition[2]))
    
    # Create a dictionary with the collected data and command output
    data = {
        "host_name":hostname,
        "cpu_usage": cpu_usage,
        "ram_usage": ram_usage,
        "storage_usage": storage_usage,
        "kernel_version": kernel_version,
        "running_services": running_services,
        "last_reboot_time":last_reboot_time,
        "command_output": (command_output+command_error)
    }
    
    # Encode the data as JSON
    json_data = json.dumps(data)
    print(json_data)
    # Send the data to the endpoint
    response = requests.post(data_url, data=json_data, headers={'Content-Type': 'application/json', 'x-access-key':'second_public_key'})
    
    # Check if the request was successful
    if response.status_code == 200:
        print("Data sent successfully.")
    else:
        print("Error sending data: {}".format(response.text))
    
    # Pause for 30 seconds before collecting data again
    time.sleep(30)

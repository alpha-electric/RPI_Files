import csv
import struct
import time
import os
import socket
import argparse
import json
import logging
import sys
from datetime import datetime

from dalybms import DalyBMS
from dalybms import DalyBMSSinowealth

log_format = '%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s'
level = logging.WARNING
logging.basicConfig(level=level, format=log_format, datefmt='%H:%M:%S')
logger = logging.getLogger()

address = 4

#Magic number for request retries to be updated
bms = DalyBMS(request_retries=864000, address=address, logger=logger)
#bms.connect(device = "/dev/ttyUSB0")

result = False

def print_result(result):
    print(json.dumps(result, indent=2))
    
def getSerial():
    cpuserial = "0000000000000000"
    try:
        f = open('/proc/cpuinfo', 'r')
        for line in f:
            if line[0:6] == 'Serial':
                cpuserial = line[10:26]
        f.close()
    except:
        cpuserial = "ERROR000000000"
        
    return cpuserial

def checkInternetConnection():
    try:
        socket.create_connection(('google.com', 80))
        return True
    except OSError:
        return False
  
batteryID = getSerial()
remoteDirectory = '"gdrive:Alpha Electrics/3. Engineering/AE Engineering/Range Tests/data/' + batteryID +'"'

def dataSync():
    if checkInternetConnection() == True:
        print('Internet Connected, Data syncing now')
        os.system('rclone mkdir ' + remoteDirectory)
        os.system('rclone -v sync ./data/ ' + remoteDirectory)
    else:
        print('No Internet Connection, Data Is Not Synced')
            
while True:
    if os.path.isdir('./data') != True:
        os.mkdir('./data')

    #while current = 0: status: idle
    current = 0
    while current == 0:
        dataSync()
        bms.connect(device = "/dev/ttyUSB0")
        soc = bms.get_soc()
        current = soc["current"]
    
    thisdatetime = datetime.now()
    dataPath = './data/' + thisdatetime.strftime("%d-%b-%Y")
        
    if os.path.isdir(dataPath) != True:
        os.mkdir(dataPath)

    #Format CSV file name based on current time
    fileName = dataPath + '/' + thisdatetime.strftime("%d-%b-%Y") + '.csv'
    
    if os.path.isfile(fileName) != True:
        #Create new CSV file
        with open(fileName, mode = 'w') as log_file:
            log_writer = csv.writer(log_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            #log_writer.writerow(['datetime', 'current', 'voltage', 'charge', 't1', 't2', 't3', 'charge mosfet', 'discharge mosfet', 'v1', 'v2', 'v3', 'v4', 'v5', 'v6', 'v7', 'v8', 'v9', 'v10', 'v11', 'v12', 'v13'])
            log_writer.writerow(['datetime', 'current', 'voltage', 'charge', 't1', 'charge mosfet', 'discharge mosfet', 'v1', 'v2', 'v3', 'v4', 'v5', 'v6', 'v7', 'v8', 'v9', 'v10', 'v11', 'v12', 'v13'])
            log_file.close()
    
    logging = True
    icTime = 0
    
    #Initialise voltages of 13 cells on alpha cell, will change to array
    v1 = 0
    v2 = 0
    v3 = 0
    v4 = 0
    v5 = 0
    v6 = 0
    v7 = 0
    v8 = 0
    v9 = 0
    v10 = 0
    v11 = 0
    v12 = 0
    v13 = 0
    
    #Initialise mosfet values
    chargeMosfet = True
    dischargeMosfet = True
        
    while logging == True:
        #Read values from BMS
        bms.connect(device = "/dev/ttyUSB0")
        soc = bms.get_soc()
        
        bms.connect(device = "/dev/ttyUSB0")
        temperatures = bms.get_temperatures()
        
        current = soc["current"]
        voltage = soc["total_voltage"]
        charge = soc["soc_percent"]
        
        t1 = temperatures[1]
        #t2 = temperatures[2]
        #t3 = temperatures[3]
        
        bms.connect(device = "/dev/ttyUSB0")
        cellVoltages = bms.get_cell_voltages()
        
        bms.connect(device = "/dev/ttyUSB0")
        mosfetStatus = bms.get_mosfet_status()
        
        #Check for cellVoltage read request errors and update if none
        if cellVoltages != False:
            v1 = cellVoltages[1]
            v2 = cellVoltages[2]
            v3 = cellVoltages[3]
            v4 = cellVoltages[4]
            v5 = cellVoltages[5]
            v6 = cellVoltages[6]
            v7 = cellVoltages[7]
            v8 = cellVoltages[8]
            v9 = cellVoltages[9]
            v10 = cellVoltages[10]
            v11 = cellVoltages[11]
            v12 = cellVoltages[12]
            v13 = cellVoltages[13]
            
        if mosfetStatus != False:
            chargeMosfet = mosfetStatus["charging_mosfet"]
            dischargeMosfet = mosfetStatus["discharging_mosfet"]
        
        #print(current, voltage, charge, t1, t2, t3, chargeMosfet, dischargeMosfet)
        print(current, voltage, charge, t1, chargeMosfet, dischargeMosfet)
        print(v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13)
        
        #Write data to CSV fle
        with open(fileName, mode = 'a') as log_file:
            log_writer = csv.writer(log_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            #log_writer.writerow([datetime.now(), current, voltage, charge, t1, t2, t3, chargeMosfet, dischargeMosfet, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13])
            log_writer.writerow([datetime.now(), current, voltage, charge, t1, chargeMosfet, dischargeMosfet, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13])
            log_file.close()        
        
        if current >= 0:
            icTime += 1
        else:
            icTime = 0
        
        #Roughly 10 mins grace till logging cut, magic number '600' to be updated
        #Note: Consider using Time functions in Python Standard Library
        if icTime >= 300:
            print("Battery not in use")
            if current == 0:
                logging = False
            else:
                dataSync()
                time.sleep(30)
                

if not result:
    sys.exit(1)

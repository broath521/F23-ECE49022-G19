from time import sleep
from math import exp

def calc_charge(voltage):
    #print(voltage)
    if(voltage > 13.6):
        return 100
    elif(voltage <= 13.6 and voltage > 12.8):
         return (100*voltage - 1260)
    elif(voltage <= 12.8 and voltage > 12.0):
        return (12.5*voltage - 140)
    elif(voltage <= 12.0 and voltage > 10.0):
        return (5*voltage - 50)
    else:
        return 0

def average_volt(volt_arr, length_arr):
    sum_volt = 0
    for i in range(length_arr):
        sum_volt += volt_arr[i]
    bat_v_avg = sum_volt / length_arr

    return bat_v_avg

def format_datetime(datetime):
    #check for single digit values
    if(int(datetime[1]) < 10):
        month = "0" + str(int(datetime[1]))
    else:
        month = str(int(datetime[1]))
        
    if(int(datetime[2]) < 10):
        day = "0" + str(int(datetime[2]))
    else:
        day = str(int(datetime[2]))
        
    if(int(datetime[4]) < 10):
        hour = "0" + str(int(datetime[4]))
    else:
        hour = str(int(datetime[4]))
        
    if(int(datetime[5]) < 10):
        minute = "0" + str(int(datetime[5]))
    else:
        minute = str(int(datetime[5]))
        
    if(int(datetime[6]) < 10):
        second = "0" + str(int(datetime[6]))
    else:
        second = str(int(datetime[6]))
    
    
    sleep(.2)
    format_date = month + "/" + day + "/" + str(int(datetime[0]))
    format_time = hour + ":" + minute + ":" + second
    
    return format_date, format_time









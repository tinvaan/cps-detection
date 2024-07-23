"""Elevator fire alarm system attack :
 1 If moving =true is detected and moving is set to true from now on, the person in the elevator will be locked in the elevator; 
 2 Change the temperature, so that the fire alarm,DOS attack, elevator can not run normally; 
 3 Record the last target floor. If the elevator is still moving when the last target floor is reached,anomaly Behavior; 
 4 Repeatedly trigger the elevator button on the first floor, and set the stair level to 2 all the time. Expectation: The elevator has been stopped on the first floor, and people on the second floor cannot use it
"""

# 3 attack
import time
from pycomm.ab_comm.clx import Driver as ClxDriver

PLC_IPS = {
    'plc1': '192.168.1.151',
}

# label name
CURRENT_LEVEL_TAG = 'currentLevel'
MOVING_TAG = 'moving'
MOVING_TO_LEVEL1_TAG = 'movingToLevel1'
MOVING_TO_LEVEL2_TAG = 'movingToLevel2'

def read_plc_tag(plc, tag_name):
    try:
        return plc.read_tag(tag_name)[0]
    except Exception as e:
        print("Error reading tag:", e)
        return None

def detect_anomaly(plc_ip):
    plc = ClxDriver()
    if plc.open(plc_ip):
        last_target_level = None
        while True:
            try:
                current_level = read_plc_tag(plc, CURRENT_LEVEL_TAG)
                moving = read_plc_tag(plc, MOVING_TAG)
                moving_to_level1 = read_plc_tag(plc, MOVING_TO_LEVEL1_TAG)
                moving_to_level2 = read_plc_tag(plc, MOVING_TO_LEVEL2_TAG)
                
                if moving_to_level1:
                    target_level = 1
                elif moving_to_level2:
                    target_level = 2
                else:
                    target_level = None

                if last_target_level is not None and current_level == last_target_level and moving:
                    print("Anomaly detected: Elevator reached target level but is still moving!")

                last_target_level = target_level

                time.sleep(1)  # Set the read interval
            except Exception as e:
                print("Error:", e)
                break
        plc.close()
    else:
        print("Unable to open", plc_ip)

def main():
    detect_anomaly(PLC_IPS['plc1'])

if __name__ == '__main__':
    main()

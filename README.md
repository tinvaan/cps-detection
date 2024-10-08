# CPS Detection

The project simulates the functioning of an elevator system with the following components,

- two levels
- button up / down
- temperature sensor
- elevator load sensor

You can run the simulator to generate a dataset depicting various states of the system with some noise and the associated values of each component.

Our aim is to identify defects/anomalies in the simulated data.

## Setup

- Set `$PYTHONPATH` to the root directory of the project.

    ```shell
    > git clone https://github.com/tinvaan/cps-detection.git
    > cd cps-detection
    > export PYTHONPATH=$PYTHONPATH:$(pwd)
    ```

- Set project specific environment variables

    ```shell
    > export SIM_RUNS=20
    > export SIM_ROUNDS=20
    > export MAX_ALARM=10
    > export MIN_DETECTION=90
    ```

- Install project requirements

    ```shell
    > pip install -r requirements.txt
    ```

## Usage

Run the `simulation/cli.py` script to run the simulation and launch attacks.

```shell
$ python simulation/cli.py --help
usage: cli.py [-h] [-a ATTACK] [-s SENSOR]

options:
  -h, --help            show this help message and exit
  -a ATTACK, --attack ATTACK
                        target attack category
  -s SENSOR, --sensor SENSOR
                        target system sensor
```

Eg: attack the elevator's load sensor.

```shell
$ python simulation/cli.py --sensor 'weight' --attack 'ATTACK_MAX_WEIGHT'

Cusum(drift=0.3, threshold=4) - : 100%|####################################################################################################################################################################| 10/10 [00:00<00:00, 146.15it/s]
Cusum(drift=0.3, threshold=6) - : 100%|####################################################################################################################################################################| 10/10 [00:00<00:00, 148.60it/s]
Cusum(drift=0.3, threshold=8) - : 100%|####################################################################################################################################################################| 10/10 [00:00<00:00, 145.27it/s]
Cusum(drift=0.5, threshold=4) - : 100%|####################################################################################################################################################################| 10/10 [00:00<00:00, 145.98it/s]
Cusum(drift=0.5, threshold=6) - : 100%|####################################################################################################################################################################| 10/10 [00:00<00:00, 147.58it/s]
Cusum(drift=0.5, threshold=8) - : 100%|####################################################################################################################################################################| 10/10 [00:00<00:00, 144.58it/s]
Cusum(drift=0.7, threshold=4) - : 100%|####################################################################################################################################################################| 10/10 [00:00<00:00, 138.45it/s]
Cusum(drift=0.7, threshold=6) - : 100%|####################################################################################################################################################################| 10/10 [00:00<00:00, 139.47it/s]
Cusum(drift=0.7, threshold=8) - : 100%|####################################################################################################################################################################| 10/10 [00:00<00:00, 136.51it/s]
Cusum(drift=0.9, threshold=4) - : 100%|####################################################################################################################################################################| 10/10 [00:00<00:00, 135.89it/s]
Cusum(drift=0.9, threshold=6) - : 100%|####################################################################################################################################################################| 10/10 [00:00<00:00, 133.66it/s]
Cusum(drift=0.9, threshold=8) - : 100%|####################################################################################################################################################################| 10/10 [00:00<00:00, 134.13it/s]
    round           category  drift  threshold  samples  attacks             attack_points                                      change_points  detected  false_alarms  detection_effectiveness  false_alarm_rate
13      3  ATTACK_MAX_WEIGHT    0.3          6      500        1              [(158, 499)]                                         [492, 497]         1             1                    100.0              0.67
14      4  ATTACK_MAX_WEIGHT    0.3          6      500        2  [(371, 469), (481, 499)]                          [481, 487, 490, 494, 498]         2             3                    100.0              0.79
24      4  ATTACK_MAX_WEIGHT    0.3          8      500        1              [(371, 499)]  [398, 402, 405, 408, 412, 417, 421, 424, 427, ...         1            22                    100.0              7.86
44      4  ATTACK_MAX_WEIGHT    0.5          6      500        2  [(284, 332), (371, 499)]      [472, 476, 478, 481, 485, 490, 492, 495, 498]         2             7                    100.0              3.11

time elapsed: 0.8633344160043634 seconds
```

import random
import numpy as np

from dataclasses import dataclass, field

from . import plots
from .runtime import Config


@dataclass
class ElevatorState:
    """ Initialise some elevator data """
    ThresTemp: int = field(default_factory=lambda: random.randint(30, 99))
    ButtonLevel1: int = 0
    ButtonLevel2: int = 0
    currentLevel: int = Config.INITIAL_CURRENT_LEVEL
    moving: int = 0
    doorOpen: int = 0
    doorOpening: int = 0
    doorClosing: int = 0
    fireAlarm: int = 0
    weight: int = field(default_factory=lambda: random.randint(0, 1500))
    movingToLevel1: int = 0
    movingToLevel2: int = 0
    MAX_WEIGHT: int = 1200
    MAX_TEMP: int = 100


class Elevator:
    def generate_noise(self, lower=-5, upper=0.5):
        """ Generate noise normal deviation value """
        return np.random.uniform(lower, upper)

    def get_elevator_actuators(self, state):
        """ Get the elevator status """
        return {
            "moving": state.moving,
            "doorOpening": state.doorOpening,
            "movingToLevel2": state.movingToLevel2,
            "doorClosing": state.doorClosing,
            "movingToLevel1": state.movingToLevel1,
            "currentLevel1": state.currentLevel == 1,
            "doorOpen": state.doorOpen,
            "fireAlarm": state.fireAlarm,
        }

    def get_noisy_elevator_state(self, state):
        """ Get the elevator status under noise """
        noise = {
            key: self.generate_noise() for key in [
                "ThresTemp", "moving", "movingToLevel1", "movingToLevel2", "doorOpen", "weight"
            ]
        }
        fire_alarm = state.ThresTemp + noise["ThresTemp"] > state.MAX_TEMP
        overweight_alarm = state.weight + noise["weight"] > state.MAX_WEIGHT
        return {
            "fire_alarm": fire_alarm,
            "overweight_alarm": overweight_alarm,
            "ThresTemp": state.ThresTemp + noise["ThresTemp"],
            "moving": int(state.moving + noise["moving"] > 0.5) if not (fire_alarm or overweight_alarm) else 0,
            "movingToLevel1": int(state.movingToLevel1 + noise["movingToLevel1"] > 0.5),
            "movingToLevel2": int(state.movingToLevel2 + noise["movingToLevel2"] > 0.5),
            "doorOpen": int(state.doorOpen + noise["doorOpen"] > 0.5),
            "weight": state.weight + noise["weight"],
        }

    def update(self, state: ElevatorState, noisy_state: ElevatorState):
        is_value_changed = False

        if state.weight > 0:
            state.fireAlarm = 1 if state.weight > state.MAX_WEIGHT else 0

        if state.doorOpen:
            state.doorOpening = 0
            state.doorClosing = 0

        if state.doorOpening:
            state.doorOpen = 0

        if state.doorClosing:
            state.doorOpen = 0

        if state.doorOpening and not is_value_changed:
            is_value_changed = True
            state.doorOpening = 0
            state.doorOpen = 1

        if state.doorClosing and not is_value_changed:
            is_value_changed = True
            state.doorClosing = 0
            state.doorOpen = 0
            if state.movingToLevel1 or state.movingToLevel2:
                state.moving = 1

        if state.doorClosing and state.fireAlarm:
            state.doorClosing = 0

        if not state.fireAlarm and state.doorOpen and not is_value_changed:
            if state.weight > state.MAX_WEIGHT:
                state.doorOpen = 1
            else:
                is_value_changed = True
                state.doorOpen = 0
                state.doorClosing = 1

        if state.moving and not is_value_changed:
            is_value_changed = True
            state.moving = 0
            state.doorOpening = 1
            if state.movingToLevel1:
                state.currentLevel = 1
                state.movingToLevel1 = 0
            else:
                state.currentLevel = 2
                state.movingToLevel2 = 0

        if state.moving and (state.fireAlarm or noisy_state["overweight_alarm"]):
            state.moving = 0

        if not state.moving:
            if state.fireAlarm:
                if not state.doorOpening and not state.doorOpen:
                    state.doorOpening = 1
                    state.doorClosing = 0
            elif not state.doorOpen and not state.doorOpening and not is_value_changed:
                is_value_changed = True
                if state.ButtonLevel2:
                    if state.currentLevel != 2:
                        state.movingToLevel2 = 1
                        state.moving = 1
                    else:
                        state.movingToLevel1 = 1
                        state.doorOpening = 1
                elif state.ButtonLevel1:
                    if state.currentLevel != 1:
                        state.movingToLevel1 = 1
                        state.moving = 1
                    else:
                        state.movingToLevel2 = 1
                        state.doorOpening = 1

        state.ButtonLevel1 = 0
        state.ButtonLevel2 = 0

    def simulate(self, state: ElevatorState, cycles: int=10,
                 attack_type: str="NONE", attack_start: int=1, attack_end: int=100
    ):
        MAX_TEMP = []
        MAX_WEIGHT = []

        BIAS_VALUE:int = 30
        BIAS_VALUE:int = random.choice(Config.BIAS_SELECTION)

        actuators_status = []
        sensor_measurements = []
        estimated_measurements = []

        for i in range(cycles):
            if not state.moving and random.randint(1, 10) == 1:
                if random.randint(1, 2) == 1:
                    state.ButtonLevel1 = 1
                else:
                    state.ButtonLevel2 = 1

            if attack_type == "ATTACK_MAX_TEMP":
                state.MAX_TEMP = 20
            elif attack_type == "ATTACK_MAX_WEIGHT":
                state.MAX_WEIGHT = 10
            elif attack_type == "BUTTON_ATTACK":
                if state.ButtonLevel1:
                    if state.currentLevel == 1:
                        state.movingToLevel2 = 1
                        state.moving = 1
                    else:
                        state.movingToLevel1 = 0
                        state.moving = 0
                elif state.ButtonLevel2:
                    if state.currentLevel == 2:
                        state.movingToLevel1 = 1
                        state.moving = 1
                    else:
                        state.movingToLevel2 = 0
                        state.moving = 0

            noisy_state = self.get_noisy_elevator_state(state)

            # Consider doing it here
            if attack_type == "BIAS" and attack_start <= i < attack_end:
                noisy_state["ThresTemp"] = noisy_state["ThresTemp"] + BIAS_VALUE

            if attack_type == "SURGE" and attack_start <= i < attack_end:
                noisy_state["ThresTemp"] = 120

            if attack_type == "RANDOM" and attack_start <= i < attack_end:
                BIAS_VALUE:int = random.randint(-30,30)
                noisy_state["ThresTemp"] = noisy_state["ThresTemp"] + BIAS_VALUE

            estimated_measurements.append(state.ThresTemp)
            sensor_measurements.append(noisy_state["ThresTemp"])
            actuators_status.append({
                "fire_alarm": noisy_state["fire_alarm"],
                "overweight_alarm": noisy_state["overweight_alarm"],
                "moving": noisy_state["moving"],
                "doorOpen": state.doorOpen,
                "movingToLevel1": noisy_state["movingToLevel1"],
                "movingToLevel2": noisy_state["movingToLevel2"],
                "temp": noisy_state["ThresTemp"],
                "MAX_TEMP": state.MAX_TEMP,
                "weight": noisy_state["weight"],
                "MAX_WEIGHT": state.MAX_WEIGHT,
                "currentLevel": state.currentLevel,
                "ButtonLevel1": state.ButtonLevel1,
                "ButtonLevel2": state.ButtonLevel2,
            })

            MAX_TEMP.append(state.MAX_TEMP)
            MAX_WEIGHT.append(state.MAX_WEIGHT)
            self.update(state, noisy_state)

        return MAX_TEMP, MAX_WEIGHT, estimated_measurements, sensor_measurements, actuators_status

    def run(self, timer, attack_type="NONE", attack_start:int =1 , attack_end:int = 100):
        """ The function that actually performs the attack """
        return self.simulate(ElevatorState(), timer, attack_type, attack_start, attack_end)

    def attack(self):
        """
        Determine the simulation parameters mainly to determine
        whether there is an intermediate function of the attack
        """
        attack_type = random.choice(Config.ATTACK_TYPES)
        attack_start = random.randint(0, 300)
        attack_duration = random.randint(1, 100)
        attack_end = attack_start + attack_duration

        if attack_type != "NONE":
            print(f"Attack type: {attack_type}")
            print(f"Attack started at t: {attack_start}")
            print(f"Attack ended at t: {attack_end}")
        else:
            print("Normal operation. No attack simulated.")

        (
            MAX_TEMP,
            MAX_WEIGHT,
            estimated_measurements,
            sensor_measurements,
            actuators_status
        ) = self.run(Config.SIMULATION_TIME, attack_type, attack_start, attack_end)

        # Ensure actuators_status is assigned before it is used
        detection_status = ["benign"] * len(actuators_status)
        for i in range(len(actuators_status)):
            if actuators_status[i]["MAX_TEMP"] != 100 or actuators_status[i]["MAX_WEIGHT"] != 1200:
                detection_status[i] = "attack"

        plots.draw(MAX_TEMP, MAX_WEIGHT, sensor_measurements, actuators_status,
                   title=(attack_type, False), detection_status=detection_status)
        return sensor_measurements, actuators_status, attack_type, detection_status

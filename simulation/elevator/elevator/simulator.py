
import random
import numpy as np

from typing import List
from dataclasses import asdict, dataclass, field

from . import plots
from .runtime import Config


@dataclass
class ElevatorState:
    """ Initialise some elevator data """
    MAX_TEMP: int = 100
    MAX_WEIGHT: int = 1200
    moving: int = 0
    doorOpen: int = 0
    fireAlarm: int = 0
    doorOpening: int = 0
    doorClosing: int = 0
    ButtonLevel1: int = 0
    ButtonLevel2: int = 0
    movingToLevel1: int = 0
    movingToLevel2: int = 0
    currentLevel: int = Config.INITIAL_CURRENT_LEVEL
    weight: int = field(default_factory=lambda: random.randint(0, 1500))
    ThresTemp: int = field(default_factory=lambda: random.randint(30, 99))

    def __dict__(self):
        return asdict(self)


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

    def update(self, state: ElevatorState, noise: ElevatorState):
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

        if state.moving and (state.fireAlarm or noise["overweight_alarm"]):
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

    def launch_attack(self, attack, cycle, state, noise):
        launched = True
        attack_end = attack.get('attack_end')
        attack_type = attack.get('attack_type')
        attack_start = attack.get('attack_start')

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

        elif attack_type == "SURGE" and cycle in range(attack_start, attack_end):
            noise["ThresTemp"] = 120

        elif attack_type == "BIAS" and cycle in range(attack_start, attack_end):
            bias = random.choice(Config.BIAS_SELECTION)
            noise["ThresTemp"] = noise["ThresTemp"] + bias

        elif attack_type == "RANDOM" and cycle in range(attack_start, attack_end):
            bias = random.randint(-30,30)
            noise["ThresTemp"] = noise["ThresTemp"] + bias

        else:
            launched = False

        return launched, state, noise

    def simulate(
        self,
        state: ElevatorState,
        cycles: int=10,
        attack_type: str="NONE",
        attack_start: int=1,
        attack_end: int=100
    ):
        num_attacks = 0
        temps: List[int] = []               # Temperature values under normal operation
        weights: List[int] = []             # Temperature values under noise
        readings: List[dict] = []           # state of the system for the current simulation cycle

        for cycle in range(cycles):
            noise = self.get_noisy_elevator_state(state)

            if not state.moving and random.randint(1, 10) == 1:
                if random.randint(1, 2) == 1:
                    state.ButtonLevel1 = 1
                else:
                    state.ButtonLevel2 = 1

            payload = {'attack_type': attack_type, 'attack_start': attack_start, 'attack_end': attack_end}
            attacked, state, noise = self.launch_attack(payload, cycle, state, noise)
            num_attacks += int(attacked)

            temps.append(state.ThresTemp)
            weights.append(state.weight)
            readings.append({
                "MAX_TEMP": state.MAX_TEMP,
                "MAX_WEIGHT": state.MAX_WEIGHT,
                "doorOpen": state.doorOpen,
                "currentLevel": state.currentLevel,
                "ButtonLevel1": state.ButtonLevel1,
                "ButtonLevel2": state.ButtonLevel2,
                "moving": noise["moving"],
                "weight": noise["weight"],
                "temp": noise["ThresTemp"],
                "fire_alarm": noise["fire_alarm"],
                "movingToLevel1": noise["movingToLevel1"],
                "movingToLevel2": noise["movingToLevel2"],
                "overweight_alarm": noise["overweight_alarm"],
            })
            self.update(state, noise)

        return num_attacks, temps, weights, readings

    def run(self, cycles, attack_type="NONE", attack_start:int =1 , attack_end:int = 100):
        """ The function that actually performs the attack """
        return self.simulate(ElevatorState(), cycles, attack_type, attack_start, attack_end)

    def attack(self):
        """
        Determine the simulation parameters mainly to determine
        whether there is an intermediate function of the attack
        """
        category = random.choice(Config.ATTACK_TYPES)
        start = random.randint(0, 300)
        duration = random.randint(1, 100)
        end = start + duration

        num_attacks, temps, weights, readings = self.run(Config.SIMULATION_TIME, category, start, end)

        # TODO: Clear this out completely
        # detection_status = ["benign"] * len(readings)
        # for i in range(len(readings)):
        #     if readings[i]["MAX_TEMP"] != 100 or readings[i]["MAX_WEIGHT"] != 1200:
        #         detection_status[i] = "attack"

        # plots.draw(MAX_TEMP, MAX_WEIGHT, sensor_measurements, snapshots,
        #            title=(category, False), detection_status=detection_status)

        # TODO: Clear out the `detection_status`
        return num_attacks, category, temps, weights, readings # , detection_status

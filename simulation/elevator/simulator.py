
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
        bias, button, surge, rand, max_temp, max_weight = False, False, False, False, False, False

        attack_window = range(attack.get('attack_start'), attack.get('attack_end'))
        if cycle not in attack_window:
            return state, noise, False, 0

        attack_type = attack.get('attack_type')
        attack_types = attack_type.split(',')
        if '' in attack_types: attack_types.remove('')

        if "SURGE" in attack_types:
            surge = True
            noise["ThresTemp"] = 120

        if "BIAS" in attack_types:
            bias = True
            noise["ThresTemp"] += random.choice(Config.BIAS_SELECTION)

        if "RANDOM" in attack_types:
            rand = True
            noise["ThresTemp"] += random.randint(-30, 30)

        if "ATTACK_MAX_TEMP" in attack_types:
            max_temp = True
            state.MAX_TEMP = 20

        if "ATTACK_MAX_WEIGHT" in attack_types:
            max_weight = True
            state.MAX_WEIGHT = 10

        if "BUTTON_ATTACK" in attack_types:
            if state.ButtonLevel1:
                button = True
                if state.currentLevel == 1:
                    state.movingToLevel2 = 1
                    state.moving = 1
                else:
                    state.movingToLevel1 = 0
                    state.moving = 0

            elif state.ButtonLevel2:
                button = True
                if state.currentLevel == 2:
                    state.movingToLevel1 = 1
                    state.moving = 1
                else:
                    state.movingToLevel2 = 0
                    state.moving = 0

        attacks = [bias, button, surge, rand, max_temp, max_weight]
        return state, noise, any(attacks), attacks.count(True)

    def simulate(
        self,
        state: ElevatorState,
        rounds: int,
        attack_type: str="NONE",
        attack_start: int=1,
        attack_end: int=Config.SIMULATION_ROUNDS
    ):
        temps: List[int] = []               # Temperature values under normal operation
        weights: List[int] = []             # Temperature values under noise
        simulations: List[dict] = []        # state of the system for the current simulation cycle

        for cycle in range(rounds):
            noise = self.get_noisy_elevator_state(state)

            if not state.moving and random.randint(1, 10) == 1:
                if random.randint(1, 2) == 1:
                    state.ButtonLevel1 = 1
                else:
                    state.ButtonLevel2 = 1

            payload = {'attack_type': attack_type, 'attack_start': attack_start, 'attack_end': attack_end}
            state, noise, attacked, count = self.launch_attack(payload, cycle, state, noise)

            temps.append(state.ThresTemp)
            weights.append(state.weight)
            simulations.append({
                "cycle": cycle,
                "attack": {'launched': attacked, 'count': count},
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

        return temps, weights, simulations

    def attack(self, category):
        """
        Determine the simulation parameters mainly to determine
        whether there is an intermediate function of the attack
        """
        start = random.randint(0, Config.SIMULATION_ROUNDS)
        duration = random.randint(1, Config.SIMULATION_ROUNDS)
        temps, weights, simulations = self.simulate(ElevatorState(), Config.SIMULATION_ROUNDS,
                                                    category, start, start + duration)
        return category, temps, weights, simulations

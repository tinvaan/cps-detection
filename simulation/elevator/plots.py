
import os
import matplotlib.pyplot as plt

from .runtime import Config


def draw(MAX_TEMP, MAX_WEIGHT, sensor_measurements, actuators_status, title=("NONE", False), detection_status=None):
    if Config.SHOW_PLOTS or Config.SAVE_PLOTS:
        fig, axs = plt.subplots(2, figsize=(12, 12))
        axs[0].set_title(f"Raw sensor measurements (Attack type: {title[0]})")

        if title[0] == "ATTACK_MAX_TEMP":
            axs[0].plot(MAX_TEMP, linestyle="-", linewidth=5, label="MAX_TEMP")
            axs[0].plot(sensor_measurements, linestyle="-", linewidth=0.8, label="Temp")
        elif title[0] == "ATTACK_MAX_WEIGHT":
            weights = [status['weight'] for status in actuators_status]
            max_weights = [status['MAX_WEIGHT'] for status in actuators_status]
            axs[0].plot(MAX_WEIGHT, linestyle="-", linewidth=5, label="MAX_WEIGHT")
            axs[0].plot(weights, linestyle="-", linewidth=0.8, label="Weight")
        elif title[0] == "BUTTON_ATTACK":
            button_level1 = [status['ButtonLevel1'] for status in actuators_status]
            button_level2 = [status['ButtonLevel2'] for status in actuators_status]
            current_level1 = [1 if status['currentLevel'] == 1 else 0 for status in actuators_status]
            axs[0].plot(current_level1, linestyle="-", linewidth=1, label="CurrentLevel1")
            axs[0].plot(button_level1, linestyle="-", linewidth=0.8, label="ButtonLevel1")
            axs[0].plot(button_level2, linestyle="-", linewidth=0.8, label="ButtonLevel2")
        elif title[0]=="BIAS":
            axs[0].plot(MAX_TEMP, linestyle="-", linewidth=5, label="thresholds")
            axs[0].plot(sensor_measurements, linestyle="-", linewidth=0.8, label="actual")
        elif title[0]=="SURGE":
            axs[0].plot(MAX_TEMP, linestyle="-", linewidth=5, label="thresholds")
            axs[0].plot(sensor_measurements, linestyle="-", linewidth=0.8, label="actual")
        elif title[0]=="RANDOM":
            axs[0].plot(MAX_TEMP, linestyle="-", linewidth=5, label="thresholds")
            axs[0].plot(sensor_measurements, linestyle="-", linewidth=0.8, label="actual")
        else:
            axs[0].plot(MAX_TEMP, linestyle="-", linewidth=5, label="thresholds")
            axs[0].plot(sensor_measurements, linestyle="-", linewidth=0.8, label="actual")

        if detection_status:
            attack_indices = [i for i, status in enumerate(detection_status) if status == "attack"]
            axs[0].scatter(attack_indices, [sensor_measurements[i] for i in attack_indices], color='red', label='Attack detected', zorder=5)

        axs[0].legend()

        fire_alarm_status = [status["fire_alarm"] for status in actuators_status]
        moving_status = [status["moving"] for status in actuators_status]
        overweight_alarm = [status["overweight_alarm"] for status in actuators_status]
        axs[1].plot(fire_alarm_status, linestyle="-", linewidth=5, label="fire_alarm")
        axs[1].plot(overweight_alarm, linestyle="-", linewidth=5, label="overweight_alarm")
        axs[1].plot(moving_status, linestyle="-", linewidth=0.8, label="moving")
        axs[1].set_title("Fire Alarm, Overweight Alarm, and Moving Status")
        axs[1].legend()

        plt.tight_layout()
        if Config.SHOW_PLOTS:
            plt.show(block=False)

        if Config.SAVE_PLOTS:
            filepath = f"runs/ATTACK_TYPE_{title[0]}"
            num = len([f for f in os.listdir(filepath) if os.path.isfile(os.path.join(filepath, f))]) + 1
            fig.savefig(f"{filepath}/{num}.png")
            plt.close()

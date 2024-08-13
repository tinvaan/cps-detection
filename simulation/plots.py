
import os
import matplotlib.pyplot as plt

from simulation.elevator.runtime import Config


def draw(frame, dst=None):
    runs = frame.readings.tolist().pop()
    category = frame.category.unique().tolist().pop()
    temps, maxTemp = [status['temp'] for status in runs], [status['MAX_TEMP'] for status in runs]
    weights, maxWeight = [status['weight'] for status in runs], [status['MAX_WEIGHT'] for status in runs]

    fig, axs = plt.subplots(2, figsize=(12, 12))
    axs[0].set_title(f"Raw sensor measurements (Attack type: {category})")

    detections = frame.change_points.tolist().pop()
    d = plt.axvspan(min(detections), max(detections), alpha=0.25, color='yellow', label=f'Detect')
    plt.annotate(
        xy=d.get_center(),
        text=f'''
        Detection Effectiveness = {frame.detection_effectiveness.tolist().pop()}%
        False Alarm Rate = {frame.false_alarm_rate.tolist().pop()}%
        '''
    )

    for idx, attacks in enumerate(frame.attack_points.tolist().pop()):
        if idx > 0:
            plt.axvspan(min(attacks), max(attacks), alpha=0.1, color='red')
        else:
            plt.axvspan(min(attacks), max(attacks), alpha=0.1, color='red', label=f'Attack')

    if category == "BUTTON_ATTACK":
        axs[0].plot([1 if status['currentLevel'] == 1 else 0 for status in runs],
                    linestyle="-", linewidth=1, label="CurrentLevel1")
        axs[0].plot([status['ButtonLevel1'] for status in runs],
                    linestyle="-", linewidth=0.8, label="ButtonLevel1")
        axs[0].plot([status['ButtonLevel2'] for status in runs],
                    linestyle="-", linewidth=0.8, label="ButtonLevel2")

    elif category == "ATTACK_MAX_TEMP":
        axs[0].plot(maxTemp, linestyle="-", linewidth=5, label="MAX_TEMP")
        axs[0].plot(temps, linestyle="-", linewidth=0.8, label="Temperature")

    elif category == "ATTACK_MAX_WEIGHT":
        axs[0].set_title(f"Elevator Load (Attack type: {category})")
        axs[0].plot(maxWeight, linestyle="-", linewidth=5, label="MAX_WEIGHT")
        axs[0].plot(weights, linestyle="-", linewidth=0.8, label="Elevator load")

    else:   # BIAS, SURGE, RANDOM, etc...
        axs[0].plot(maxTemp, linestyle="-", linewidth=5, label="MAX_TEMP")
        axs[0].plot(maxWeight, linestyle="-", linewidth=5, label="MAX_WEIGHT")

        axs[0].plot(temps, linestyle="-", linewidth=0.8, label="Temperature")
        axs[0].plot(weights, linestyle="-", linewidth=0.8, label="Elevator load")
    axs[0].legend()

    axs[1].plot([status["moving"] for status in runs], linestyle="-", linewidth=0.8, label="Moving")
    axs[1].plot([status["fire_alarm"] for status in runs], linestyle="-", linewidth=5, label="Fire Alarm")
    axs[1].plot([status["overweight_alarm"] for status in runs], linestyle="-", linewidth=5, label="Load Alarm")
    axs[1].set_title("Fire alarm, Load alarm, Elevator motion")
    axs[1].legend()

    plt.tight_layout()
    if Config.SHOW_PLOTS:
        plt.show(block=True)

    if dst and Config.SAVE_PLOTS:
        num = len([f for f in os.listdir(dst) if os.path.isfile(os.path.join(dst, f))]) + 1
        fig.savefig(f"{dst}/{num}.png")
        plt.close()

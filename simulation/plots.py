
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
    # axs[0].plot(frame.change_points.tolist().pop(), linestyle="-", linewidth=2.0, label="Change Points")
    # axs[0].plot(frame.attack_points.tolist().pop(), linestyle="-", linewidth=2.0, label="Attack Points")

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

    # axs[1].plot(frame.change_points.tolist().pop(), linestyle="-", linewidth=2.0, label="Change Points")
    # axs[1].plot(frame.attack_points.tolist().pop(), linestyle="-", linewidth=2.0, label="Attack Points")
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

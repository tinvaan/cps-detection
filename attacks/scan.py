
import os
import csv
import time

from datetime import datetime
from pycomm.ab_comm.clx import Driver as ClxDriver


class TemperatureScanner:
    TEMP_TAG = 'ThresTemp'
    IP_ADDR = '192.168.1.151'
    INTERVAL = 1    # seconds

    def __init__(self) -> None:
        cwd = os.path.dirname(__file__)
        runs = os.path.join(cwd, "./artifacts/runs")
        nextRun = os.path.join(
            runs, f"./{max([int(r) for r in os.walk(runs)[1]]) + 1}")
        os.makedirs(nextRun, exist_ok=True)
        self.outfile = os.path.join(nextRun, "./temp.csv")
        open(self.outfile, 'w')

    def scan(self):
        self.plc = ClxDriver()
        if self.plc.open(self.IP_ADDR):
            print("Monitoring temperature sensor ...")
            with open(self.outfile, 'a', newline='\n') as csvfile:
                tv = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                for _ in range(1000):
                    temp = self.plc.read_tag(self.TEMP_TAG)
                    if temp:
                        now = [datetime.now().ctime(), temp[0]]
                        print("\t", now)
                        tv.writerow(now)
                    time.sleep(self.INTERVAL)
        raise ConnectionError("Unable to connect to PLC: <%s>" % self.IP_ADDR)

    def __del__(self):
        self.plc.close()


if __name__ == '__main__':
    ts = TemperatureScanner()
    ts.scan()

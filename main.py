import wmi
import psutil
import subprocess
import time
import os
from dotenv import load_dotenv
from datetime import datetime
import csv

load_dotenv()

def get_sensors(hwmon, sensor_type, sensor_names):
	sensors = hwmon.Sensor(SensorType=sensor_type)
	dt = datetime.now().strftime('%Y%m%d_%H%M%S')
	filtered_sensors = [sensor for sensor in sensors if sensor.ole_object.Name in sensor_names]
	formatted_sensors = [{'Name': sensor.ole_object.Name, 'Value': sensor.ole_object.Value} for sensor in filtered_sensors]
	return formatted_sensors, dt


def is_process_running(process_name):
	for proc in psutil.process_iter(['pid', 'name']):
		if process_name.lower() in proc.info['name'].lower():
			return True
	return False


def start_process(process_path):
	return subprocess.Popen(['start', process_path], shell=True)

def start_process_and_wait(process_name,process_path):
	timeout = 30
	start_time = time.time()
	new_process =	start_process(process_path)
	while time.time() - start_time < timeout:
		if is_process_running(process_name):
			time.sleep(2.5) # wait for process to fully start before doing anything
			break
		print(f"Attempting to start process: {process_name}")
		time.sleep(1)
	else:
		print("Timed out waiting for process to start")
		if new_process is not None: new_process.terminate()

def write_to_csv(hwmon):
	interval = int(os.getenv('LOG_INTERVAL'))
	file_name = f'loads_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
	fieldnames = ['Timestamp', 'CPU Load', 'GPU Load', 'RAM Load']

	while True:
		# Fetch the latest data
		raw_data = get_sensors(hwmon, "Load", ['CPU Total', 'GPU Core', 'Memory'])
		data = {'Timestamp': raw_data[1], 'CPU Load': raw_data[0][0]['Value'], 'GPU Load': raw_data[0][1]['Value'], 'RAM Load': raw_data[0][2]['Value']}


		with open(f'out\\{file_name}', 'a', newline='') as csvfile:

			# Create a writer object
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

			# Write the header if the file is new
			if csvfile.tell() == 0:
				writer.writeheader()

			# Write the data to the CSV file
			writer.writerow(data)
			print(f"Written to CSV: {data}")

			# Sleep for the specified interval
		time.sleep(interval)

def main():
	process_name = 'LibreHardwareMonitor.exe'
	process_path = os.getenv('HWM_PATH')

	if not is_process_running(process_name):
		start_process_and_wait(process_name,process_path)
	
	hwmon = wmi.WMI(namespace=r"root\LibreHardwareMonitor")
	write_to_csv(hwmon)

if __name__ == '__main__':
	main()
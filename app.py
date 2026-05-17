import subprocess
import csv
import os
from datetime import datetime
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

CSV_FILE = 	'system_history.csv'

if not os.path.exists(CSV_FILE):
	with open(CSV_FILE, mode='w', newline='') as file:
		writer = csv.writer(file)
		writer.writerow(['Timestamp', 'Temperature', 'CPU_Usage'])

def get_cpu_temperature():
	try:
		raw_temp = subprocess.check_output(['vcgencmd', 'measure_temp']).decode('utf-8')
		temp_value = float(raw_temp.replace("temp=", "").replace("'C\n", ""))
		return temp_value
	except Exception as e:
		print(f"Eroare la rularea vcgencmd: {e}")
		return 0.0

def get_top_processes():
	try:
		raw_top = subprocess.check_output(['top', '-b', '-n', '1']).decode('utf-8')
		lines = raw_top.split('\n')
		
		cpu_usage = 0.0
		for line in lines:
			if "%Cpu(s)" in line:
				parts = line.split(',')
				us = float(parts[0].split(':')[1].strip().split()[0].replace('%', ''))
				sy = float(parts[1].strip().split()[0].replace('%', ''))
				cpu_usage = round(us + sy, 1)
				break;
		
		processes = []
		start_parsing = False
		
		for line in lines:
			if "PID" in line and "COMMAND" in line:
				start_parsing = True
				continue
		
			if start_parsing and line.strip():
				parts = line.split()
				if len(parts) >= 12:
					proc_info = {
						'pid': parts[0],
						'user': parts[1],
						'cpu': parts[8],
						'mem': parts[9],
						'command': " ".join(parts[11:])
						}
				processes.append(proc_info)
			
				if len(processes) == 5:
					break
		
		return cpu_usage, processes
	except Exception as e:
		print(f"Eroare la parsarea top: {e}")
		return 0.0, []
		
def save_log_to_csv(temp, cpu):
	now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	with open('system_history.csv', mode='a', newline='') as file:
		writer = csv.writer(file)
		writer.writerow([now, temp, cpu])
		

@app.route('/')
def index():
	return render_template('index.html')
	
@app.route('/api/stats')
def api_stats():
	temp = get_cpu_temperature()
	cpu, processes = get_top_processes()	
	save_log_to_csv(temp, cpu)
	
	return jsonify({
		'temperature': temp,
		'cpu_usage': cpu,
		'processes': processes
		})
		
if 	__name__ == '__main__':
	app.run(host='0.0.0.0', port=5000, debug=True)

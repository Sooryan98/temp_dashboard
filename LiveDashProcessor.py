
import os
import time
import threading
from threading import Event 
import re
from collections import defaultdict
from datetime import datetime

from collections import Counter

sim_speed=20
robot_count=10
cart_count=30
start_time=0
end_time=0
ptrack=0
inbound_count = 15
outbound_count = 42
simulation_start_time=0
simulation_started=False
current_elapsed_time=-0
robot_destro_data = defaultdict(lambda: defaultdict(dict))
progress_track={"0.0":0}
progress=defaultdict(int)
task_id_tracker=[]
uph_tracker={}
log_data = {"total_cases": 0}
robot_fms_data = {f"Robot {i+1}": 0 for i in range(15)}
robot_total_cases={f"Robot {i+1}" : 0 for i in range(15)}
robot_dwell={f"Robot {i+1}" : 0 for i in range(15)}
cases_per_hour = defaultdict(lambda: defaultdict(int))
log_time_format = "%Y-%m-%d %H:%M:%S,%f"
robot_destro_data = defaultdict(lambda: defaultdict(dict))
robot_total_cases = defaultdict(int)
cases_per_hour = defaultdict(lambda: defaultdict(int))
trips_robot={}
cart_empty_idle={}
cart_full_idle={}
indoor_idle={}
outdoor_idle={}
flag=False
lock = threading.Lock()
flag_event= Event()
log_time_format = "%Y-%m-%d %H:%M:%S,%f"


def update_elapsed_time():
    global current_elapsed_time,simulation_start_time,simulation_started
    while True:
        if simulation_started and flag_event.is_set():
            current_elapsed_time=time.time()-simulation_start_time
        time.sleep(0.5)
def read_fms_log(fms_log):
    if not os.path.exists(fms_log):
        open(fms_log, 'w').close()


    with open(fms_log, "r") as file:
        file.seek(0, 2)  # Seek to end

        while True:
            line = file.readline()

            if not line:
                time.sleep(0.2)
                continue

            line = re.sub(r'\x1b\[[0-9;]*m', '', line)  # Remove ANSI

            with lock:
                # print(f"FROM LOG READER{progress}")
                if "CODE F01" in line :
                    pattern = re.compile(r"CODE F01 at (\d+\.\d+) number of cases finished is (\d+)")
                    match = pattern.search(line)
                    # print(match)
                    if match:
                        hour, cases = match.groups()
                        # print(f"L1{cases} --- type is {type(cases)}")
                        cases_until_now= sum(progress_track.values())
                        progress_track[hour]=int(cases)   
                        # print(f"L2{progress_track}")
                        progress_track[hour]=progress_track[hour]-cases_until_now
                        # print(f"L3--{progress_track}")
                        progress[hour]=progress_track[hour]
                        # print(f"L4{progress}")
                        
                elif "CODE F02" in line:
                    pattern =re.compile(
                            r"CODE F02 at (\d+\.\d+) UPH is (\d+)"

)
                    match=pattern.search(line)
                    if match:
                        hour,uph=match.groups()
                        uph_tracker[hour]=uph


                elif "CODE 000" in line : 
                    global simulation_start_time,simulation_started
                    if not simulation_started:
                        simulation_start_time=time.time()
                        simulation_started=True 


                    # print("FMS CAN START NOW")
                    flag_event.set()
                elif "has dwelled" in line:
                    pattern = re.compile(r"Robot robot_(\d+) has dwelled for ([\d.]+) sec")
                    match=pattern.search(line)
                    if match:
                        robot_id,dwell_time=match.groups()
                        dwell_time=round(float(dwell_time),2)/60
                        robot_key = f"Robot {int(robot_id)+1}"
                        if dwell_time!=0:
                            robot_dwell[robot_key]=dwell_time
                else:
                    pattern = re.compile(r"Robot robot_(\d+)\s+has travelled\s+([\d\.]+)\s+m")
                    match = pattern.search(line)
                    if match:
                        robot_id, dist = match.groups()
                        if int(robot_id)<25:

                            robot_key = f"Robot {int(robot_id)+1}"
                            robot_fms_data[robot_key] = float(dist)
              
            
                    


def read_destro_log(destro_log):
    if not os.path.exists(destro_log):
        open(destro_log, 'w').close()

    with open(destro_log, "r") as file:
        file.seek(0, 2)  # Seek to end

        while True:
            line = file.readline()

            if not line:
                time.sleep(0.2)
                continue

            line = re.sub(r'\x1b\[[0-9;]*m', '', line)  # Remove ANSI

            with lock:
           
                if "CODE 201" in line:
                    timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+)', line)
                    if timestamp_match:
                        log_time_str = timestamp_match.group(1)
                        log_time = datetime.strptime(log_time_str, log_time_format)

                        log_hour_str = log_time.strftime("%Y-%m-%d %H:00")
#                    
                    pattern = re.compile(r"CODE 201 \[Cart CART_(\d+)] Loading case (\d+) of (\d+) from cart \w+ for item (\d+)")

                    match = pattern.search(line)
                    if match:
                        cart_id, current_case, total_cases, item_id = match.groups()
                        current_case = int(current_case)
                        total_cases = int(total_cases)
                        
                        robot_destro_data[f"Cart {int(cart_id)}"][item_id] = {
                            # "loaded_cases": current_case,
                            "total_cases": total_cases
                        }
                        # robot_destro_data[cart_id][item_id]["loaded_cases"] += 1
                        # robot_destro_data[cart_id][item_id]["total_cases"] = int(total_cases)
                        robot_total_cases[cart_id] += 1

                        cases_per_hour[cart_id][log_hour_str] += 1

                elif "CODE 101" in line:
                    pattern =re.compile(r"CODE 101 --------------- (\d+)")
                    match =pattern.search(line)
                    # print(match)
                    if match :
                        cases=match.groups()
                        # print(f"cases ----{cases}")
                      

                        log_data['total_cases']=int(cases[0])
                elif "[IDLE] CODE 701 " in line:
                    # pattern=  re.compile(r"[IDLE] Cart CART_(\d+) total idle time: ([\d.]+) seconds")
                    pattern = re.compile(r"\[IDLE\] CODE 701 Cart CART_(\d+) total idle time: ([\d.]+) seconds")

                    match=pattern.search(line)
                    if match:
                        cart_id,idle_time=match.groups()
                        idle_time=float(idle_time)/60
                        cart_full_idle[f"Cart {cart_id}"]=idle_time
                elif "[IDLE] CODE 601 " in line:
                    # pattern=  re.compile(r"[IDLE] Cart CART_(\d+) total idle time: ([\d.]+) seconds")
                    pattern = re.compile(r"\[IDLE\] CODE 601 Cart CART_(\d+) total idle time: ([\d.]+) seconds")

                    match=pattern.search(line)
                    if match:
                        cart_id,idle_time=match.groups()
                        idle_time=float(idle_time)/60
                        cart_empty_idle[f"Cart {cart_id}"]=idle_time
                elif "CODE 501" in line:
                    
                    pattern= re.compile(r"CODE 501 Trips taken by Robot_(\d+) is (\d+)")
                    match=pattern.search(line)
                    if match:
                        robot_id,trips=match.groups()
                        trips_robot[f"Robot {int(robot_id)+1}"]=trips
                elif "[DOOR DWELL] CODE 801 Inbound" in line:
                    pattern=re.compile(r"\[DOOR DWELL\] CODE 801 Inbound dock Inbound_(\d+) total dwell time : ([\d.]+)")
                    match=pattern.search(line)
                    if match:
                        indoor_id, dtime=match.groups()
                        dtime =float(dtime)/60
                        indoor_idle[f"Inbound {indoor_id}"]=dtime
                elif "[DOOR DWELL] CODE 801 Outbound" in line:
                    pattern=re.compile(r"\[DOOR DWELL\] CODE 801 Outbound dock Outbound_(\d+) total dwell time : ([\d.]+)")
                    match=pattern.search(line)
                    if match:
                        outdoor_id, dtime=match.groups()
                        dtime =float(dtime)/60
                        outdoor_idle[f"Outbound {outdoor_id}"]=dtime

def start_destro_thread(log_path):
    thread1 = threading.Thread(target=read_destro_log, args=(log_path,), daemon=True)
    thread1.start()


def start_fms_thread(log_path):
    thread2 =threading.Thread(target= read_fms_log, args=(log_path,),daemon= True)
    thread2.start()
def start_timing_thread():
    clock_thread=threading.Thread(target=update_elapsed_time,daemon=True)
    clock_thread.start()
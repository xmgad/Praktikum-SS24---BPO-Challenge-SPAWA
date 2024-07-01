import requests
import random
from datetime import datetime, timedelta

base_url = "https://cpee.org/flow/start/url/"
init_data = {
    "behavior": "fork_running",
    "url": "https://cpee.org/hub/server/Teaching.dir/Prak.dir/Challengers.dir/Amgad_Al-Zamkan.dir/Main_03710934.xml",
}
possible_patient_types = ["EM","A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4"]

total_patients = 10

#calculate the current time for the first patient
current_time = datetime.now()

for i in range(total_patients):
    # Format the arrival time for each patient
    arrival_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
    patient_type = random.choice(possible_patient_types)
    
    # Data for the current request
    data = {
        **init_data,
        "init": f'{{"patient_type":"{patient_type}", "arrival_time":"{arrival_time}"}}',
    }
    
    # Send POST request
    response = requests.post(base_url, data=data)
    print(f"Request {i+1} - Status Code:", response.status_code)
    
    try:
        response_json = response.json()
        print(f"Request {i+1} - CPEE-INSTANCE:", response_json.get("CPEE-INSTANCE"))
    except ValueError:
        print(f"Request {i+1} - Response does not contain valid JSON data.")
    
    # Increment the time by 2 minutes for the next patient
    current_time += timedelta(minutes=2)
from bottle import Bottle, request, response, run
import json  
import random
import requests

app = Bottle()

#Global dictionary to store patient data
patients = {}
resources = {
    'EM': 9,
    'INTAKE': 4,
    #Surgery
    'OR': 5, 
    # Nursing
    'A_BED': 30,
    'B_BED': 40
}

def checkResources(patient_type, resource_type, is_new_patient):
    status = None
    if patient_type != "EM" and is_new_patient: #Set replan to true only if patient type is not "EM" and new
        replan = True
        status ='INTAKE'
    else:
            if resources[resource_type] > 0:
                 replan = False
                 status = resource_type
            else:
                 replan = True
    return replan, status

@app.post('/admitPatient')
def admitPatient():
    print(patients)
    print('\nentered admitPatient\n')

    #Extract patient_type and patient_id 
    data = request.json
    #print(data)
    status = None
    if data:
        patient_id = data.get('patient_id')
        patient_type = data.get('patient_type')
        replan = data.get('replan')
    else:
        patient_id = request.forms.get('patient_id') or request.query.patient_id
        patient_type = request.forms.get('patient_type') or request.query.patient_type
        replan = request.forms.get('replan') or request.query.replan
        replan = request.forms.get('status') or request.query.status

    # print(patient_type + " pt ")
    # print(patient_id + " p_id ")
    # print(str(replan) + " replan ")

    # Check if the patient_id exists, if not, generate one
    if not patient_id:
        print('no patient id -     ')
        patient_id = random.randint(1000, 9999)  # Example range for IDs
        while patient_id in patients:
            patient_id = random.randint(1000, 9999)  # Ensure uniqueness
        patients[patient_id] = {'patient_type': patient_type}  # Add to dictionary
        replan, status = checkResources(patient_type, "EM", True)
        print(patient_id)
    else:
        replan, status = checkResources(patient_type, "INTAKE", False) 
    #New patient added above, prepare response
    response_data = {
        'message': f"New patient {patient_id} admitted.",
        'patient_id': patient_id,
        'patient_type': patient_type,
        'replan': replan,
        'status': status
        }
    print(response_data)
    print(patients)

    #response content type to application/json
    response.content_type = 'application/json'
    return json.dumps(response_data)




@app.post('/replanPatient')
def replanPatient():
    print("entered replanPatient")
    print(patients)
    patient_id = int(request.forms.get('patient_id', None))
    response.content_type = 'application/json'
    request_data = {
         "behavior": "fork_running",
         "url": "https://cpee.org/hub/server/Teaching.dir/Prak.dir/Challengers.dir/Amgad_Al-Zamkan.dir/Main_03710934.xml",
        "init": json.dumps({
             "patient_id": patient_id
        })
    }
    res = requests.post('https://cpee.org/flow/start/url/', request_data)
    print(res)
    if res.status_code != 200:
         raise Exception(res)
    print("exit replanPatient")
    return json.dumps({})


def nextTreatment(diagnosis, status):
    print("nextTreatment: " + diagnosis + " - " + status)
    if (diagnosis == 'A1' or diagnosis == 'B1' or diagnosis == 'B2'):
        if (status == "INTAKE" or status == "EM"):
            return "NURSING"
        elif(status == 'NURSING' and determineComp(diagnosis)):
            print("complications: yes")
            return "NURSING"
        else:
            print('time to release')
            return "RELEASE"         
                
    else:
        #A2, A3, A4, B3, B4
        if (status == "INTAKE" or status == "EM"):
            return "OR"
        elif(status == "OR"):
            return "NURSING"
        elif(status == "NURSING" and determineComp(diagnosis)):
            print("complications: yes")
            return "OR"
        else:
            print('time to release')
            return "RELEASE" 
     
         
def determineDiagnosis(patient_type):
    print("entered determineDiagnosis")

    diagnoses = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4']
    probabilities = [0.125, 0.125, 0.125, 0.125, 0.5, 0.25, 0.0625, 0.0625]

    #non EM patient type already = diagnosis
    if patient_type != 'EM':
        return patient_type
    #assign EM patient diagnosis based on given p
    else:
        diagnosis = random.choices(diagnoses, weights=probabilities, k=1)
        return diagnosis[0] 

def determineComp(diagnosis):

    probabilities = {'A1': 0.125, 'A2': 0.125, 'A3': 0.125, 'A4': 0.125, 
    'B1': 0.5, 'B2': 0.25, 'B3': 0.0625,'B4': 0.0625 }

    print("entered determineComp")

    return random.random() < probabilities.get(diagnosis, 0)



@app.post('/treatPatient')
def treatPatient():
    print("entered treatPatient")
    status = request.forms.get('status', None)
    patient_id = int(request.forms.get('patient_id', None))
    diagnosis = None
    
    print('currently in: ' + status)

    if (status == 'EM'):
        if random.choice([True,False]):
            status = 'RELEASE'
        else:
            diagnosis = determineDiagnosis(patients[patient_id]['patient_type'])
            patients[patient_id]['diagnosis'] = diagnosis
            status = nextTreatment(diagnosis, status)
            #decrement EM resources
        resources['EM'] -= 1

    elif (status == 'INTAKE'):
        status = nextTreatment(patients[patient_id]['patient_type'], status)
        #decrement INTAKE resources
        resources['INTAKE'] -= 1
    elif (status == 'OR'):
        status = nextTreatment(patients[patient_id]['patient_type'], status)
        resources['OR'] -=1
    elif(status == 'NURSING'):
        if(patients[patient_id]['patient_type'] == "EM"):
           status = nextTreatment(patients[patient_id]['diagnosis'], status)
        else:
            status = nextTreatment(patients[patient_id]['patient_type'], status)

        if( 'A' in patients[patient_id]['patient_type'] or patients[patient_id]['diagnosis']):
            resources['A_BED'] -= 1
        else:
            resources['B_BED'] -= 1
    else:
        print("Patient will be released")


    response_data = {
        'message': f"Patient {patient_id} needs to go to {status} .",
        'patient_id': patient_id,
        'status': status,
        'diagnosis': diagnosis
        }
    print("status: " + status)
    print("exit treatPatient")

    response.content_type = 'application/json'
    return json.dumps(response_data)


if __name__ == '__main__':
       app.run(host='::1', port=12857)


     

    # treatment_type = request.forms.get('treatment_type', None)
    # status = request.forms.get('status', None)
    # patient_id = int(request.forms.get('patient_id', None))
    # patient = patients[patient_id]
    # if status == 'RELEASE':
    #     resources[treatment_type] += 1
    #     return {}
    # else:
    #     resources[treatment_type] -= 1

    # # Determine status next round
    # if patient['patient_type'] == 'EM':
    #     is_release =  random.choice(True, False)
    #     if is_release:
    #         new_status = 'RELEASE'
    #     else:
    #         determine_new_status(patient['patient_type'])
    #         # hard code next step (nursing if intake and a1/b1/b2)
    #         # else other next step
            
             
    # response.content_type = 'application/json'
    # return json.dumps({
    #      # return next status or treatment type
    # })




# if __name__ == '__main__':
#        app.run(host='::1', port=12855)






# from bottle import Bottle, request, response, run
# import random
# import json
# import datetime

# app = Bottle()


# from bottle import Bottle, request, response, run
# import random
# import json
# import datetime

# app = Bottle()

# # In-memory data structure to store patient data
# patients = {}

# # Resource management dictionary
# resources = {
#     'ER_Resources': 9,
#     'Intake_Resources': 4,
#     'Operation_Rooms': 5,
#     'Nursing_Type_A_Beds': 30,
#     'Nursing_Type_B_Beds': 40
# }

# @app.post('/admitPatient')
# def admitPatient():
#     global patients
#     print('admit patients', patients)
#     # Extract data from query parameters
#     patient_id = request.query.patient_id
#     patient_type = request.query.patient_type
#     arrival_time = request.query.arrival_time
#     status = request.query.get('status', 'waiting')  # Default to 'waiting' if no status provided

#     # If patient_id is not provided or is empty, generate a random one
#     if not patient_id:
#         print('no patient id - ')
#         patient_id = random.randint(1000, 9999)  # Example range for IDs
#         while patient_id in patients:
#             patient_id = random.randint(1000, 9999)  # Ensure uniqueness

#     # Save the patient data
#     patients[patient_id] = {
#         'patient_type': patient_type,
#         'arrival_time': arrival_time,
#         'status': status
#     }

#     print(' added patient to patient dic - ')

#     # Prepare the response data
#     response_data = {
#         'message': f'Patient {patient_id} admitted with status {status}',
#         'patient_type': patient_type,
#         'patient_id': patient_id,
#         'status': status,
#         'arrival_time': arrival_time
#     }

#     # Set the response content type to application/json
#     response.content_type = 'application/json'
#     return json.dumps(response_data)

# if __name__ == '__main__':
#       app.run(host='::1', port=12855)





































# resources=9

# @app.post('/admitPatient')
# def admitPatient():
#         global resources
#         print("admitPatientttt", resources)
#         patient_type = request.query.patient_type
#         patient_id = request.query.patient_id

#         # Check if a patient_id is provided, if not, create a new patient and get the new ID
#         if not patient_id:
#             patient_id = 1

#         # Check resource availability
#         if patient_type == 'EM':
#             status = 'ER Treatment'
#             resources= resources-1
#         else:
#             status = 'Intake'  # Assuming a default status for other types

#         response_data = {
#             'message': f'Patient {patient_id} with status {status} is released',
#             'patient_id': patient_id,
#             'status': status,
#         }

#         # Set the response content type to application/json
#         response.content_type = 'application/json'
#         return json.dumps(response_data)

# if __name__ == '__main__':
#      app.run(host='::1', port=12855)


# def create_patient(db, patient_type, arrival_time):
#     cursor = db.cursor()
#     cursor.execute("INSERT INTO Patients (patient_type, arrival_time, status) VALUES (?, ?, 'waiting')", (patient_type, arrival_time))
#     db.commit()
#     return cursor.lastrowid  # Return the auto-generated ID of the newly created patient


# def update_patient_status(db, patient_id, status):
#     cursor = db.cursor()
#     new_patient_type = None  # Initialize to None to handle cases where no new type is assigned

#     if status == 'ER Treatment':
#         # Determine a new patient type only for ER treatments
#         new_patient_type = determine_new_patient_type()
#         # Update patient status and new patient type in the "Patients" table
#         cursor.execute("""
#             UPDATE Patients 
#             SET status = ?, last_updated = ?, patient_type = ?
#             WHERE patient_id = ?""",
#             (status, datetime.datetime.now(), new_patient_type, patient_id))
#     else:
#         # For non-ER treatments, just update the status and last_updated
#         cursor.execute("""
#             UPDATE Patients 
#             SET status = ?, last_updated = ?
#             WHERE patient_id = ?""",
#             (status, datetime.datetime.now(), patient_id))

#     # Decrement a resource; resource_type is derived from status
#     resource_type = 'ER' if status == 'ER Treatment' else 'Intake'
#     cursor.execute("UPDATE Resources SET in_use_count = in_use_count + 1 WHERE resource_type = ?", (resource_type,))
#     db.commit()

# def determine_new_patient_type():
#     # Assign a diagnosis with a 50% chance
#     if random.random() < 0.5:
#         # Create a random diagnosis by selecting from predefined types
#         diagnosis_types = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4']
#         diagnosis = random.choice(diagnosis_types)
#         return f'EM-{diagnosis}'
#     else:
#         # 50% chance to just have phantom pain with no specific diagnosis
#         return 'EM-Phantom Pain'

# #good to go
# def resource_availability_check(db, patient_type):
#     resource_type = 'ER' if patient_type == 'EM' else 'Intake'
#     cursor = db.cursor()
#     cursor.execute("SELECT total_count, in_use_count FROM Resources WHERE resource_type = ?", (resource_type,))
#     total, in_use = cursor.fetchone()
#     return total > in_use


# @app.teardown_appcontext
# def teardown(error):
#     """Close the db connection at the end of the request or when the application shuts down."""
#     close_db(error)

# def replanPatient(db, patient_id):
#     print("replan")





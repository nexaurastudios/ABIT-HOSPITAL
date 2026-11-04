import random
from datetime import datetime, date, time, timedelta
from app.extensions import db
from app.models.department import Department
from app.models.doctor import Doctor, DoctorSchedule
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.visit import Visit
from app.models.bed import Bed, Admission
from app.models.resource import Resource
from app.models.notification import Notification
from app.services.activity_logger import log_activity

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
    "Edward", "Deborah", "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Sharon",
    "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    "Nicholas", "Shirley", "Eric", "Angela", "Jonathan", "Helen", "Stephen", "Anna",
    "Larry", "Brenda", "Justin", "Pamela", "Scott", "Nicole", "Brandon", "Emma",
    "Benjamin", "Samantha", "Samuel", "Katherine", "Gregory", "Christine", "Frank", "Debra",
    "Alexander", "Rachel", "Raymond", "Catherine", "Patrick", "Carolyn", "Jack", "Janet",
    "Dennis", "Ruth", "Jerry", "Maria", "Tyler", "Heather", "Aaron", "Diane",
    "Jose", "Virginia", "Adam", "Julie", "Henry", "Joyce", "Nathan", "Victoria",
    "Douglas", "Olivia", "Zachary", "Kelly", "Peter", "Christina", "Kyle", "Lauren"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
    "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy",
    "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey",
    "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson",
    "Watson", "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza",
    "Ruiz", "Hughes", "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers",
    "Long", "Ross", "Foster", "Jimenez", "Powell", "Jenkins", "Perry", "Russell"
]

CITIES = [
    "Metro Health District", "Downtown Medical Center", "North Suburb", "South Bay",
    "Westside Medical Park", "East Hill", "Oakridge District", "Pine Grove", "Riverside"
]

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

DEPARTMENT_DEFINITIONS = [
    {"name": "Cardiology", "code": "CARD", "head": "Dr. Arthur Vance", "floor": "Floor 3, East Wing", "phone": "ext. 301"},
    {"name": "Neurology", "code": "NEUR", "head": "Dr. Eleanor Vance", "floor": "Floor 4, West Wing", "phone": "ext. 402"},
    {"name": "Orthopaedics", "code": "ORTH", "head": "Dr. Marcus Brody", "floor": "Floor 2, Central", "phone": "ext. 203"},
    {"name": "General Medicine", "code": "GENM", "head": "Dr. Sarah Sterling", "floor": "Floor 1, Main Pavilion", "phone": "ext. 104"},
    {"name": "Pediatrics", "code": "PEDI", "head": "Dr. Clara Oswald", "floor": "Floor 2, East Wing", "phone": "ext. 205"},
    {"name": "Dermatology", "code": "DERM", "head": "Dr. Julian Bashir", "floor": "Floor 1, Clinic A", "phone": "ext. 106"},
    {"name": "Emergency", "code": "EMRG", "head": "Dr. Leonard McCoy", "floor": "Ground Floor, Trauma Bay", "phone": "ext. 001"},
    {"name": "Gynecology", "code": "GYNE", "head": "Dr. Beverly Crusher", "floor": "Floor 3, West Wing", "phone": "ext. 308"},
    {"name": "ENT", "code": "ENTD", "head": "Dr. Phlox Denobula", "floor": "Floor 1, Clinic B", "phone": "ext. 109"},
    {"name": "Ophthalmology", "code": "OPHT", "head": "Dr. Katherine Pulaski", "floor": "Floor 2, Clinic C", "phone": "ext. 210"},
]

DOCTOR_SPECIALTIES = {
    "Cardiology": [("Interventional Cardiology", "MD, FACC"), ("Electrophysiology", "MD, FHRS"), ("Heart Failure Specialist", "MBBS, MD")],
    "Neurology": [("Stroke Specialist", "MD, FAAN"), ("Neuro-oncology", "MD, PhD"), ("Epilepsy Specialist", "MD")],
    "Orthopaedics": [("Joint Replacement", "MS (Ortho)"), ("Spine Surgery", "MS, MCh"), ("Sports Medicine", "MD, Ortho")],
    "General Medicine": [("Internal Medicine", "MD (Internal)"), ("Critical Care", "MD, FCCP"), ("Preventive Medicine", "MBBS, MD")],
    "Pediatrics": [("Neonatology", "MD, FAAP"), ("Pediatric Cardiology", "MD, DM"), ("General Pediatrics", "MBBS, DCH")],
    "Dermatology": [("Cosmetic Dermatology", "MD (Derm)"), ("Dermatosurgery", "MD, DNB"), ("Pediatric Dermatology", "MBBS, MD")],
    "Emergency": [("Trauma Specialist", "MD (Emergency)"), ("Acute Resuscitation", "MBBS, FACEM"), ("Disaster Medicine", "MD")],
    "Gynecology": [("Obstetrics & Gynae", "MS (OBG)"), ("Reproductive Endocrinology", "MD, DM"), ("Gynecologic Oncology", "MS, MCh")],
    "ENT": [("Otology & Neurotology", "MS (ENT)"), ("Rhinology & Sinus", "MS (ENT)"), ("Head & Neck Surgery", "MS, DNB")],
    "Ophthalmology": [("Cataract & Refractive", "MS (Ophth)"), ("Retina Specialist", "MD, FVRS"), ("Glaucoma Specialist", "MS (Ophth)")]
}

def seed_departments():
    """Ensure all 10 standard departments exist"""
    created = 0
    depts = []
    for d_def in DEPARTMENT_DEFINITIONS:
        dept = Department.query.filter_by(code=d_def['code']).first()
        if not dept:
            dept = Department(
                name=d_def['name'],
                code=d_def['code'],
                description=f"Specialized healthcare division providing comprehensive care in {d_def['name']}.",
                head_of_department=d_def['head'],
                floor=d_def['floor'],
                phone=d_def['phone'],
                is_active=True
            )
            db.session.add(dept)
            created += 1
        depts.append(dept)
    db.session.commit()
    return created

def seed_doctors(target_count=30):
    """Seed 30 qualified doctors across departments"""
    existing_count = Doctor.query.count()
    if existing_count >= target_count:
        return 0

    depts = Department.query.all()
    created = 0
    doc_num = existing_count + 1

    for dept in depts:
        specs = DOCTOR_SPECIALTIES.get(dept.name, [("General Specialist", "MD")])
        for spec_name, qual in specs:
            doc_id = f"DOC-{1000 + doc_num}"
            if not Doctor.query.filter_by(doctor_id=doc_id).first():
                first = random.choice(FIRST_NAMES)
                last = random.choice(LAST_NAMES)
                name = f"{first} {last}"
                email = f"{first.lower()}.{last.lower()}{doc_num}@apexhealth.org"
                
                # Alternate shift times: 08:00 - 16:00 or 12:00 - 20:00
                start_h = 8 if (doc_num % 2 == 1) else 12
                end_h = start_h + 8

                avail_status = random.choice(['Available', 'Available', 'Available', 'Busy', 'On Leave'])

                doc = Doctor(
                    doctor_id=doc_id,
                    name=name,
                    qualification=qual,
                    specialization=spec_name,
                    department_id=dept.id,
                    phone=f"+1 555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                    email=email,
                    experience_years=random.randint(4, 25),
                    duty_start_time=time(start_h, 0),
                    duty_end_time=time(end_h, 0),
                    availability_status=avail_status,
                    max_patient_capacity=random.randint(20, 35),
                    is_active=True,
                    is_demo=True
                )
                db.session.add(doc)
                db.session.flush()

                # Add weekly schedule Mon-Fri
                for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
                    sched = DoctorSchedule(
                        doctor_id=doc.id,
                        day_of_week=day,
                        start_time=time(start_h, 0),
                        end_time=time(end_h, 0),
                        slot_duration_minutes=20,
                        max_slots=24,
                        is_active=True
                    )
                    db.session.add(sched)

                created += 1
                doc_num += 1

    db.session.commit()
    return created

def seed_beds(target_count=200):
    """Seed 200 hospital beds across 5 types and various wards"""
    existing_count = Bed.query.count()
    if existing_count >= target_count:
        return 0

    depts = Department.query.all()
    bed_types = [
        ("General Ward", 110),
        ("ICU", 30),
        ("Private Room", 30),
        ("Emergency", 20),
        ("Semi-Private", 10)
    ]
    
    created = 0
    bed_seq = existing_count + 1

    for b_type, count_needed in bed_types:
        for i in range(count_needed):
            if existing_count + created >= target_count:
                break
            dept = random.choice(depts)
            bed_code_prefix = b_type[:3].upper()
            bed_id = f"BED-{bed_code_prefix}-{bed_seq:03d}"
            
            if not Bed.query.filter_by(bed_id=bed_id).first():
                ward = f"{dept.name} Ward {chr(65 + (i % 4))}"
                bed = Bed(
                    bed_id=bed_id,
                    bed_number=f"{bed_seq:03d}",
                    department_id=dept.id,
                    ward=ward,
                    bed_type=b_type,
                    occupancy_status='Available',
                    is_demo=True
                )
                db.session.add(bed)
                created += 1
                bed_seq += 1

    db.session.commit()
    return created

def seed_resources():
    """Seed essential hospital operational equipment"""
    if Resource.query.count() > 0:
        return 0

    depts = Department.query.all()
    resource_templates = [
        ("Mechanical Ventilator (ICU Grade)", "Ventilator", 12, 8),
        ("Multipara Patient Monitor", "Monitor", 35, 24),
        ("Advanced Cardiac Life Support Defibrillator", "Defibrillator", 15, 12),
        ("High-Flow Oxygen Concentrator", "Oxygen Concentrator", 40, 29),
        ("Transport Wheelchair", "Wheelchair", 50, 42),
        ("Mobile Digital X-Ray Unit", "Diagnostic", 6, 5),
        ("Infusion Pump System", "Pump", 60, 48),
        ("Hemodialysis Machine", "Dialysis", 8, 6),
        ("Trauma Stretcher Gurney", "Stretcher", 30, 25),
        ("Rapid Blood Gas Analyzer", "Laboratory", 5, 4)
    ]

    created = 0
    for r_name, r_type, total, avail in resource_templates:
        dept = random.choice(depts)
        res = Resource(
            resource_name=r_name,
            resource_type=r_type,
            department_id=dept.id,
            total_quantity=total,
            available_quantity=avail,
            status='Operational'
        )
        db.session.add(res)
        created += 1

    db.session.commit()
    return created

def seed_patients(target_count=5000, batch_size=500):
    """Seed synthetic patients in high-speed batches up to 5000"""
    existing_count = Patient.query.count()
    if existing_count >= target_count:
        return 0

    to_create = target_count - existing_count
    depts = Department.query.all()
    dept_ids = [d.id for d in depts] if depts else [1]

    created = 0
    start_seq = existing_count + 1
    today = date.today()

    for batch_start in range(0, to_create, batch_size):
        current_batch_size = min(batch_size, to_create - batch_start)
        batch_patients = []

        for i in range(current_batch_size):
            seq = start_seq + batch_start + i
            pat_id = f"PAT-202611-{seq:05d}"
            
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            gender = random.choice(["Male", "Female", "Other"])
            age = random.randint(1, 89)
            
            # Registration date distributed over last 180 days
            days_ago = random.randint(0, 180)
            reg_date = today - timedelta(days=days_ago)
            
            dob = today - timedelta(days=int(age * 365.25) + random.randint(0, 360))
            bg = random.choice(BLOOD_GROUPS)
            
            p = Patient(
                patient_id=pat_id,
                full_name=f"{first} {last} [DEMO]",
                age=age,
                dob=dob,
                gender=gender,
                phone=f"+1 555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                email=f"{first.lower()}.{last.lower()}{seq}@demo-patient.org",
                address=f"{random.randint(100, 999)} {random.choice(CITIES)} Ave",
                blood_group=bg,
                emergency_contact=f"+1 555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                registration_date=reg_date,
                assigned_department_id=random.choice(dept_ids),
                status='Outpatient',
                is_demo=True
            )
            batch_patients.append(p)

        db.session.bulk_save_objects(batch_patients)
        db.session.commit()
        created += current_batch_size

    return created

def seed_appointments_and_visits(target_count=1000):
    """Seed 1000 appointments and realistic visits with timestamps for waiting time calculations"""
    existing_count = Appointment.query.count()
    if existing_count >= target_count:
        return 0

    to_create = target_count - existing_count
    patients = Patient.query.limit(2000).all()
    doctors = Doctor.query.all()
    
    if not patients or not doctors:
        return 0

    today = date.today()
    created_appts = 0
    created_visits = 0

    # Group doctors by department
    dept_doctors = {}
    for d in doctors:
        dept_doctors.setdefault(d.department_id, []).append(d)

    appt_seq = existing_count + 1

    for i in range(to_create):
        # Choose random patient and department
        pat = random.choice(patients)
        dept_id = pat.assigned_department_id or random.choice(list(dept_doctors.keys()))
        docs = dept_doctors.get(dept_id, doctors)
        doc = random.choice(docs)

        # Dates: 80% past 60 days, 20% next 7 days
        if random.random() < 0.8:
            days_offset = -random.randint(0, 60)
        else:
            days_offset = random.randint(0, 7)

        appt_date = today + timedelta(days=days_offset)
        appt_hour = random.randint(8, 16)
        appt_minute = random.choice([0, 15, 20, 30, 40, 45])
        appt_time = time(appt_hour, appt_minute)

        appt_id = f"APT-202611-{appt_seq:05d}"
        appt_seq += 1

        if days_offset < 0:
            status = random.choice(['Completed', 'Completed', 'Completed', 'Cancelled', 'No Show'])
        elif days_offset == 0:
            status = random.choice(['Scheduled', 'Confirmed', 'Waiting', 'In Consultation', 'Completed'])
        else:
            status = random.choice(['Scheduled', 'Confirmed'])

        appt = Appointment(
            appointment_id=appt_id,
            patient_id=pat.id,
            doctor_id=doc.id,
            department_id=dept_id,
            appointment_date=appt_date,
            appointment_time=appt_time,
            status=status,
            reason=random.choice([
                "Routine health checkup", "Persistent headache and dizziness", "Joint stiffness and knee pain",
                "Skin rash and allergic flare-up", "Cardiovascular follow-up", "Pediatric wellness examination",
                "Acute ear pain and hearing discomfort", "Vision blur and eye strain", "Shortness of breath on exertion"
            ]),
            notes="Demo generated medical appointment.",
            is_demo=True
        )
        db.session.add(appt)
        db.session.flush()
        created_appts += 1

        # If appointment was Completed or In Progress, create a corresponding Visit record with timestamps!
        if status in ['Completed', 'Waiting', 'In Consultation'] or (days_offset < 0 and status not in ['Cancelled', 'No Show']):
            # Construct arrival time
            base_dt = datetime.combine(appt_date, appt_time)
            # Arrived 5-25 minutes before or after appt
            arrival = base_dt - timedelta(minutes=random.randint(5, 20))
            reg_time = arrival + timedelta(minutes=random.randint(2, 6))

            if status == 'Waiting':
                # Patient is currently waiting; consultation hasn't started yet!
                consult_start = None
                consult_end = None
                v_status = 'Waiting'
            elif status == 'In Consultation':
                # Consultation just started 5-10 mins ago
                waiting_mins = random.randint(10, 40)
                consult_start = arrival + timedelta(minutes=waiting_mins)
                consult_end = None
                v_status = 'In Consultation'
            else:
                # Completed visit: realistic waiting time 8 - 55 minutes
                waiting_mins = random.randint(12, 50)
                consult_start = arrival + timedelta(minutes=waiting_mins)
                duration_mins = random.randint(10, 30)
                consult_end = consult_start + timedelta(minutes=duration_mins)
                v_status = 'Completed'

            visit = Visit(
                visit_id=f"VIS-202611-{created_appts:05d}",
                appointment_id=appt.id,
                patient_id=pat.id,
                doctor_id=doc.id,
                department_id=dept_id,
                visit_date=appt_date,
                arrival_time=arrival,
                registration_time=reg_time,
                consultation_start_time=consult_start,
                consultation_end_time=consult_end,
                status=v_status,
                symptoms=appt.reason,
                diagnosis="Evaluated condition; clinical findings documented.",
                prescription="Prescribed symptomatic therapy and follow-up advice.",
                is_demo=True
            )
            visit.calculate_metrics()
            db.session.add(visit)
            created_visits += 1

    db.session.commit()
    return created_appts

def seed_admissions_and_occupancy(active_target=45, past_discharges=80):
    """Seed admissions and bind beds to demonstrate active and discharged states"""
    if Admission.query.count() >= (active_target + past_discharges):
        return 0

    beds = Bed.query.filter_by(occupancy_status='Available').all()
    patients = Patient.query.filter_by(status='Outpatient').limit(150).all()
    doctors = Doctor.query.all()

    if not beds or not patients:
        return 0

    created = 0
    adm_seq = 1
    now = datetime.utcnow()

    # 1. Past Discharged Admissions
    for i in range(min(past_discharges, len(patients) // 2)):
        pat = patients[i]
        bed = random.choice(beds)
        doc = random.choice(doctors)
        
        adm_date = now - timedelta(days=random.randint(10, 45))
        dis_date = adm_date + timedelta(days=random.randint(2, 7))

        adm = Admission(
            admission_id=f"ADM-202611-{adm_seq:05d}",
            patient_id=pat.id,
            department_id=bed.department_id,
            doctor_id=doc.id,
            bed_id=bed.id,
            admission_date=adm_date,
            discharge_date=dis_date,
            admission_reason="Inpatient medical management and monitoring",
            diagnosis="Resolved primary symptoms following clinical intervention",
            discharge_notes="Patient stable, vitals normal; discharge instructions provided.",
            discharge_condition="Recovered",
            status='Discharged',
            is_demo=True
        )
        db.session.add(adm)
        pat.status = 'Discharged'
        created += 1
        adm_seq += 1

    # 2. Active Inpatient Admissions (assigning beds atomically!)
    active_count = 0
    available_beds = Bed.query.filter_by(occupancy_status='Available').all()
    remaining_patients = Patient.query.filter_by(status='Outpatient').all()

    for bed in available_beds:
        if active_count >= active_target or not remaining_patients:
            break
        
        pat = remaining_patients.pop()
        doc = random.choice(doctors)
        adm_date = now - timedelta(days=random.randint(1, 5), hours=random.randint(1, 10))

        adm = Admission(
            admission_id=f"ADM-202611-{adm_seq:05d}",
            patient_id=pat.id,
            department_id=bed.department_id,
            doctor_id=doc.id,
            bed_id=bed.id,
            admission_date=adm_date,
            discharge_date=None,
            admission_reason="Acute inpatient treatment requiring specialized bed care",
            diagnosis="Active therapeutic course in progress",
            status='Active',
            is_demo=True
        )
        db.session.add(adm)
        db.session.flush()

        # Update bed occupancy atomically
        bed.occupancy_status = 'Occupied'
        bed.current_patient_id = pat.id
        bed.current_admission_id = adm.id

        # Update patient status
        pat.status = 'Admitted'

        created += 1
        active_count += 1
        adm_seq += 1

    # Set a few beds to Maintenance or Reserved for realism
    avail_beds_left = Bed.query.filter_by(occupancy_status='Available').limit(15).all()
    for idx, b in enumerate(avail_beds_left):
        if idx % 3 == 0:
            b.occupancy_status = 'Maintenance'
        elif idx % 3 == 1:
            b.occupancy_status = 'Reserved'

    db.session.commit()
    return created

def generate_full_synthetic_dataset():
    """Master idempotent generator method"""
    log_activity("SYNTHETIC_DATA_GENERATION", "Datasets", "Started complete synthetic data generation pipeline")

    depts_created = seed_departments()
    docs_created = seed_doctors(30)
    beds_created = seed_beds(200)
    res_created = seed_resources()
    pats_created = seed_patients(5000)
    appts_created = seed_appointments_and_visits(1000)
    adms_created = seed_admissions_and_occupancy(45, 80)

    summary = {
        'departments': depts_created,
        'doctors': docs_created,
        'beds': beds_created,
        'resources': res_created,
        'patients': pats_created,
        'appointments': appts_created,
        'admissions': adms_created
    }

    log_activity(
        "SYNTHETIC_DATA_GENERATED",
        "Datasets",
        f"Generated {pats_created} patients, {appts_created} appointments, {adms_created} admissions."
    )

    return summary

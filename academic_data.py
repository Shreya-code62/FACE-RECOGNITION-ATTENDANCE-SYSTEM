COLLEGE_INFO = {
    "name": "I.T.S Engineering College",
    "department": "Computer Science & Engineering (CSE)",
    "academic_year": "2026-27",
    "semester": "II Year III Sem (Odd Semester)",
    "room": "New Building (NB)-245",
    "effective_from": "16th July 2026",
}

SUBJECTS = [
    {
        "name": "Digital Electronics",
        "short_name": "DE",
        "code": "BOE-310",
        "faculty": "Dr. Jaspal Kumar",
        "kind": "Theory",
    },
    {
        "name": "Universal Human Values",
        "short_name": "UHV",
        "code": "BVE-301",
        "faculty": "Mr. Anuj Rajdhan",
        "kind": "Theory",
    },
    {
        "name": "Data Structures",
        "short_name": "DS",
        "code": "BCS-301",
        "faculty": "Ms. P.K./Mr. Y.S.",
        "kind": "Theory",
    },
    {
        "name": "Computer Organization & Architecture",
        "short_name": "COA",
        "code": "BCS-302",
        "faculty": "Ms. Arpita Srivastava",
        "kind": "Theory",
    },
    {
        "name": "Discrete Structure & Theory of Logic",
        "short_name": "DSTL",
        "code": "BCS-303",
        "faculty": "Mr. Abhishek Shivhare",
        "kind": "Theory",
    },
    {
        "name": "Cyber Security",
        "short_name": "CS",
        "code": "BCC-301",
        "faculty": "Mr. Abhishek Kumar",
        "kind": "Theory",
    },
    {
        "name": "Data Structure Lab",
        "short_name": "DS LAB",
        "code": "BCS-351",
        "faculty": "Ms. P.K./Mr. Y.S., Mr. Vikas Kumar, Mr. Rahul Kumar",
        "kind": "Lab",
    },
    {
        "name": "Computer Organization & Architecture Lab",
        "short_name": "COA LAB",
        "code": "BCS-352",
        "faculty": "Mr. Arpita Srivastava",
        "kind": "Lab",
    },
    {
        "name": "Web Designing Workshop Lab",
        "short_name": "WDW LAB",
        "code": "BCS-353",
        "faculty": "Mr. Abhishek Kumar",
        "kind": "Lab",
    },
    {
        "name": "Mini Project Lab",
        "short_name": "M.P. LAB",
        "code": "BCC-351",
        "faculty": "Mr. Abhishek Shivhare",
        "kind": "Lab",
    },
    {
        "name": "iOS Training Development",
        "short_name": "iOS LAB",
        "code": "NA",
        "faculty": "Mr. Atul Agrawal",
        "kind": "Lab",
    },
]

SUBJECT_BY_CODE = {subject["code"]: subject for subject in SUBJECTS}

TIMETABLE = {
    "Monday": [
        ("09:10 - 10:00", "DSTL", "BCS-303", "class"),
        ("10:00 - 10:50", "COA", "BCS-302", "class"),
        ("10:50 - 10:55", "SHORT BREAK", "", "break"),
        ("10:55 - 11:45", "UHV", "BVE-301", "class"),
        ("11:45 - 12:35", "DS", "BCS-301", "class"),
        ("12:35 - 01:25", "LUNCH", "", "break"),
        ("01:25 - 03:05", "DS LAB + COA LAB", "BCS-351 + BCS-352", "class"),
        ("03:05 - 03:10", "SHORT BREAK", "", "break"),
        ("03:10 - 04:00", "DE", "BOE-310", "class"),
        ("04:00 - 04:50", "LIBRARY", "", "activity"),
    ],
    "Tuesday": [
        ("09:10 - 10:50", "DS LAB + COA LAB / OB LAB", "BCS-351 + BCS-352", "class"),
        ("10:50 - 10:55", "SHORT BREAK", "", "break"),
        ("10:55 - 11:45", "DE", "BOE-310", "class"),
        ("11:45 - 12:35", "UHV", "BVE-301", "class"),
        ("12:35 - 01:25", "LUNCH", "", "break"),
        ("01:25 - 02:15", "COA (T) (L1+L2)", "BCS-302", "class"),
        ("02:15 - 03:05", "DS", "BCS-301", "class"),
        ("03:05 - 03:10", "SHORT BREAK", "", "break"),
        ("03:10 - 04:00", "CS", "BCC-301", "class"),
        ("04:00 - 04:50", "LIBRARY", "", "activity"),
    ],
    "Wednesday": [
        ("09:10 - 10:00", "DE", "BOE-310", "class"),
        ("10:00 - 10:50", "DS", "BCS-301", "class"),
        ("10:50 - 10:55", "SHORT BREAK", "", "break"),
        ("10:55 - 11:45", "DSTL (T) (L1+L2)", "BCS-303", "class"),
        ("11:45 - 12:35", "COA", "BCS-302", "class"),
        ("12:35 - 01:25", "LUNCH", "", "break"),
        ("01:25 - 03:05", "WDW LAB + MP LAB", "BCS-353 + BCC-351", "class"),
        ("03:05 - 03:10", "SHORT BREAK", "", "break"),
        ("03:10 - 04:00", "MENTOR-MENTEE", "", "activity"),
        ("04:00 - 04:50", "LIBRARY", "", "activity"),
    ],
    "Thursday": [
        ("09:10 - 10:50", "WDW LAB + iOS LAB", "BCS-353 + NA", "class"),
        ("10:50 - 10:55", "SHORT BREAK", "", "break"),
        ("10:55 - 11:45", "DE", "BOE-310", "class"),
        ("11:45 - 12:35", "COA", "BCS-302", "class"),
        ("12:35 - 01:25", "LUNCH", "", "break"),
        ("01:25 - 02:15", "DSTL", "BCS-303", "class"),
        ("02:15 - 03:05", "UHV (T) (L1+L2)", "BVE-301", "class"),
        ("03:05 - 03:10", "SHORT BREAK", "", "break"),
        ("03:10 - 04:00", "DS", "BCS-301", "class"),
        ("04:00 - 04:50", "MENTOR-MENTEE", "", "activity"),
    ],
    "Friday": [
        ("09:10 - 10:00", "COA", "BCS-302", "class"),
        ("10:00 - 10:50", "CS", "BCC-301", "class"),
        ("10:50 - 10:55", "SHORT BREAK", "", "break"),
        ("10:55 - 11:45", "DSTL", "BCS-303", "class"),
        ("11:45 - 12:35", "DS (T) (L1+L2)", "BCS-301", "class"),
        ("12:35 - 01:25", "LUNCH", "", "break"),
        ("01:25 - 02:15", "DSTL", "BCS-303", "class"),
        ("02:15 - 03:05", "DE (T) (L1+L2)", "BOE-310", "class"),
        ("03:05 - 03:10", "SHORT BREAK", "", "break"),
        ("03:10 - 04:50", "MP LAB + iOS LAB", "BCC-351 + NA", "class"),
    ],
}


def subject_details(codes):
    return [SUBJECT_BY_CODE[code] for code in codes.split(" + ") if code in SUBJECT_BY_CODE]


def timetable_for_template():
    return {
        day: [
            {
                "time": time,
                "label": label,
                "code": code,
                "kind": kind,
            }
            for time, label, code, kind in entries
        ]
        for day, entries in TIMETABLE.items()
    }

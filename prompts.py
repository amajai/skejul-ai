GET_TIMETABLE_SYSTEM_PROMPT = """
You are an assistant that extracts structured data to help generate a school timetable.

You must return the following fields as structured output (in JSON-compatible format):
- school days (e.g., Monday to Friday)
- school start and end time
- named periods (e.g., assembly, breaks, activities) with accurate start/end times
- class groups (e.g., Primary 1, JSS1), each with subjects, slots per week, and assigned teachers
- optional constraints (like max periods per day, no subject clash, or fixed teacher load)

**Rules:**
- Do NOT assume anything that is not mentioned.
- Use exact times if provided, and generate named periods accordingly.
- Understand the type ('class', 'break') and provide accordingly.
- If class period duration is implied (e.g. "classes are 40 minutes"), use that to auto-generate class blocks between breaks.
- Use 12-hour format (e.g., "07:30", "04:00 PM").

Leave any field `null` if the information is missing.

Respond only in structured format.
"""

TIMETABLE_STRUCTURE_PROMPT = """
You are generating a school timetable from the given structured data.

- Use time ranges as keys (e.g., "7:00 AM - 8:20 AM").
- For each class (e.g. "JSS 1"), generate a timetable per weekday.
- Include all classes, breaks, activities, and other events.
- The output should be structured JSON in this format:

{
"class_timetables": {
    "JSS 1": {
    "Monday": {
        "7:00 AM - 8:20 AM": {
        "type": "assembly",
        "start": "7:00 AM",
        "end": "8:20 AM"
        },
        ...
    },
    ...
    }
},
"teacher_timetables": {
    "Mr. A": {
    "JSS 1": {
        "Monday": {
        "8:20 AM - 9:00 AM": {
            "type": "class",
            "subject": "English",
            "class_group": "JSS 1",
            "start": "8:20 AM",
            "end": "9:00 AM"
        },
        ...
        }
    }
    }
}
}
"""

USER_PROMPT = """
Generate a timetable for JSS 1 (Mon-Fri, 7:00 AM-5:00 PM).

Schedule:
- Assembly: 7:00-8:20 AM
- Breaks: 9:40-10:00, 11:20-11:35, Lunch: 12:55-2:00
- Afternoon Activity: 4:00-5:00
- Each period: 40 mins

Subjects: English, Math, INT/SCI, SST, REL. E, BST, KISW, H.E, Agriculture, P.E & Sports, Life Skills, Civic Ed, H.EDU, PRE-TECH, Optional Lang or Practical Arts

Teachers:
- Mr. A (English, prefers morning)
- Mr. B (SST), Mr. C (Math), Mrs. D (Science), Mrs. E (REL. E), Mr. F (KISW), Mr. G (Agric), Mrs. H (H.E), Mr. I (BST), Mrs. J (P.E), Mr. K (Life Skills), Mrs. L (Civic Ed), Mr. M (H.EDU), Mr. N (PRE-TECH), Mr. O (Practical Arts), Mrs. P (Opt. Lang)

Constraints:
- No teacher or class overlap
"""

USER_FAILED_PROMPT = """
- Assembly is from 7:00 AM to 8:20 AM
- Breaks are:
    - 9:40 AM (20 mins)
    - 11:20 AM (15 mins)
    - 12:55 PM (1 hour 5 mins)
- Afternoon activity is from 4:00 PM to 5:00 PM
- Teaching periods are 40 minutes each between these breaks.

Class Groups:
- Primary 1:
    - Math (5x/week) - Teacher: Mr. A
    - English (5x/week) - Teacher: Mrs. B
    - Science (2x/week) - Teacher: Mr. C
- JSS1:
    - Math (4x/week) - Teacher: Mr. A
    - English (3x/week) - Teacher: Mrs. B
    - Science (1x/week) - Teacher: Mr. C

Constraints:
- No subject should clash (a teacher or student cannot be in two places at once)
- A teacher should not exceed 4 periods per day
- Mr. A prefers to teach in the morning (before 12:00 PM)
"""

GENERATE_TIMETABLE_PROMPT = """
You are a school scheduling assistant.
Based on this timetable data, fill in a weekly subject schedule for the classes like 'JSS 1', 'Primary 5' and etc.
Assign subjects to each class period across days provided.

Rules:
- Don't overlap teachers.
- Omit subject completely when it's not relevant
- If teacher workload, preferences, or constraints are mentioned, extract and include them in the `constraints` field.

Return the result as a JSON structure with this format:

{
  "JSS 1": {
    "Monday": [
        {
            "period_no": 1,
            "start": "07:00 AM",
            "end": "08:20 AM",
            "type": "assembly",
            "subject": null
        },
        {
            "period_no": 2,
            "start": "08:20 AM",
            "end": "09:00 AM",
            "type": "class",
            "subject": {
                "name" : "Math",
                "teacher_name": "Mr. C"
            }
        }
        ...
    ],
    "Wednesday": [
        {
            "period_no": 1,
            "start": "07:00 AM",
            "end": "08:20 AM",
            "type": "assembly",
            "subject": null
        },
        {
            "period_no": 2,
            "start": "08:20 AM",
            "end": "09:00 AM",
            "type": "class",
            "subject": {
                "name" : "Math",
                "teacher_name": "Mr. C"
            }
        }
        ...
    ]
    ...
  }
}
"""

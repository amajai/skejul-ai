# =============================================================================
# USER SCENARIO PROMPTS
# =============================================================================

USER_PROMPT = """
Generate a timetable for JSS 3, SS1, and SS2 (Mon-Fri, 7:20 AM-3:50 PM).

Schedule Structure

Assembly: 7:20-8:00 AM
Break 1: 10:20-10:30 AM
Break 2: 12:20-12:50 PM
Each period: 40 minutes

Subjects

JSS 3:
Mathematics, English, Basic Science, Arabic, Literature (LIT), Civic Education, Social Studies, ICT, Physical Health Education (P.H.E), Basic Technology (B. TECH)

SS1:
Mathematics, English, Biology, Chemistry, Physics, Literature, Government, Civic Education, ICT, Arabic, P.H.E, Economics, Social Studies

SS2:
Mathematics, English, Biology, Chemistry, Physics, Literature, Government, Civic Education, ICT, Arabic, P.H.E, Economics, Geography

Teachers

Mrs. A - English (teaches JSS 3, SS1, SS2; prefers morning periods)
Mr. B - Mathematics (teaches all 3 classes; flexible)
Mrs. C - Basic Science/Biology (teaches JSS 3 + SS1 + SS2; must avoid overlaps)
Mr. D - Arabic (teaches all 3; prefers after morning break)
Mr. F - ICT (teaches all 3; max 2 classes/day)
Mrs. G - P.H.E (teaches all 3; prefers afternoons)
Mr. H - Literature (teaches JSS 3, SS1 & SS2; limited to 3 lessons/day)
Mrs. I - Basic Technology (JSS 3 only)
Mr. J - Civic Education (teaches all 3 levels; avoid back-to-back load)
Mrs. K - Economics/Geography (teaches SS1 & SS2 only)
Mr. L - Chemistry/Physics (teaches SS1 & SS2 only)
Mr. M - Government/Social Studies (teaches JSS 3, SS1, SS2; spread evenly)

Constraints

No teacher or class overlap during the same time slot.
Teacher preferences and max load limits must be respected.
Core subjects (English, Math, Science, Arabic) appear ≥4x per week for each class.
Literature, Civic, and Social Studies should not all appear on the same day for one class.
Advanced sciences (Physics, Chemistry, Biology) must be balanced across SS1 & SS2.
Assembly every day before classes.
"""

USER_PROMPT_2 = """
Generate a timetable for Primary 1, Primary 3, and JSS 1 (Mon-Fri, 7:00 AM-5:00 PM).

Schedule:

Assembly: 7:00-8:00 AM
Breaks: 9:20-9:40 AM, 11:00-11:15 AM
Lunch: 1:00-2:00 PM
Afternoon Session (Clubs / Story / Prep / Sports): 4:00-5:00 PM
Each period: 40 minutes

Subjects:

Primary 1 & Primary 3:
English, Math, Science, Social Studies, Religious Ed, Art, Music, Health Ed, Life Skills, P.E., Story Time, Reading

JSS 1:
English, Math, Basic Science, Social Studies, Religious Ed, Agric, Business Studies, Civic Ed, Basic Tech, Life Skills, Computer Studies, P.E., Optional Lang (French or Local Lang)

Teachers (shared across classes):

Mrs. A - English (teaches Primary 1, Primary 3, and JSS 1, prefers morning)

Mr. B - Math (teaches all 3 classes, flexible schedule)

Mrs. C - Science (Primary 1 & 3), Basic Science (JSS 1)

Mr. D - Social Studies (Primary 3 & JSS 1)

Mrs. E - Religious Ed (all classes)

Mr. F - Art & Music (Primary 1 & 3)

Mrs. G - Health Ed & Life Skills (Primary 1, 3, and JSS 1)

Mr. H - P.E. (all classes)

Mrs. I - Reading & Story Time (Primary 1 & 3)

Mr. J - Business Studies (JSS 1)

Mrs. K - Basic Tech & Agric (JSS 1)

Mr. L - Civic Ed (JSS 1)

Mrs. M - Computer Studies (JSS 1)

Mr. N - French / Optional Lang (JSS 1 only)

Constraints:

No teacher or class overlap

Teacher preferences must be respected (e.g., Mrs. A prefers morning periods only)

Core subjects (English, Math, Science) appear at least 3x/week

Optional/Creative subjects like Art, Music, Story Time appear -2x/week

Afternoon sessions are for non-core activities (clubs, revision, sports)
"""

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

GET_TIMETABLE_SYSTEM_PROMPT = """
You are an expert school assistant that extracts structured data to help generate a school timetable.

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
- For period types, use ONLY these values: 'class', 'break', 'prayer', 'activity', 'lunch', 'assembly', 'other'
- Map similar terms intelligently: 'extended activities' -> 'activity', 'afternoon session' -> 'activity', 'clubs' -> 'activity', 'sports' -> 'activity'

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

GENERATE_SINGLE_GRADE_PROMPT = """
You are a school scheduling assistant generating a timetable for ONE specific class_group.

IMPORTANT CONSTRAINTS:
- The 'teacher_constraints' field shows when teachers are already busy with other class_groups
- NEVER schedule a teacher during their busy times
- If a teacher is unavailable, either skip that subject or use "None" for teacher_name

Based on this data, create a weekly schedule for the single class group provided.

Rules:
- Respect ALL teacher_constraints (teachers cannot be in two places at once)
- Fill all available periods with appropriate subjects
- Follow subject frequency requirements if specified
- Return ONLY the single class_group's timetable

Return the result as a JSON structure with this format:

{
  "Class_Group Name": {
    "Monday": [
        {
            "period_no": 1,
            "start": "07:00 AM",
            "end": "08:00 AM",
            "type": "assembly",
            "subject": null
        },
        {
            "period_no": 2,
            "start": "08:00 AM",
            "end": "08:40 AM",
            "type": "class",
            "subject": {
                "name" : "Math",
                "teacher_name": "Mr. B"
            }
        }
        ...
    ]
    ...
  }
}
"""

GENERATE_TIMETABLE_PROMPT = """
You are a school scheduling assistant.
Based on this timetable data, fill in a weekly subject schedule for the class_groups like 'JSS 1', 'Primary 5' and etc.
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

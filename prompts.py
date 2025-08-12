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
OLD_USER_FAILED_PROMPT = """
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

USER_PROMPT = """
Generate a timetable for JSS 1, JSS 2, and Primary 5 (Mon-Fri, 7:20 AM-3:50 PM) following Amana Legacy Foundation Academy structure.

Schedule Structure:
- Assembly: 7:20-8:00 AM
- Morning Break: 10:20-10:30 AM  
- Quran Break: 11:10-11:50 AM
- Afternoon Break: 12:20-12:50 PM
- Lunch Break: 1:20-1:50 PM
- Practice Session: 2:30-3:10 PM
- Extended Activities: 3:10-3:50 PM

Each period: 40 minutes

Subjects:

JSS 1 & JSS 2:
Mathematics, English, Basic Science, Arabic, Literature (LIT), Religious & National Values (R.N.V), Hadith, ICT, Physical Health Education (P.H.E), Basic Technology (B. TECH), Civic Education, Tajwid, Social Studies, Computer Studies

Primary 5:
Mathematics, English, Basic Science, Arabic, Hadith, Azkar, Social Studies, Religious Education, ICT, Physical Education, Art & Craft, Life Skills, Reading

Teachers (shared across classes):

Mrs. A - English (teaches JSS 1, JSS 2, and Primary 5, prefers morning periods)
Mr. B - Mathematics (teaches all 3 classes, flexible schedule)
Mrs. C - Basic Science (all classes)
Mr. D - Arabic (all classes, prefers after morning break)
Mrs. E - Religious Ed/R.N.V/Hadith (all classes)
Mr. F - ICT/Computer Studies (all classes)
Mrs. G - P.H.E/Physical Education (all classes)
Mr. H - Literature/Social Studies (JSS 1 & JSS 2)
Mrs. I - Basic Technology (JSS 1 & JSS 2)
Mr. J - Civic Education/Tajwid (JSS 1 & JSS 2)
Mrs. K - Art & Craft/Life Skills (Primary 5)
Mr. L - Azkar/Reading (Primary 5)

Constraints:
- No teacher or class overlap during the same time slot
- Teacher preferences must be respected
- Core subjects (English, Mathematics, Arabic, Basic Science) appear at least 4x/week
- Religious subjects (Hadith, R.N.V, Tajwid, Azkar) distributed throughout the week
- Quran break period (11:10-11:50 AM) must be maintained for Islamic studies
- Practice sessions (2:30-3:10 PM) for mathematics competitions and spelling bee
- Extended activities period for clubs, sports, and enrichment programs
- Assembly period every morning before academic sessions begin
"""

USER_PROMPT_2 = """
Generate a timetable for Primary 2 to SS2 (Mon-Fri, 7:00 AM-5:00 PM).

Schedule:
Assembly: 7:00-8:00 AM
Breaks: 9:20-9:40 AM, 11:00-11:15 AM
Lunch: 1:00-2:00 PM
Afternoon Clubs / Prep / Sports: 4:00-5:00 PM
Each period: 40 minutes

Subjects (vary by level):

Primary 2 - Primary 6:
English, Math, Science, Social Studies, Religious Ed, Art, Music, Life Skills, Health Ed, P.E., Reading, Story Time

JSS 1 - JSS 3:
English, Math, Basic Science, Basic Tech, Social Studies, Agric, Civic Ed, Religious Ed, Business Studies, French or Indigenous Lang, P.E., Life Skills, Computer Studies

SS1 - SS2:
English, Math, Civic Ed, ICT, P.E.

Science: Physics, Chemistry, Biology, Further Math, Agric

Art: Literature, CRS/IRS, Government, History, Languages (French, Indigenous)

Commercial: Economics, Accounting, Commerce, Office Practice

Teachers:

Mrs. A (English - all levels)
Mr. B (Math - all levels)
Mrs. C (Science - Primary & JSS)
Mr. D (Basic Tech - JSS)
Mrs. E (Social Studies - Primary & JSS)
Mr. F (Civic Ed - JSS & SS)
Mrs. G (Religious Ed - all levels)
Mr. H (Agric - JSS & SS)
Mrs. I (Art & Music - Primary only)
Mr. J (P.E. - all levels)
Mr. K (Life Skills - Primary & JSS)
Mrs. L (Computer Studies - JSS & SS)
Mr. M (French & Langs - JSS & SS)
Mrs. N (Physics, Chemistry - SS)
Mr. O (Biology - SS)
Mrs. P (Literature, Government - SS)
Mr. Q (Economics, Commerce - SS)
Mr. R (Business Studies - JSS)
Mrs. S (ICT - SS)
Mr. T (History - SS)
Mrs. U (Accounting - SS)

Constraints:
No teacher or class overlaps allowed
Teachers' preferences must be respected (e.g., Mrs. A prefers morning classes)
Core subjects should occur at least 3x/week
Language or elective/practical classes 1-2x/week
Clubs and non-academic activities limited to last period or 4-5 PM

Class groups: Primary 2, 3, 4, 5, 6, JSS 1-3, SS1, SS2
"""

USER_PROMPT_3 = """
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

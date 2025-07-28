from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from dotenv import load_dotenv

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Dict, Optional, Set, Tuple, Union, Literal
from datetime import time, datetime
from enum import Enum
from langchain_core.messages import SystemMessage, HumanMessage
from pprint import pprint
import json

load_dotenv()

DayOfWeek = Literal["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
PeriodType = Literal["class", "break", "prayer", "activity", "lunch", "assembly", "other"]

class SubjectDefinition(BaseModel):
    name: str = Field(None, description="Name of the subject, e.g., Mathematics")
    teacher: str = Field(None, description="Name of the teacher assigned to this subject")
    slots_per_week: int = Field(None, description="How many periods per week for this subject")


class ClassGroup(BaseModel):
    name: str = Field(None, description="Name of the class group, e.g., 'JSS1 Red'")
    subjects: Optional[List[SubjectDefinition]] = Field(None, description="Subjects and their weekly slots for this class group")


class TimePeriod(BaseModel):
    type: Optional[PeriodType] = Field(
        None, description="Type of period: class, break, prayer, activity, etc."
    )
    start: str = Field(None, description="Start time in HH:MM format")
    end: str = Field(None, description="End time in HH:MM format")


class SchoolData(BaseModel):
    days: Optional[List[DayOfWeek]] = Field(None, description="List of school days")
    start_time: Optional[str] = Field(None, description="School start time (e.g., '7:20 AM', '07:20')")
    end_time: Optional[str] = Field(None, description="School end time (e.g., '3:50 PM', '15:50')")
    periods: Optional[List[TimePeriod]] = Field(None, description="Each subject period with start and end time")
    class_groups: Optional[List[ClassGroup]] = Field(
        None,
        description="List of classes/grades (E.g., ['Primary 1', 'Primary 2', 'SS1A'])"
        " with their subjects, teachers, and slot allocations"
    )


# LLM setup
llm = init_chat_model(
    model="qwen/qwen3-32b",
    model_provider="groq", 
    temperature=0
)

structured_llm = llm.with_structured_output(SchoolData)

# System + User prompt
response: SchoolData = structured_llm.invoke([
    SystemMessage(content="""
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
        - If class period duration is implied (e.g. "classes are 40 minutes"), use that to auto-generate class blocks between breaks.
        - If teacher workload, preferences, or constraints are mentioned, extract and include them in the `constraints` field.
        - Use 12-hour format (e.g., "07:30", "04:00 PM").

        Leave any field `null` if the information is missing.

        Respond only in structured format.
        """),
    HumanMessage(content="""
        The school runs Monday to Friday, from 7:00 AM to 5:00 PM.

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
        """)
    ])

# print(response)
json_str = json.dumps(response.model_dump(), indent=2)
print(json_str)

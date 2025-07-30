from pydantic import BaseModel, Field
from typing import List, TypedDict, Optional, Literal


# Type aliases
DayOfWeek = Literal["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
PeriodType = Literal["class", "break", "prayer", "activity", "lunch", "assembly", "other"]

# PYDANTIC MODELS
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


class PeriodEntry(BaseModel):
    type: PeriodType
    subject: Optional[str] = None  # Only relevant for "class"
    teacher: Optional[str] = None  # Only for "class"
    class_group: Optional[str] = None  # Only for teacher timetable
    start: str
    end: str


class TimetableData(BaseModel):
    days: Optional[List[DayOfWeek]] = Field(None, description="List of school days")
    start_time: Optional[str] = Field(None, description="School start time (e.g., '7:20 AM', '07:20')")
    end_time: Optional[str] = Field(None, description="School end time (e.g., '3:50 PM', '15:50')")
    periods: Optional[List[TimePeriod]] = Field(None, description="Each subject period with start and end time")
    class_groups: Optional[List[ClassGroup]] = Field(
        None,
        description="List of classes/grades (E.g., ['Primary 1', 'Primary 2', 'SS1A'])"
        " with their subjects, teachers, and slot allocations"
    )


# STATE DEFINITIONS
class TimeTableState(TypedDict):
    """State structure for the timetable generation workflow."""
    input: str
    timetable_data: TimetableData
    class_timetables: dict
    attempt: int
    validation_errors: list[str]
    validated: bool
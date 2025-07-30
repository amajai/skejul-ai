import json
from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq

# Local imports
from models import TimeTableState, TimetableData

from prompts import (
    GET_TIMETABLE_SYSTEM_PROMPT,
    GENERATE_TIMETABLE_PROMPT,
    USER_PROMPT
)

from utils import remove_markdown_code_blocks

load_dotenv()

# Initialize language model
llm_gemini = init_chat_model(
    model="gemini-2.5-flash",
    model_provider="google_genai", 
    temperature=0
)

llm_kimi_k2 = ChatGroq(
    model="moonshotai/kimi-k2-instruct",
    temperature=0.1,
    max_tokens=16000
)


structured_llm = llm_gemini.with_structured_output(TimetableData) 

# WORKFLOW FUNCTIONS
def get_timetable_data(state: TimeTableState) -> TimeTableState:
    """Extract structured timetable data from user input."""
    print("Extracting data into structured table...")
    structured_llm = llm_gemini.with_structured_output(TimetableData)
    res: TimetableData = structured_llm.invoke([
        SystemMessage(content=GET_TIMETABLE_SYSTEM_PROMPT),
        HumanMessage(content=state["input"])
    ])
    print("✅ Done extracting data!")

    state["timetable_data"] = res.model_dump()
    return state


def validate_timetable_data(state: TimeTableState) -> TimeTableState:
    """Validate that required timetable data is present."""
    missing = []
    data = state["timetable_data"]

    if not data:
        state['validated'] = False
        state['validation_errors'] = ["Missing timetable data entirely"]
        return state

    if not data['days']:
        missing.append("school days")
    if not data['start_time'] or not data['end_time']:
        missing.append("school start/end time")
    if not data['periods']:
        missing.append("named periods (e.g., breaks, assembly)")
    if not data['class_groups']:
        missing.append("class groups")

    state['validated'] = len(missing) == 0
    state['validation_errors'] = missing if missing else None
    return state


def route_on_validation(state: TimeTableState) -> str:
    """Route workflow based on validation results."""
    print("Validating the date...")

    if not state["validated"]:
        print('entering invalid')
        return "invalid"
    print("✅ Data valid!")
    
    return "valid"


def invalid(state: TimeTableState):
    """Handle invalid state - display missing data."""
    print("❌ Data not valid!")

    print("Invalid state encountered!")
    print("Missing:", state['validation_errors'])
    return state


def abort(state: TimeTableState):
    """Abort workflow after too many attempts."""
    print("Too many attempts. Aborting.")
    return state


def generate_timetable(state: TimeTableState):
    """Generate timetables for all the class group available"""
    print("Generating timetables...")

    result = llm_kimi_k2.invoke([
        SystemMessage(content=GENERATE_TIMETABLE_PROMPT),
        HumanMessage(content='{}'.format(state['timetable_data']))
    ])
    print("✅ Done generating timetables!")
    state['class_timetables'] = json.loads(remove_markdown_code_blocks(result.content))
    return state


# WORKFLOW SETUP
workflow = StateGraph(TimeTableState)

# Add nodes
workflow.add_node('get_timetable_data', get_timetable_data)
workflow.add_node('validate_timetable_data', validate_timetable_data)
workflow.add_node('invalid', invalid)
workflow.add_node('generate_timetable', generate_timetable)

# Add edges
workflow.add_edge(START, 'get_timetable_data')
workflow.add_edge('get_timetable_data', 'validate_timetable_data')
workflow.add_conditional_edges(
    'validate_timetable_data',
    route_on_validation,
    {
        "valid": 'generate_timetable',
        "invalid": "invalid"
    }
)
workflow.add_edge('generate_timetable', END)


# Compile workflow
graph = workflow.compile()

if __name__ == "__main__":
    # Execute workflow
    result = graph.invoke({"input": USER_PROMPT})
    
    # Output results
    print(result['class_timetables'])
    

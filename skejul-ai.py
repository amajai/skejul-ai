import json
import os
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
    GENERATE_SINGLE_GRADE_PROMPT,
    USER_PROMPT
)
from utils import remove_markdown_code_blocks

load_dotenv()

# Initialize language models from environment variables
def create_structured_llm():
    provider = os.getenv("STRUCTURED_LLM_PROVIDER", "google_genai")
    model = os.getenv("STRUCTURED_LLM_MODEL", "gemini-2.5-flash")
    temperature = float(os.getenv("STRUCTURED_LLM_TEMPERATURE", "0"))
    
    return init_chat_model(
        model=model,
        model_provider=provider,
        temperature=temperature
    )

def create_llm():
    provider = os.getenv("LLM_PROVIDER", "google_genai")
    model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))

    return init_chat_model(
        model=model,
        model_provider=provider,
        temperature=temperature
    )

# Initialize LLMs
structured_llm = create_structured_llm()
llm = create_llm() 

# WORKFLOW FUNCTIONS
def get_timetable_data(state: TimeTableState) -> TimeTableState:
    """Extract structured timetable data from user input."""
    print("Extracting data into structured table...")
    structured_output_llm = structured_llm.with_structured_output(TimetableData)
    response: TimetableData = structured_output_llm.invoke([
        SystemMessage(content=GET_TIMETABLE_SYSTEM_PROMPT),
        HumanMessage(content=state["input"])
    ])
    print("✅ Done extracting data!")

    state["timetable_data"] = response.model_dump()
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


def initialize_sequential_processing(state: TimeTableState) -> TimeTableState:
    """Initialize the sequential class_group processing"""
    print("🔄 Initializing sequential processing...")
    
    # Extract all class_group names from timetable_data
    all_class_groups = [class_group['name'] for class_group in state['timetable_data']['class_groups']]
    
    state['all_grades'] = all_class_groups
    state['current_grade_index'] = 0
    state['teacher_availability'] = {}  # Start with no teacher constraints
    state['class_timetables'] = {}  # Initialize empty timetables
    
    print(f"📋 Processing {len(all_class_groups)} class_groups: {', '.join(all_class_groups)}")
    return state


def generate_single_class_group(state: TimeTableState) -> TimeTableState:
    """Generate timetable for current class_group only"""
    current_class_group = state['all_grades'][state['current_grade_index']]
    print(f"🎯 Generating timetable for {current_class_group}...")
    
    # Find current class_group's data
    current_class_group_data = None
    for class_group in state['timetable_data']['class_groups']:
        if class_group['name'] == current_class_group:
            current_class_group_data = class_group
            break
    
    # Create single-class_group prompt data
    single_class_group_data = {
        'days': state['timetable_data']['days'],
        'start_time': state['timetable_data']['start_time'],
        'end_time': state['timetable_data']['end_time'],
        'periods': state['timetable_data']['periods'],
        'class_groups': [current_class_group_data], 
        'teacher_constraints': state['teacher_availability']
    }
    
    # Generate timetable for this class_group
    result = llm.invoke([
        SystemMessage(content=GENERATE_SINGLE_GRADE_PROMPT),
        HumanMessage(content=json.dumps(single_class_group_data, indent=2))
    ])
    
    # Parse result and add to state
    class_group_timetable = json.loads(remove_markdown_code_blocks(result.content))
    state['class_timetables'][current_class_group] = class_group_timetable[current_class_group]
    
    print(f"✅ Done generating {current_class_group}!")
    return state


def update_teacher_availability(state: TimeTableState) -> TimeTableState:
    """Extract teacher busy times from newly generated timetable"""
    current_class_group = state['all_grades'][state['current_grade_index']]
    print(f"📝 Updating teacher availability from {current_class_group}...")
    
    class_group_schedule = state['class_timetables'][current_class_group]
    
    # Extract teacher busy times
    for day, periods in class_group_schedule.items():
        for period in periods:
            if period['type'] == 'class' and period.get('subject', {}).get('teacher_name'):
                teacher = period['subject']['teacher_name']
                time_slot = f"{day} {period['start']}-{period['end']}"
                
                if teacher not in state['teacher_availability']:
                    state['teacher_availability'][teacher] = []
                state['teacher_availability'][teacher].append(time_slot)    
    return state


def increment_class_group_index(state: TimeTableState) -> TimeTableState:
    """Increment the current class_group index"""
    state['current_grade_index'] += 1
    print(f"📈 Moving to index {state['current_grade_index']}")
    return state


def route_next_class_group(state: TimeTableState) -> str:
    """Check if more class_groups need processing"""
    if state['current_grade_index'] < len(state['all_grades']):
        next_class_group = state['all_grades'][state['current_grade_index']]
        print(f"➡️  Next class_group: {next_class_group}")
        return "continue"
    else:
        print("🏁 All class_groups processed!")
        return "complete"


# WORKFLOW SETUP
workflow = StateGraph(TimeTableState)

# Add nodes
workflow.add_node('get_timetable_data', get_timetable_data)
workflow.add_node('validate_timetable_data', validate_timetable_data)
workflow.add_node('invalid', invalid)
workflow.add_node('initialize_sequential', initialize_sequential_processing)
workflow.add_node('generate_single_class_group', generate_single_class_group)
workflow.add_node('update_teacher_availability', update_teacher_availability)
workflow.add_node('increment_class_group', increment_class_group_index)

# Add edges
workflow.add_edge(START, 'get_timetable_data')
workflow.add_edge('get_timetable_data', 'validate_timetable_data')
workflow.add_conditional_edges(
    'validate_timetable_data',
    route_on_validation,
    {
        "valid": 'initialize_sequential',
        "invalid": "invalid"
    }
)
workflow.add_edge('initialize_sequential', 'generate_single_class_group')
workflow.add_edge('generate_single_class_group', 'update_teacher_availability')
workflow.add_edge('update_teacher_availability', 'increment_class_group')
workflow.add_conditional_edges(
    'increment_class_group',
    route_next_class_group,
    {
        "continue": "generate_single_class_group",
        "complete": END
    }
)


# Compile workflow
graph = workflow.compile()

def generate_mermaid_diagram():
    """Generate horizontal Mermaid diagram for the workflow"""
    print(graph.get_graph().draw_mermaid())

if __name__ == "__main__":
    # Uncomment to see the Mermaid diagram
    # generate_mermaid_diagram()
    
    # Execute workflow
    result = graph.invoke({"input": USER_PROMPT})
    
    # Output results
    print(result['class_timetables'])
    

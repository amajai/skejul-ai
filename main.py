import json
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq

# Local imports
from models import TimeTableState, TimetableData
from niceterminalui import (
    print_banner, print_step, print_success, print_warning, print_error, 
    print_info, print_result_box, print_completion_message, print_table,
    print_status_panel, print_alert
)

from prompts import (
    GET_TIMETABLE_SYSTEM_PROMPT,
    GENERATE_TIMETABLE_PROMPT,
    GENERATE_SINGLE_GRADE_PROMPT,
    USER_PROMPT
)
from utils import remove_markdown_code_blocks
from create_timetable_image import create_timetable_image

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
    print_step("Extracting data into structured table", "📊")
    structured_output_llm = structured_llm.with_structured_output(TimetableData)
    response: TimetableData = structured_output_llm.invoke([
        SystemMessage(content=GET_TIMETABLE_SYSTEM_PROMPT),
        HumanMessage(content=state["input"])
    ])
    print_success("Done extracting data!")

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

    # Display validation status
    validation_status = {
        "School Days": "✅ Valid" if data.get('days') else "❌ Missing",
        "Time Range": "✅ Valid" if (data.get('start_time') and data.get('end_time')) else "❌ Missing",
        "Periods": "✅ Valid" if data.get('periods') else "❌ Missing",
        "Class Groups": "✅ Valid" if data.get('class_groups') else "❌ Missing"
    }
    print_status_panel("Data Validation Results", validation_status)

    state['validated'] = len(missing) == 0
    state['validation_errors'] = missing if missing else None
    return state


def route_on_validation(state: TimeTableState) -> str:
    """Route workflow based on validation results."""
    print_step("Validating the data", "🔍")

    if not state["validated"]:
        print_info('Entering invalid state')
        return "invalid"
    print_success("Data valid!")
    
    return "valid"


def invalid(state: TimeTableState):
    """Handle invalid state - display missing data."""
    print_error("Data not valid!")
    print_alert("Invalid state encountered!", "error")
    missing_items = "\n".join([f"• {item}" for item in state['validation_errors']])
    print_result_box("Missing Data", missing_items)
    return state


def abort(state: TimeTableState):
    """Abort workflow after too many attempts."""
    print_error("Too many attempts. Aborting.")
    return state


def initialize_sequential_processing(state: TimeTableState) -> TimeTableState:
    """Initialize the sequential class_group processing"""
    print_step("Initializing sequential processing", "🔄")
    
    # Extract all class_group names from timetable_data
    all_class_groups = [class_group['name'] for class_group in state['timetable_data']['class_groups']]
    
    state['all_grades'] = all_class_groups
    state['current_grade_index'] = 0
    state['teacher_availability'] = {}  # Start with no teacher constraints
    state['class_timetables'] = {}  # Initialize empty timetables
    state['class_timetables_df'] = {} 

    print_info(f"Processing {len(all_class_groups)} class_groups: {', '.join(all_class_groups)}")
    return state


def generate_single_class_group(state: TimeTableState) -> TimeTableState:
    """Generate timetable for current class_group only"""
    current_class_group = state['all_grades'][state['current_grade_index']]
    print_step(f"Generating timetable for {current_class_group}", "🎯")
    
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
    
    print_success(f"Done generating {current_class_group}!")
    return state


def update_teacher_availability(state: TimeTableState) -> TimeTableState:
    """Extract teacher busy times from newly generated timetable"""
    current_class_group = state['all_grades'][state['current_grade_index']]
    print_step(f"Updating teacher availability from {current_class_group}", "📝")
    
    class_group_schedule = state['class_timetables'][current_class_group]
    
    print(class_group_schedule.items())
    # Extract teacher busy times
    for day, periods in class_group_schedule.items():
        for period in periods:
            subject = period.get('subject')
            if period['type'] == 'class' and subject and subject.get('teacher_name'):
                teacher = subject['teacher_name']
                time_slot = f"{day} {period['start']}-{period['end']}"
                
                if teacher not in state['teacher_availability']:
                    state['teacher_availability'][teacher] = []
                state['teacher_availability'][teacher].append(time_slot)    
    return state


def increment_class_group_index(state: TimeTableState) -> TimeTableState:
    """Increment the current class_group index"""
    state['current_grade_index'] += 1
    print_info(f"Moving to index {state['current_grade_index']}")
    return state


def route_next_class_group(state: TimeTableState) -> str:
    """Check if more class_groups need processing"""
    if state['current_grade_index'] < len(state['all_grades']):
        next_class_group = state['all_grades'][state['current_grade_index']]
        print_info(f"Next class_group: {next_class_group}")
        return "continue"
    else:
        print_success("All class_groups processed!")
        return "convert_to_dataframes"


def convert_to_dataframes(state: TimeTableState) -> TimeTableState:
    """Convert class timetables to pandas DataFrames"""
    print_step("Converting timetables to DataFrames", "📊")
    
    all_classes = state['class_timetables']
    
    # Step 1: Collect all unique time slots used across all classes
    time_slots_set = set()
    
    for class_data in all_classes.values():
        for day_periods in class_data.values():
            for period in day_periods:
                time_range = f"{period['start']} - {period['end']}"
                time_slots_set.add(time_range)
    
    # Step 2: Sort time slots chronologically
    def time_key(time_range):
        start = time_range.split(" - ")[0]
        return datetime.strptime(start, "%I:%M %p")
    
    sorted_time_slots = sorted(time_slots_set, key=time_key)
    
    # Step 3: Generate timetable matrix per class
    class_timetables_df = {}
    
    for class_name, days_data in all_classes.items():
        # Create empty matrix with days as rows, sorted time slots as columns
        df = pd.DataFrame(index=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                          columns=sorted_time_slots)
        
        for day, periods in days_data.items():
            for period in periods:
                time_range = f"{period['start']} - {period['end']}"
                if period["subject"]:
                    subject = period["subject"]["name"]
                    value = subject
                else:
                    value = period["type"].capitalize()
                
                df.loc[day, time_range] = value
        
        df.fillna("", inplace=True)
        class_timetables_df[class_name] = df
    
    state['class_timetables_df'] = class_timetables_df
    print_success("DataFrames created successfully!")
    return state


def generate_timetable_files(state: TimeTableState) -> TimeTableState:
    """Generate PNG, CSV, and Excel files from timetable DataFrames"""
    print_step("Generating timetable files", "📁")
    
    class_timetables_df = state['class_timetables_df']
    all_grades = list(class_timetables_df.keys())
    
    # Create output directory if it doesn't exist
    import os
    output_dir = "generated_timetables"
    os.makedirs(output_dir, exist_ok=True)
    
    generated_files = []
    
    for class_group in all_grades:
        class_timetable_df = class_timetables_df[class_group]
        
        # Generate file paths
        safe_class_name = class_group.replace(" ", "_").replace("/", "_")
        png_file = f"{output_dir}/{safe_class_name}_timetable.png"
        csv_file = f"{output_dir}/{safe_class_name}_timetable.csv"
        excel_file = f"{output_dir}/{safe_class_name}_timetable.xlsx"
        
        # Generate PNG image
        try:
            create_timetable_image(class_timetable_df, class_group, png_file, use_colors=False)
            generated_files.append(png_file)
            print_success(f"Generated PNG for {class_group}")
        except Exception as e:
            print_error(f"Failed to generate PNG for {class_group}: {str(e)}")
        
        # Generate CSV file
        try:
            class_timetable_df.to_csv(csv_file, index=True)
            generated_files.append(csv_file)
            print_success(f"Generated CSV for {class_group}")
        except Exception as e:
            print_error(f"Failed to generate CSV for {class_group}: {str(e)}")
        
        # Generate Excel file
        try:
            class_timetable_df.to_excel(excel_file, index=True, sheet_name=class_group)
            generated_files.append(excel_file)
            print_success(f"Generated Excel for {class_group}")
        except Exception as e:
            print_error(f"Failed to generate Excel for {class_group}: {str(e)}")
    
    # Store generated files in state
    state['generated_files'] = generated_files
    
    # Display summary
    file_summary = {
        "Classes Processed": str(len(all_grades)),
        "PNG Files": str(len([f for f in generated_files if f.endswith('.png')])),
        "CSV Files": str(len([f for f in generated_files if f.endswith('.csv')])),
        "Excel Files": str(len([f for f in generated_files if f.endswith('.xlsx')])),
        "Output Directory": output_dir
    }
    print_status_panel("File Generation Summary", file_summary)
    
    print_success("All timetable files generated successfully!")
    return state


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
workflow.add_node('convert_to_dataframes', convert_to_dataframes)
workflow.add_node('generate_files', generate_timetable_files)

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
        "convert_to_dataframes": "convert_to_dataframes"
    }
)
workflow.add_edge('convert_to_dataframes', 'generate_files')
workflow.add_edge('generate_files', END)


# Compile workflow
graph = workflow.compile()

if __name__ == "__main__":
    # Display application banner
    print_banner(
        title="SKEJUL-AI",
        subtitle="AI-Powered Timetable Generator", 
        description="Intelligent School Scheduling System",
        subheader1="Creating optimized timetables with AI",
        subheader2="Handling teacher constraints automatically"
    )
    
    
    # Execute workflow
    result = graph.invoke({"input": USER_PROMPT})
    
    # Output results with nice formatting
    print_result_box("Generated Timetables", json.dumps(result['class_timetables'], indent=2))
    
    # Display completion message
    print_completion_message("Skejul-AI", "Your Intelligent Scheduling Assistant")
    

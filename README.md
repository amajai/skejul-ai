# Skejul AI - School Timetable Generator

An intelligent school timetable generator that uses AI to automatically create optimized class schedules based on natural language input. The system extracts structured data from user requirements and generates comprehensive timetables for class groups sequentially with teacher availability tracking.

## Features

- **Natural Language Processing**: Input timetable requirements in plain English
- **Intelligent Data Extraction**: Automatically extracts school days, periods, subjects, teachers, and constraints
- **Flexible LLM Configuration**: Configure any LLM provider via environment variables (.env file)
- **Sequential Processing**: Generates timetables one class group at a time to prevent teacher conflicts
- **Teacher Availability Tracking**: Prevents double-booking teachers across class groups
- **Structured Validation**: Validates extracted data before timetable generation
- **Flexible Constraints**: Handles teacher preferences, workload limits, and scheduling constraints
- **JSON Output**: Generates structured timetables in JSON format for easy integration
- **Workflow Visualization**: Generate Mermaid diagrams to visualize the workflow

## Usage

### Basic Usage

Run the script with a sample prompt:

```bash
python skejul-ai.py
```

### Custom Input

Modify the `USER_PROMPT` in `prompts.py` or pass your requirements:

```python
from skejul_ai import graph

result = graph.invoke({
    "input": """
    Generate a timetable for JSS 1, JSS 2, Primary 5 (Mon-Fri, 7:00 AM-5:00 PM).
    
    Schedule:
    - Assembly: 7:00-8:20 AM
    - Breaks: 9:40-10:00, 11:20-11:35, Lunch: 12:55-2:00
    - Each period: 40 mins
    
    Subjects: English, Math, Science, Social Studies
    Teachers: Mr. A (English), Mr. B (Math), Mrs. C (Science)
    
    Constraints:
    - No teacher overlap across class groups
    - Max 4 periods per teacher per day
    """
})

print(result['class_timetables'])
```

### View Workflow Diagram

Generate a Mermaid diagram to visualize the workflow:

```python
from skejul_ai import graph

# Print workflow diagram
print(graph.get_graph().draw_mermaid())

# Print horizontal workflow diagram
mermaid_code = graph.get_graph().draw_mermaid()
horizontal_mermaid_code = mermaid_code.replace("graph TD","graph LR")
print(horizontal_mermaid_code)
```

## Input Format

The system accepts natural language input describing:

### Required Information:
- **School Days**: e.g., "Monday to Friday"
- **School Hours**: e.g., "7:00 AM to 5:00 PM"
- **Class Groups**: e.g., "JSS 1", "Primary 5"
- **Subjects**: List of subjects to be scheduled
- **Teachers**: Teacher names and their subjects

### Optional Information:
- **Fixed Periods**: Assembly, breaks, lunch times
- **Period Duration**: e.g., "40 minutes per period"
- **Teacher Constraints**: Preferences, maximum periods per day
- **Special Activities**: Sports, prayers, etc.

## Output Format

The system generates structured JSON timetables:

```json
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
          "name": "Math",
          "teacher_name": "Mr. C"
        }
      }
    ]
  }
}
```

## Workflow

The system uses a LangGraph workflow with sequential class group processing:

1. **Data Extraction**: Extracts structured data from natural language input using structured LLM
2. **Validation**: Validates that all required information is present
3. **Sequential Processing Initialization**: Sets up processing for multiple class groups
4. **For Each Class Group**:
   - **Generate Single Class Group**: Creates timetable for current class group only
   - **Update Teacher Availability**: Tracks when teachers are busy from previous class groups
   - **Increment Index**: Moves to next class group
5. **Output**: Returns formatted JSON timetables for all class groups

This sequential approach ensures no teacher conflicts across different class groups.

## Configuration

### LLM Models
Configure AI models flexibly via `.env` file:

```env
# Structured data extraction LLM
STRUCTURED_LLM_PROVIDER=google_genai
STRUCTURED_LLM_MODEL=gemini-2.5-flash
STRUCTURED_LLM_TEMPERATURE=0

# Timetable generation LLM  
LLM_PROVIDER=groq
LLM_MODEL=moonshotai/kimi-k2-instruct
LLM_TEMPERATURE=0.1
```

Supported providers:
- `google_genai`: Google Gemini models
- `groq`: Groq models including Moonshot AI
- `openai`: OpenAI models (via LangChain)
- Any LangChain-compatible provider

### Prompts
Customize the AI prompts in `prompts.py`:
- `GET_TIMETABLE_SYSTEM_PROMPT`: For structured data extraction
- `GENERATE_SINGLE_GRADE_PROMPT`: For single class group timetable generation

## Data Models

The system uses Pydantic models for type safety:

- **TimetableData**: Main data structure for extracted information
- **ClassGroup**: Represents a class with subjects and teachers
- **TimePeriod**: Represents time slots and their types
- **SubjectDefinition**: Subject details with teacher assignments

## Error Handling

The system includes validation for:
- Missing required data (school days, periods, class groups)
- Invalid time formats
- Teacher scheduling conflicts across class groups
- Incomplete subject-teacher assignments
- Sequential processing ensures teacher availability tracking

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check existing documentation
- Review the example prompts in `prompts.py`

## Example Use Cases

- **Primary Schools**: Generate timetables for elementary classes
- **Secondary Schools**: Handle complex subject-teacher assignments
- **Private Schools**: Accommodate special schedules and constraints
- **Tutoring Centers**: Organize multiple classes and instructors

## Roadmap

- [x] Sequential class group processing
- [x] Teacher availability tracking
- [x] Flexible LLM configuration via .env
- [x] Workflow visualization with Mermaid
- [ ] Human-in-the-loop review system
- [ ] Web interface for easier input
- [ ] Teacher timetable generation
- [ ] Conflict resolution suggestions  
- [ ] Export to Excel/PDF formats
- [ ] Multi-language support
- [ ] Advanced constraint handling
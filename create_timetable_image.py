import pandas as pd
import matplotlib.pyplot as plt
import random

# Global dictionary to store subject colors persistently
_subject_colors = {}

def create_timetable_image(df, class_name, output_file="timetable.png", use_colors=True):
    """
    Create a structured visual representation of a timetable dataframe
    """
    # Set up the figure
    fig_width = max(12, len(df.columns) * 1.5)  
    fig_height = max(8, len(df.index) * 1.2)
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis('off')
    
    # Fixed colors for special periods
    fixed_colors = {
        'Assembly': '#FF6B6B',
        'Break': '#4ECDC4', 
        'Lunch': '#45B7D1',
        'Activity': '#96CEB4',
        'default': '#E8E8E8'
    }
    
    def generate_random_color():
        """Generate a random pleasant color"""
        colors = [
            '#FFEAA7', '#DDA0DD', "#79B3A5", '#F7DC6F', '#AED6F1',
            '#F8C471', '#D7BDE2', '#A9DFBF', '#FAD7A0', '#F5B7B1',
            '#D5A6BD', '#AED6F1', '#A3E4D7', '#F9E79F', '#D2B4DE',
            '#85C1E9', '#82E0AA', '#F8D7DA', '#D1ECF1', '#FFF3CD',
            '#E2E3E5', '#D4E6F1', '#D5F4E6', '#FCF3CF', '#FADBD8'
        ]
        return random.choice(colors)
    
    def get_subject_color(subject):
        """Get or assign color for a subject"""
        # Check fixed colors first
        if subject in fixed_colors:
            return fixed_colors[subject]
        
        # Check if we already assigned a color to this subject
        if subject in _subject_colors:
            return _subject_colors[subject]
        
        # Assign new random color
        color = generate_random_color()
        _subject_colors[subject] = color
        return color
    
    def abbreviate_subject(subject, max_length=12):
        """Dynamically abbreviate long subject names intelligently"""
        if len(subject) <= max_length:
            return subject
        
        def shorten_word(word, target_length):
            """Intelligently shorten a single word"""
            if len(word) <= target_length:
                return word
            
            # Remove vowels (except first letter) while keeping consonants
            if target_length >= 4:
                vowels = 'aeiouAEIOU'
                consonants_only = word[0]  # Keep first letter
                for char in word[1:]:
                    if char not in vowels:
                        consonants_only += char
                    if len(consonants_only) >= target_length:
                        break
                
                if len(consonants_only) <= target_length:
                    return consonants_only
            
            # If still too long, truncate and add period
            return word[:target_length-1] + '.'
        
        words = subject.split()
        
        if len(words) == 1:
            # Single word - use intelligent shortening
            return shorten_word(words[0], max_length)
        
        elif len(words) == 2:
            # Two words - try different strategies
            word1, word2 = words
            
            # Strategy 1: Try shortening the longer word
            if len(word1) > len(word2):
                shortened_w1 = shorten_word(word1, max_length - len(word2) - 1)
                result = f"{shortened_w1} {word2}"
                if len(result) <= max_length:
                    return result
            else:
                shortened_w2 = shorten_word(word2, max_length - len(word1) - 1)
                result = f"{word1} {shortened_w2}"
                if len(result) <= max_length:
                    return result
            
            # Strategy 2: Shorten both words proportionally
            available_chars = max_length - 1  # -1 for space
            w1_target = min(len(word1), available_chars // 2)
            w2_target = available_chars - w1_target
            
            shortened_w1 = shorten_word(word1, w1_target)
            shortened_w2 = shorten_word(word2, w2_target)
            
            return f"{shortened_w1} {shortened_w2}"
        
        else:
            # Multiple words - use initials + last word approach
            last_word = words[-1]
            other_words = words[:-1]
            
            # Calculate space for initials
            available_for_initials = max_length - len(last_word) - 1
            
            if available_for_initials >= len(other_words):
                # Use first letter of each word
                initials = ''.join([w[0].upper() for w in other_words])
                result = f"{initials} {last_word}"
                
                if len(result) <= max_length:
                    return result
            
            # If initials + last word is too long, shorten last word too
            if available_for_initials >= 2:
                initials = ''.join([w[0].upper() for w in other_words])
                remaining_space = max_length - len(initials) - 1
                shortened_last = shorten_word(last_word, remaining_space)
                return f"{initials} {shortened_last}"
            
            # Last resort: use first few letters of first word + last word
            first_word_abbrev = shorten_word(words[0], max_length - len(last_word) - 1)
            return f"{first_word_abbrev} {last_word}"
    
    # Create the table with custom styling
    table_data = []
    cell_colors = []
    
    # Add header row with formatted time slots
    formatted_columns = []
    for col in df.columns:
        # Format time range with line break
        if ' - ' in col:
            start_time, end_time = col.split(' - ')
            formatted_time = f"{start_time} -\n{end_time}"
            formatted_columns.append(formatted_time)
        else:
            formatted_columns.append(col)
    
    headers = ['Day/Time'] + formatted_columns
    table_data.append(headers)
    if use_colors:
        header_colors = ['#2C3E50'] * len(headers)
    else:
        header_colors = ['#FFFFFF'] * len(headers)  # White headers for no colors
    cell_colors.append(header_colors)
    
    # Add data rows
    for day in df.index:
        row = [day]
        if use_colors:
            row_colors = ['#34495E']  # Day column color
        else:
            row_colors = ['#FFFFFF']  # White day column for no colors
        
        for time_slot in df.columns:
            cell_value = df.loc[day, time_slot]
            if pd.isna(cell_value) or cell_value == '':
                cell_value = ''
                if use_colors:
                    color = fixed_colors['default']
                else:
                    color = '#FFFFFF'  # White background for no colors
            else:
                # Extract subject name (remove teacher info if present)
                subject = cell_value.split('(')[0].strip()
                original_subject = subject  # Keep original for color mapping
                
                # Abbreviate long subject names
                abbreviated_subject = abbreviate_subject(subject)
                
                # Format subject with line breaks for multi-word subjects
                if ' ' in abbreviated_subject and abbreviated_subject not in fixed_colors:
                    # Split on spaces and rejoin with \n for line breaks
                    words = abbreviated_subject.split()
                    if len(words) == 2:
                        formatted_subject = f"{words[0]}\n{words[1]}"
                        # Replace the original subject with the formatted abbreviated version
                        cell_value = cell_value.replace(subject, formatted_subject)
                    else:
                        # For more than 2 words, just use the abbreviated version
                        cell_value = cell_value.replace(subject, abbreviated_subject)
                else:
                    # Single word or fixed color subject
                    cell_value = cell_value.replace(subject, abbreviated_subject)
                
                if use_colors:
                    color = get_subject_color(original_subject)  # Use original for consistent coloring
                else:
                    color = '#FFFFFF'  # White background for no colors
            
            row.append(cell_value)
            row_colors.append(color)
        
        table_data.append(row)
        cell_colors.append(row_colors)
    
    # Create the table
    table = ax.table(
        cellText=table_data,
        cellColours=cell_colors,
        cellLoc='center',
        loc='center',
        bbox=[0, 0, 1, 1]
    )
    
    # Style the table
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 2.5)
    
    # Style header row
    header_text_color = 'white' if use_colors else 'black'
    for i in range(len(headers)):
        cell = table[(0, i)]
        cell.set_text_props(weight='bold', color=header_text_color)
        cell.set_height(0.08)
    
    # Style day column and make top-left cell same width
    day_column_width = 0.12
    day_text_color = 'white' if use_colors else 'black'
    for i in range(len(table_data)):
        cell = table[(i, 0)]
        if i == 0:  # Header row (Day/Time cell)
            cell.set_text_props(weight='bold', color=header_text_color)
        else:  # Day cells
            cell.set_text_props(weight='bold', color=day_text_color)
        cell.set_width(day_column_width)
    
    # Wrap text for long entries
    for i in range(len(table_data)):
        for j in range(len(table_data[i])):
            cell = table[(i, j)]
            if len(str(table_data[i][j])) > 15:
                # Break long text
                text = str(table_data[i][j])
                if '(' in text:
                    parts = text.split('(')
                    wrapped = parts[0] + '\n(' + parts[1]
                    cell.set_text_props(text=wrapped)
    
    # Add title
    plt.suptitle(f"{class_name} - Weekly Timetable", 
                fontsize=16, fontweight='bold', y=0.99)
    
    # Save the image
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Timetable image saved as {output_file}")
    
    return fig

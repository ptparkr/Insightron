"""
Utility functions for Insightron
Handles markdown creation and text formatting
"""
from datetime import datetime
import logging
from typing import List, Dict, Any
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)


def format_text(text: str, style: str = "auto") -> str:
    """
    Format transcription text into readable paragraphs
    
    Args:
        text: Raw transcription text
        style: Formatting style (auto, paragraphs, minimal)
        
    Returns:
        Formatted text with proper paragraphs
    """
    if not text:
        return ""
    
    # Split into sentences
    sentences = split_into_sentences(text)
    
    if style == "minimal":
        # Group every 5 sentences
        return group_sentences(sentences, 5)
    elif style == "paragraphs":
        # Group every 3 sentences
        return group_sentences(sentences, 3)
    else:  # auto
        # Smart grouping based on content
        return smart_format(sentences)


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using regex"""
    import re
    # Split on sentence endings followed by space
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def group_sentences(sentences: List[str], group_size: int) -> str:
    """Group sentences into paragraphs of specified size"""
    paragraphs = []
    for i in range(0, len(sentences), group_size):
        group = sentences[i:i + group_size]
        paragraphs.append(' '.join(group))
    return '\n\n'.join(paragraphs)


def smart_format(sentences: List[str]) -> str:
    """
    Smart formatting based on sentence length and content
    Creates natural paragraph breaks
    """
    paragraphs = []
    current_paragraph = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence.split())
        
        # Start new paragraph if:
        # 1. Current paragraph has 3+ sentences, OR
        # 2. Current paragraph is long enough (150+ words)
        if len(current_paragraph) >= 3 or current_length > 150:
            paragraphs.append(' '.join(current_paragraph))
            current_paragraph = []
            current_length = 0
        
        current_paragraph.append(sentence)
        current_length += sentence_length
    
    # Add remaining sentences
    if current_paragraph:
        paragraphs.append(' '.join(current_paragraph))
    
    return '\n\n'.join(paragraphs)


def format_timestamp(seconds: float) -> str:
    """
    Format seconds to MM:SS or HH:MM:SS
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def create_timestamps_section(segments: List[Dict[str, Any]], max_segments: int = 20) -> str:
    """
    Create a timestamps section from Whisper segments
    
    Args:
        segments: List of segment dictionaries from Whisper
        max_segments: Maximum number of segments to display
        
    Returns:
        Formatted timestamps section
    """
    if not segments:
        return "_No timestamp data available_"
    
    timestamp_lines = []
    total_segments = len(segments)
    segments_to_show = segments[:max_segments]
    
    for segment in segments_to_show:
        start = segment.get('start', 0)
        end = segment.get('end', 0)
        text = segment.get('text', '').strip()
        
        start_time = format_timestamp(start)
        end_time = format_timestamp(end)
        
        timestamp_lines.append(f"**{start_time} - {end_time}:** {text}")
    
    result = '\n\n'.join(timestamp_lines)
    
    # Add note if there are more segments
    if total_segments > max_segments:
        remaining = total_segments - max_segments
        result += f"\n\n*... and {remaining} more segment{'s' if remaining > 1 else ''}*"
    
    return result


def create_markdown(
    filename: str,
    text: str,
    date: str,
    duration: str,
    file_size_mb: float,
    model: str,
    language: str,
    formatting_style: str = "auto",
    processing_time_seconds: float = 0,
    duration_seconds: float = 0,
    segments: List[Dict[str, Any]] = None,
    **kwargs  # Accept additional kwargs and ignore them
) -> str:
    """
    Create a formatted markdown document from transcription data with Obsidian-style frontmatter
    
    Args:
        filename: Name of the audio file (without extension)
        text: Transcribed text
        date: Transcription date/time
        duration: Audio duration (formatted)
        file_size_mb: File size in MB
        model: Whisper model used
        language: Detected language
        formatting_style: Text formatting style
        processing_time_seconds: Time taken to process
        duration_seconds: Duration in seconds
        segments: Whisper segments for timestamps
        **kwargs: Additional parameters (ignored for compatibility)
        
    Returns:
        Formatted markdown content with frontmatter
    """
    try:
        # Format the transcription text
        formatted_text = format_text(text, formatting_style)
        
        # Create timestamps section if segments available
        timestamps_section = ""
        if segments:
            timestamps_section = f"""## 🕐 Timestamps

{create_timestamps_section(segments)}

"""
        
        # Get current datetime
        now = datetime.now()
        created_date = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Create Obsidian-compatible frontmatter
        frontmatter = f"""---
title: {filename}
date: {created_date}
duration: {duration}
duration_seconds: {duration_seconds}
file_size: {file_size_mb:.1f} MB
model: {model}
language: {language}
formatting: {formatting_style}
tags: [transcription, audio-note, whisper]
created: {created_date}
---"""
        
        # Create the full markdown document
        markdown = f"""{frontmatter}

# 🎤 Transcription: {filename}

## 📊 Metadata
- **Duration:** {duration} ({duration_seconds:.1f} seconds)
- **File Size:** {file_size_mb:.1f} MB
- **Model:** {model}
- **Language:** {language}
- **Formatting:** {formatting_style.capitalize()}
- **Transcribed:** {created_date}

## 📝 Transcript

{formatted_text}

{timestamps_section}
---
*Transcribed using Insightron*  
*Generated on {created_date}*
"""
        
        logger.info(f"Enhanced markdown created for: {filename}")
        return markdown
        
    except Exception as e:
        logger.error(f"Error creating markdown: {e}")
        # Return basic markdown on error
        return f"""---
title: {filename}
date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
tags: [transcription, error]
---

# {filename}

## Transcription

{text}

---

*Error creating full markdown: {e}*
*Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable format
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "2:34" or "1:23:45")
    """
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}:{minutes:02d}:{secs:02d}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for filesystem
    """
    import re
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename


def create_timestamps_section(segments: List[Dict[str, Any]], max_segments: int = 20) -> str:
    """
    Create a timestamps section from Whisper segments
    
    Args:
        segments: List of segment dictionaries from Whisper
        max_segments: Maximum number of segments to display
        
    Returns:
        Formatted timestamps section
    """
    if not segments:
        return "_No timestamp data available_"
    
    timestamp_lines = []
    total_segments = len(segments)
    segments_to_show = segments[:max_segments]
    
    for segment in segments_to_show:
        start = segment.get('start', 0)
        end = segment.get('end', 0)
        text = segment.get('text', '').strip()
        
        start_time = format_timestamp(start)
        end_time = format_timestamp(end)
        
        timestamp_lines.append(f"**{start_time} - {end_time}:** {text}")
    
    result = '\n\n'.join(timestamp_lines)
    
    # Add note if there are more segments
    if total_segments > max_segments:
        remaining = total_segments - max_segments
        result += f"\n\n*... and {remaining} more segment{'s' if remaining > 1 else ''}*"
    
    return result


def create_markdown(
    filename: str,
    text: str,
    date: str,
    duration: str,
    file_size_mb: float,
    model: str,
    language: str,
    formatting_style: str = "auto",
    processing_time_seconds: float = 0,
    duration_seconds: float = 0,
    segments: List[Dict[str, Any]] = None,
    **kwargs  # Accept additional kwargs and ignore them
) -> str:
    """
    Create a formatted markdown document from transcription data with Obsidian-style frontmatter
    
    Args:
        filename: Name of the audio file (without extension)
        text: Transcribed text
        date: Transcription date/time
        duration: Audio duration (formatted)
        file_size_mb: File size in MB
        model: Whisper model used
        language: Detected language
        formatting_style: Text formatting style
        processing_time_seconds: Time taken to process
        duration_seconds: Duration in seconds
        segments: Whisper segments for timestamps
        **kwargs: Additional parameters (ignored for compatibility)
        
    Returns:
        Formatted markdown content with frontmatter
    """
    try:
        # Format the transcription text
        formatted_text = format_text(text, formatting_style)
        
        # Create timestamps section if segments available
        timestamps_section = ""
        if segments:
            timestamps_section = f"""## 🕐 Timestamps

{create_timestamps_section(segments)}

"""
        
        # Get current datetime
        now = datetime.now()
        created_date = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Create Obsidian-compatible frontmatter
        frontmatter = f"""---
title: {filename}
date: {created_date}
duration: {duration}
duration_seconds: {duration_seconds}
file_size: {file_size_mb:.1f} MB
model: {model}
language: {language}
formatting: {formatting_style}
tags: [transcription, audio-note, whisper]
created: {created_date}
---"""
        
        # Create the full markdown document
        markdown = f"""{frontmatter}

# 🎤 Transcription: {filename}

## 📊 Metadata
- **Duration:** {duration} ({duration_seconds:.1f} seconds)
- **File Size:** {file_size_mb:.1f} MB
- **Model:** {model}
- **Language:** {language}
- **Formatting:** {formatting_style.capitalize()}
- **Transcribed:** {created_date}

## 📝 Transcript

{formatted_text}

{timestamps_section}
---
*Transcribed using Insightron*  
*Generated on {created_date}*
"""
        
        logger.info(f"Enhanced markdown created for: {filename}")
        return markdown
        
    except Exception as e:
        logger.error(f"Error creating markdown: {e}")
        # Return basic markdown on error
        return f"""---
title: {filename}
date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
tags: [transcription, error]
---

# {filename}

## Transcription

{text}

---

*Error creating full markdown: {e}*
*Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable format
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "2:34" or "1:23:45")
    """
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}:{minutes:02d}:{secs:02d}"


def save_processed_audio(audio_path: str, processed_folder: Path) -> Path:
    """
    Save processed audio file to the processed audio folder.
    Copies the file to preserve the original.
    
    Args:
        audio_path: Path to the original audio file
        processed_folder: Path to the processed audio folder
        
    Returns:
        Path to the saved audio file in the processed folder
        
    Raises:
        FileNotFoundError: If the audio file doesn't exist
        OSError: If the file cannot be copied
    """
    audio_file = Path(audio_path)
    
    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    # Ensure processed folder exists
    processed_folder.mkdir(parents=True, exist_ok=True)
    
    # Create destination path
    # If file already exists, add a timestamp to avoid overwriting
    dest_path = processed_folder / audio_file.name
    
    if dest_path.exists():
        # Add timestamp to filename to avoid overwriting
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = audio_file.stem
        suffix = audio_file.suffix
        dest_path = processed_folder / f"{stem}_{timestamp}{suffix}"
    
    try:
        # Copy the file
        shutil.copy2(audio_file, dest_path)
        logger.info(f"Saved processed audio: {audio_file.name} -> {dest_path}")
        return dest_path
    except Exception as e:
        logger.error(f"Error saving processed audio {audio_file.name}: {e}")
        raise OSError(f"Failed to save processed audio: {e}")


# Example usage and testing
if __name__ == "__main__":
    # Test markdown creation with timestamps
    test_segments = [
        {'start': 0, 'end': 9, 'text': 'What happened is that she has been talking about the harsh disturbances and realizing'},
        {'start': 9, 'end': 14, 'text': 'them through the perfect consciousness relieves it.'},
        {'start': 14, 'end': 26, 'text': 'Well this clears the easier karma and outer karma whereas the more external karma gets'}
    ]
    
    test_data = {
        'filename': 'Recording',
        'text': 'This is a test transcription. It has multiple sentences. This helps test formatting.',
        'date': '2025-10-19 09:53:57',
        'duration': '1:50',
        'duration_seconds': 109.5,
        'file_size_mb': 18.4,
        'model': 'whisper',
        'language': 'en',
        'formatting_style': 'auto',
        'processing_time_seconds': 45.3,
        'segments': test_segments
    }
    
    markdown = create_markdown(**test_data)
    print(markdown)


def create_realtime_note(
    filename: str,
    text: str,
    date: str,
    duration: str,
    file_size_mb: float,
    model: str,
    language: str,
    formatting_style: str = "auto",
    duration_seconds: float = 0,
    segments: List[Dict[str, Any]] = None,
    folder_path: str = ""
) -> str:
    """
    Create a formatted markdown note specifically for Realtime Transcription
    Matches user-requested Obsidian format
    """
    try:
        # Format the transcription text
        formatted_text = format_text(text, formatting_style)
        
        # Create timestamps section
        timestamps_section = ""
        if segments:
            timestamps_section = f"## 🕐 Timestamps\n\n{create_timestamps_section(segments, max_segments=1000)}"

        # Create Obsidian-compatible frontmatter
        frontmatter = f"""---
title: {filename}
date: {date}
duration: {duration}
duration_seconds: {duration_seconds:.3f}
file_size: {file_size_mb:.1f} MB
model: {model}
language: {language}
formatting: {formatting_style}
tags: [transcription, audio-note, whisper]
created: {date}
---"""
        
        # Create the full markdown document
        markdown = f"""{frontmatter}

# 🎤 Transcription: {filename}

## 📊 Metadata
- **Duration:** {duration} ({duration_seconds:.1f} seconds)
- **File Size:** {file_size_mb:.1f} MB
- **Model:** {model}
- **Language:** {language}
- **Formatting:** {formatting_style.capitalize()}
- **Transcribed:** {date}

## 📝 Transcript

{formatted_text}

{timestamps_section}

---
*Transcribed using Insightron - Realtime Transcription*  
*Generated on {date}*
"""
        return markdown
        
    except Exception as e:
        logger.error(f"Error creating realtime note: {e}")
        return f"Error generating note: {e}"

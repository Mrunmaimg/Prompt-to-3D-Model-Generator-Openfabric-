import os
import base64
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import streamlit as st
import warnings
import tracemalloc

def save_binary_to_file(data: bytes, directory: str, prefix: str, extension: str) -> Optional[str]:
    """
    Save binary data to a file with timestamp
    
    Args:
        data (bytes): Binary data to save
        directory (str): Directory to save the file in
        prefix (str): Prefix for the filename
        extension (str): File extension
        
    Returns:
        Optional[str]: Path to saved file if successful, None otherwise
    """
    try:
        os.makedirs(directory, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.{extension}"
        filepath = os.path.join(directory, filename)
        
        with open(filepath, 'wb') as f:
            f.write(data)
            
        return filepath
    except Exception as e:
        logging.error(f"Error saving file: {e}")
        return None

def load_binary_from_file(filepath: str) -> Optional[bytes]:
    """
    Load binary data from a file
    
    Args:
        filepath (str): Path to the file
        
    Returns:
        Optional[bytes]: File contents if successful
    """
    try:
        with open(filepath, 'rb') as f:
            return f.read()
    except Exception as e:
        logging.error(f"Error loading file: {e}")
        return None

def image_to_base64(image_data: bytes) -> str:
    """
    Convert image binary data to base64 string
    
    Args:
        image_data (bytes): Binary image data
        
    Returns:
        str: Base64 encoded image string
    """
    return base64.b64encode(image_data).decode('utf-8')

def base64_to_image(base64_str: str) -> Optional[bytes]:
    """
    Convert base64 string to image binary data
    
    Args:
        base64_str (str): Base64 encoded image string
        
    Returns:
        Optional[bytes]: Binary image data if successful
    """
    try:
        return base64.b64decode(base64_str)
    except Exception as e:
        logging.error(f"Error decoding base64: {e}")
        return None

def create_model_viewer_html(model_bytes: bytes) -> str:
    """
    Create HTML string for the 3D model viewer using base64 encoded model data
    
    Args:
        model_bytes (bytes): Binary model data in GLB format
        
    Returns:
        str: HTML code for the model viewer
    """
    model_base64 = base64.b64encode(model_bytes).decode('utf-8')
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.3.0/model-viewer.min.js"></script>
        <style>
            model-viewer {{
                width: 100%;
                height: 400px;
                background-color: #ffffff;
                --poster-color: transparent;
            }}
        </style>
    </head>
    <body>
        <model-viewer
            src="data:model/gltf-binary;base64,{model_base64}"
            alt="3D model"
            auto-rotate
            camera-controls
            ar
            shadow-intensity="1"
            environment-image="neutral"
            exposure="1"
            camera-orbit="0deg 75deg 105%"
            min-camera-orbit="auto auto auto"
            max-camera-orbit="auto auto 105%"
            interaction-prompt="none"
            shadow-softness="1"
            stage-light-intensity="2"
            environment-intensity="1"
        ></model-viewer>
    </body>
    </html>
    """

def setup_logging():
    """Configure logging for the application"""
    tracemalloc.start()
    
    warnings.filterwarnings(
        "ignore",
        message="coroutine '.*' was never awaited",
        category=RuntimeWarning
    )
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log')
        ]
    )
    
    logging.getLogger('numexpr.utils').setLevel(logging.WARNING)

def format_timestamp(timestamp_str: str) -> str:
    """Format timestamp string to human readable format
    
    Args:
        timestamp_str (str): Timestamp string in format 'YYYY-MM-DD HH:MM:SS'
        
    Returns:
        str: Formatted timestamp string like 'Month DD, YYYY at HH:MM AM/PM'
    """
    try:
        dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%B %d, %Y at %I:%M %p')
    except:
        return timestamp_str

def show_database_info(db_info: Dict[str, Any], on_close: callable):
    """Display database information in a modal dialog
    
    Args:
        db_info (Dict[str, Any]): Database information dictionary containing:
            - total_entries: Total number of entries
            - table_info: Table structure information
            - entries: List of all entries
        on_close (callable): Callback function to handle modal close
    """
    # Create the overlay and modal HTML structure
    st.markdown("""
        
     
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([0.9, 0.1])
    with col1:
        st.markdown("## Database Information")
    with col2:
        if st.button("✕", key="close_modal_x", help="Close"):
            on_close()
            st.rerun()
    
    st.markdown("---")
    
    # Statistics row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Entries", db_info['total_entries'])
    with col2:
        complete_entries = len([e for e in db_info['entries'] if e['status'] == 'Complete'])
        st.metric("Complete Generations", complete_entries)
    with col3:
        image_only = len([e for e in db_info['entries'] if e['status'] == 'Image Only'])
        st.metric("Image Only", image_only)
    
    # Content tabs
    tab1, tab2 = st.tabs(["Table Structure", "All Entries"])
    
    with tab1:
        if db_info['table_info']:
            st.markdown("#### Database Schema")
            schema_data = []
            for col in db_info['table_info']:
                schema_data.append({
                    'Column Name': col['name'],
                    'Type': col['type'],
                    'Required': "Yes" if col['notnull'] else "No",
                    'Default': col['dflt_value'] if col['dflt_value'] else "None"
                })
            st.table(schema_data)
            
            st.markdown("""
            #### Column Descriptions:
            - **id**: Unique identifier for each generation
            - **prompt**: Original user input prompt
            - **enhanced_prompt**: AI-enhanced version of the prompt
            - **image_path**: Path to the generated image file
            - **model_path**: Path to the generated 3D model file
            - **created_at**: Timestamp of generation
            - **metadata**: Additional information (JSON format)
            """)
    
    with tab2:
        if db_info['entries']:
            entries_data = []
            for entry in db_info['entries']:
                entries_data.append({
                    'ID': entry['id'],
                    'Created': format_timestamp(entry['created_at']),
                    'Prompt': entry['prompt'],
                    'Enhanced Prompt': entry['enhanced_prompt'] or 'None',
                    'Image Path': entry['image_path'] or 'None',
                    'Model Path': entry['model_path'] or 'None',
                    'Metadata': entry['metadata'] or 'None'
                })
            st.dataframe(
                entries_data,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'ID': st.column_config.NumberColumn(
                        'ID',
                        help='Unique identifier for each generation'
                    ),
                    'Created': st.column_config.DatetimeColumn(
                        'Created',
                        help='When this generation was created'
                    ),
                    'Status': st.column_config.TextColumn(
                        'Status',
                        help='Current status of the generation'
                    ),
                    'Prompt': st.column_config.TextColumn(
                        'Prompt',
                        help='Original user prompt',
                        width='large'
                    ),
                    'Enhanced Prompt': st.column_config.TextColumn(
                        'Enhanced Prompt',
                        help='AI-enhanced version of the prompt',
                        width='large'
                    ),
                    'Image Path': st.column_config.TextColumn(
                        'Image Path',
                        help='Path to the generated image file'
                    ),
                    'Model Path': st.column_config.TextColumn(
                        'Model Path',
                        help='Path to the generated 3D model file'
                    ),
                    'Metadata': st.column_config.TextColumn(
                        'Metadata',
                        help='Additional information about the generation'
                    )
                }
            )
        else:
            st.info("No entries in database")
    
    st.markdown("---")
    if st.button("Close Window", use_container_width=True):
        on_close()
        st.rerun() 
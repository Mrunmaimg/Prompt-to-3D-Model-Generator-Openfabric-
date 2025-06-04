import os
os.environ["NUMEXPR_MAX_THREADS"] = "12"  

import warnings
warnings.filterwarnings("ignore", category=Warning) 

import streamlit as st
from managers.llm_manager import LLMManager
from managers.openfabric_manager import OpenfabricManager
from managers.memory_manager import MemoryManager
from utils.utils import (
    save_binary_to_file, 
    image_to_base64, 
    create_model_viewer_html, 
    setup_logging, 
    format_timestamp,
    show_database_info
)
import logging
from datetime import datetime

st.set_page_config(
    page_title="AI Image to 3D Model Generator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Setup logging
setup_logging()

# Initialize managers
@st.cache_resource
def init_managers():
    return {
        'llm': LLMManager(),
        'openfabric': OpenfabricManager(),
        'memory': MemoryManager()
    }

managers = init_managers()

# Initialize session state
if 'current_image' not in st.session_state:
    st.session_state.current_image = None
if 'current_model' not in st.session_state:
    st.session_state.current_model = None
if 'enhanced_prompt' not in st.session_state:
    st.session_state.enhanced_prompt = None
if 'reference_prompt' not in st.session_state:
    st.session_state.reference_prompt = None
if 'reference_image' not in st.session_state:
    st.session_state.reference_image = None
if 'reference_id' not in st.session_state:
    st.session_state.reference_id = None
if 'confirm_clear' not in st.session_state:
    st.session_state.confirm_clear = False
if 'show_db_info' not in st.session_state:
    st.session_state.show_db_info = False
if 'current_image_path' not in st.session_state:
    st.session_state.current_image_path = None

# Add custom CSS for the new design
st.markdown("""
    <style>
    /* Main container styling */
    .main .block-container {
        padding: 2rem 1rem !important;
        max-width: 1200px;
    }
    
    /* Sidebar styling - Purple/Blue theme */
    [data-testid="stSidebar"] {
        min-width: 400px !important;
        max-width: 300px !important;
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 1px solid #4e4376;
    }
    [data-testid="stSidebarContent"] {
        padding: 1.5rem 1rem !important;
    }
    
    /* Button styling */
    div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #6e45e2 0%, #88d3ce 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        color: white !important;
        height: 42px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    div[data-testid="stButton"] button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
        background: linear-gradient(135deg, #6e45e2 0%, #88d3ce 100%) !important;
        opacity: 0.9;
    }
    
    div[data-testid="stButton"] button:active {
        transform: translateY(0);
    }
    
    /* Secondary button styling */
    div[data-testid="stButton"] button[kind="secondary"] {
        background: linear-gradient(135deg, #4e4376 0%, #2b5876 100%) !important;
    }
    
    /* Fix button width in columns */
    [data-testid="column"] > div > div > div > div > div[data-testid="stButton"] {
        width: 100%;
        min-width: 100%;
    }
    [data-testid="column"] > div > div > div > div > div[data-testid="stButton"] > button {
        width: 100%;
        min-width: 100%;
    }
    
    /* Column styling */
    [data-testid="column"] {
        padding: 0 1rem !important;
        background: rgba(30, 30, 46, 0.7);
        border-radius: 12px;
        border: 1px solid #4e4376;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    [data-testid="column"]:hover {
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        border-color: #6e45e2;
    }
    
    /* Text input styling */
    .stTextArea textarea, .stTextInput input {
        background: rgba(30, 30, 46, 0.7) !important;
        border: 1px solid #4e4376 !important;
        border-radius: 8px !important;
        color: white !important;
        padding: 10px !important;
    }
    
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #6e45e2 !important;
        box-shadow: 0 0 0 2px rgba(110, 69, 226, 0.2) !important;
    }
    
    /* Expander styling */
    .streamlit-expander {
        background: rgba(30, 30, 46, 0.7) !important;
        border: 1px solid #4e4376 !important;
        border-radius: 8px !important;
    }
    
    .streamlit-expanderHeader {
        color: #88d3ce !important;
        font-weight: 600 !important;
    }
    
    /* Header styling */
    h1, h2, h3, h4, h5, h6 {
        color: #88d3ce !important;
    }
    
    /* Image container styling */
    .stImage {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #4e4376;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1a2e;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #4e4376;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #6e45e2;
    }
    
    /* Special styling for delete buttons */
    div[data-testid="column"]:last-child button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid #ff4b4b !important;
        color: #ff4b4b !important;
        padding: 0 !important;
        width: 24px !important;
        height: 24px !important;
        min-width: 24px !important;
        min-height: 24px !important;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50% !important;
    }
    
    div[data-testid="column"]:last-child button[kind="secondary"]:hover {
        background: rgba(255, 75, 75, 0.1) !important;
        color: #ff0000 !important;
        border-color: #ff0000 !important;
    }
    
    /* Divider styling */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #4e4376, transparent);
        margin: 1rem 0;
    }
    
    /* Info boxes */
    .stAlert {
        background: rgba(30, 30, 46, 0.8) !important;
        border: 1px solid #4e4376 !important;
        border-radius: 8px !important;
    }
    
    /* Success message */
    .stAlert [data-testid="stMarkdownContainer"] {
        color: #88d3ce !important;
    }
    
    /* Warning message */
    .stWarning {
        background: rgba(78, 67, 118, 0.3) !important;
        border: 1px solid #6e45e2 !important;
    }
    
    /* Error message */
    .stError {
        background: rgba(255, 75, 75, 0.1) !important;
        border: 1px solid #ff4b4b !important;
    }
    </style>
""", unsafe_allow_html=True)

# Create a container for the modal at the top level
modal_placeholder = st.empty()

# Show database info modal if state is True
if st.session_state.show_db_info:
    db_info = managers['memory'].get_database_info()
    show_database_info(
        db_info=db_info,
        on_close=lambda: setattr(st.session_state, 'show_db_info', False)
    )

# Sidebar with search and history - Enhanced design
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <h2 style="color: #88d3ce; margin-bottom: 0.5rem;"> Memory & History</h2>
            <div style="height: 2px; background: linear-gradient(90deg, transparent, #6e45e2, transparent); margin: 0 auto 1rem; width: 80%;"></div>
        </div>
    """, unsafe_allow_html=True)
    
    search_query = st.text_input("Search by prompt:", key="search_box", 
                                placeholder="Search your past generations...")
    
    if search_query:
        results = managers['memory'].search_generations(search_query)
        if results:
            st.write(f"Found {len(results)} results:")
            for idx, result in enumerate(results):
                with st.expander(f"{result['prompt'][:40]}...", expanded=False):
                    st.write("**Original Prompt:**")
                    st.write(result['prompt'])
                    if result['enhanced_prompt']:
                        st.write("**Enhanced Prompt:**")
                        st.write(result['enhanced_prompt'])
                    if result['image_path'] and os.path.exists(result['image_path']):
                        st.image(result['image_path'], use_column_width=True)
                    if result['model_path'] and os.path.exists(result['model_path']):
                        st.download_button(
                            "Download 3D Model",
                            data=open(result['model_path'], 'rb').read(),
                            file_name=os.path.basename(result['model_path']),
                            mime="model/gltf-binary",
                            key=f"download_search_{idx}"
                        )
                    if st.button("Use as Reference", key=f"ref_search_{idx}"):
                        st.session_state.reference_prompt = result['prompt']
                        st.session_state.reference_image = result['image_path']
                        st.session_state.reference_id = result['id']
                        st.session_state.enhanced_prompt = result['enhanced_prompt']
                        if result['image_path'] and os.path.exists(result['image_path']):
                            st.session_state.current_image = open(result['image_path'], 'rb').read()
                            st.session_state.current_image_path = result['image_path']
                        st.session_state["prompt_input"] = result['prompt']
                        st.rerun()
        else:
            st.info("No matching generations found.")
    
    # Recent generations with enhanced design
    st.markdown("""
        <div style="margin: 1.5rem 0 0.5rem;">
            <h3 style="color: #88d3ce; margin-bottom: 0;">Recent Generations</h3>
            <div style="height: 1px; background: linear-gradient(90deg, transparent, #4e4376, transparent); margin: 0.25rem 0 0.5rem;"></div>
        </div>
    """, unsafe_allow_html=True)
    
    history = managers['memory'].get_generations(limit=10)
    
    if history:
        for idx, gen in enumerate(history):
            with st.container():
                title = gen['prompt'][:30] + "..." if len(gen['prompt']) > 30 else gen['prompt']
                with st.expander(title, expanded=False):
                    col1, col2 = st.columns([0.92, 0.08])
                    with col1:
                        st.markdown(f"<em style='color: #88d3ce;'>{format_timestamp(gen.get('created_at', 'Unknown'))}</em>", unsafe_allow_html=True)
                    with col2:
                        if st.button("✕", key=f"delete_recent_{idx}", help="Delete this generation", type="secondary", use_container_width=True):
                            if managers['memory'].delete_generation(gen['id']):
                                st.rerun()
                            else:
                                st.error("Failed to delete generation.")
                    
                    if gen['image_path'] and os.path.exists(gen['image_path']):
                        st.image(gen['image_path'], use_column_width=True)
                    
                    st.markdown('<div class="sidebar-buttons">', unsafe_allow_html=True)
                    
                    if st.button("📎 Use as Reference", key=f"ref_recent_{idx}", help="Use as Reference"):
                        st.session_state.reference_prompt = gen['prompt']
                        st.session_state.reference_image = gen['image_path']
                        st.session_state.reference_id = gen['id']
                        st.session_state.enhanced_prompt = gen['enhanced_prompt']
                        st.session_state.current_image = open(gen['image_path'], 'rb').read() if gen['image_path'] and os.path.exists(gen['image_path']) else None
                        st.session_state.current_image_path = gen['image_path']
                        st.session_state["prompt_input"] = gen['prompt']
                        st.rerun()
                    
                    if gen['model_path'] and os.path.exists(gen['model_path']):
                        st.download_button(
                            " Download 3D Model",
                            data=open(gen['model_path'], 'rb').read(),
                            file_name=os.path.basename(gen['model_path']),
                            mime="model/gltf-binary",
                            key=f"download_recent_{idx}",
                            help="Download 3D Model"
                        )
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<hr style="margin: 5px 0;">', unsafe_allow_html=True)
    else:
        st.info("No stored generations yet. Start creating to see your history here.")
    
    # Database viewer button
    st.markdown("""
        <div style="margin-top: 1.5rem;">
            <div style="height: 1px; background: linear-gradient(90deg, transparent, #4e4376, transparent); margin: 0.5rem 0;"></div>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button(" View Database Info", use_container_width=True):
        st.session_state.show_db_info = True
    
    # Clear All button
    if st.button(" Clear All History", type="secondary", use_container_width=True):
        st.session_state.confirm_clear = True
    
    if st.session_state.confirm_clear:
        st.warning("Are you sure you want to clear all history? This cannot be undone.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(" Yes, Clear All"):
                try:
                    for item in history:
                        try:
                            if item['image_path'] and os.path.exists(item['image_path']):
                                os.remove(item['image_path'])
                            if item['model_path'] and os.path.exists(item['model_path']):
                                os.remove(item['model_path'])
                        except Exception as e:
                            logging.error(f"Error deleting files: {e}")
                    
                    if managers['memory'].clear_database():
                        for key in ['current_image', 'current_model', 'enhanced_prompt', 
                                    'reference_prompt', 'reference_image', 'reference_id']:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.session_state.confirm_clear = False
                        st.success("History cleared successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to clear history. Please try again.")
                except Exception as e:
                    logging.error(f"Error during cleanup: {e}")
                    st.error("Failed to clear history. Please try again.")
        with col2:
            if st.button("No, Cancel"):
                st.session_state.confirm_clear = False
                st.rerun()

# Main content with enhanced design
st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: #88d3ce; margin-bottom: 0.5rem;">AI - Text to 3D Model Generator</h1>
        <div style="height: 2px; background: linear-gradient(90deg, transparent, #6e45e2, transparent); margin: 0 auto 1rem; width: 60%;"></div>
        <p style="color: #a1a1b5; font-size: 1.1rem;">Transform your text descriptions into stunning images and 3D models using AI</p>
    </div>
""", unsafe_allow_html=True)

st.markdown('<div style="padding: 0 1rem;">', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    # Text to Image section with enhanced design
    st.markdown("""
        <div style="background: linear-gradient(90deg, rgba(110, 69, 226, 0.1), rgba(136, 211, 206, 0.1));
                    padding: 1rem;
                    border-radius: 12px;
                    border-left: 4px solid #6e45e2;
                    margin-bottom: 1.5rem;">
            <h2 style="color: #88d3ce; margin-bottom: 0.5rem;">Text to Image Generation</h2>
        </div>
    """, unsafe_allow_html=True)
    
    prompt = st.text_area(
        "Enter your prompt:", 
        height=120,
        key="prompt_input",
        placeholder="Example: A beautiful glowing dragon standing on a cliff at sunset"
    )
    
    if st.button("Generate Image", key="generate_btn", type="primary", use_container_width=True):
        if prompt:
            try:
                with st.spinner("Enhancing prompt with AI..."):
                    enhanced_prompt = managers['llm'].enhance_prompt(prompt)
                    st.session_state.enhanced_prompt = enhanced_prompt
                
                with st.spinner("Generating image..."):
                    image_data = managers['openfabric'].generate_image(enhanced_prompt)
                    if image_data:
                        image_path = save_binary_to_file(
                            image_data, 
                            "outputs/images", 
                            "generated", 
                            "png"
                        )
                        if image_path:
                            st.session_state.current_image = image_data
                            st.session_state.current_image_path = image_path  
                            
                            managers['memory'].save_generation(
                                prompt=prompt,
                                enhanced_prompt=enhanced_prompt,
                                image_path=image_path
                            )
                        else:
                            st.error("Failed to save generated image")
                    else:
                        st.error("Failed to generate image")
            except Exception as e:
                logging.error(f"Error in generation pipeline: {e}")
                st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please enter a prompt first")
    
    if st.session_state.enhanced_prompt:
        with st.expander("Enhanced Prompt", expanded=False):
            st.info(st.session_state.enhanced_prompt)
    
    if st.session_state.current_image:
        image_container = st.empty()
        image_container.image(st.session_state.current_image, caption="Generated Image", use_column_width=True)
        
        st.markdown("""
            <div style="background: linear-gradient(90deg, rgba(110, 69, 226, 0.1), rgba(136, 211, 206, 0.1));
                        padding: 1rem;
                        border-radius: 12px;
                        border-left: 4px solid #88d3ce;
                        margin: 1.5rem 0;">
                <h3 style="color: #88d3ce; margin-bottom: 0.5rem;"> Edit Your Image</h3>
            </div>
        """, unsafe_allow_html=True)
        
        edit_prompt = st.text_input(
            "Describe what you want to change:",
            placeholder="Example: make it more colorful, add sparkles, change background to night"
        )
        
        if st.button("Update Image", key="update_btn", type="primary", use_container_width=True):
            if edit_prompt:
                try:
                    with st.spinner("Enhancing edit prompt..."):
                        previous_prompt = st.session_state.enhanced_prompt
                        enhanced_edit_prompt = managers['llm'].enhance_edit_prompt(
                            current_prompt=previous_prompt,
                            edit_request=edit_prompt
                        )
                        st.session_state.enhanced_prompt = enhanced_edit_prompt
                        
                        with st.expander("View prompt changes", expanded=False):
                            st.write("**Original Prompt:**")
                            st.write(previous_prompt)
                            st.write("**Requested Change:**")
                            st.write(edit_prompt)
                            st.write("**New Enhanced Prompt:**")
                            st.write(enhanced_edit_prompt)
                    
                    with st.spinner("Updating image..."):
                        image_data = managers['openfabric'].generate_image(enhanced_edit_prompt)
                        if image_data:
                            image_path = save_binary_to_file(
                                image_data, 
                                "outputs/images", 
                                "generated", 
                                "png"
                            )
                            if image_path:
                                st.session_state.current_image = image_data
                                st.session_state.current_image_path = image_path
                                image_container.image(image_data, caption="Generated Image", use_column_width=True)
                                
                                metadata = {
                                    "edit_history": {
                                        "original_prompt": prompt if 'prompt' in locals() else "unknown",
                                        "edit_prompt": edit_prompt,
                                        "previous_enhanced_prompt": previous_prompt,
                                        "timestamp": datetime.now().isoformat()
                                    }
                                }
                                
                                managers['memory'].save_generation(
                                    prompt=edit_prompt,
                                    enhanced_prompt=enhanced_edit_prompt,
                                    image_path=image_path,
                                    metadata=metadata
                                )
                                
                                st.success("Image updated successfully!")
                            else:
                                st.error("Failed to save updated image")
                        else:
                            st.error("Failed to update image")
                except Exception as e:
                    logging.error(f"Error in image update pipeline: {e}")
                    st.error(f"An error occurred: {str(e)}")
            else:
                st.warning("Please describe what changes you want to make")

with col2:
    # Image to 3D section with enhanced design
    st.markdown("""
        <div style="background: linear-gradient(90deg, rgba(110, 69, 226, 0.1), rgba(136, 211, 206, 0.1));
                    padding: 1rem;
                    border-radius: 12px;
                    border-left: 4px solid #6e45e2;
                    margin-bottom: 1.5rem;
                    height: 120px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;">
            <h2 style="color: #88d3ce; margin-bottom: 0.5rem;">Image to 3D Model Generation</h2>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.current_image is not None:
        if st.button("Convert to 3D Model", key="convert_btn", type="primary", use_container_width=True):
            try:
                with st.spinner("Converting image to 3D model..."):
                    model_data = managers['openfabric'].convert_to_3d(
                        st.session_state.current_image,
                        image_path=st.session_state.current_image_path
                    )
                    if model_data:
                        model_path = save_binary_to_file(
                            model_data.get("model", b""),
                            "outputs/models",
                            "model",
                            "glb"
                        )
                        if model_path:
                            st.session_state.current_model = model_data.get("model", b"")
                            managers['memory'].save_generation(
                                prompt=prompt if 'prompt' in locals() else "",
                                enhanced_prompt=st.session_state.enhanced_prompt,
                                image_path=st.session_state.current_image_path,
                                model_path=model_path
                            )
                            st.success("3D model generated successfully!")
                        else:
                            st.error("Failed to save 3D model")
                    else:
                        st.error("Failed to generate 3D model")
            except Exception as e:
                logging.error(f"Error converting to 3D: {e}")
                st.error(f"An error occurred: {str(e)}")
    else:
        st.markdown("""
            <div style="background: rgba(30, 30, 46, 0.5);
                        border: 1px dashed #4e4376;
                        border-radius: 12px;
                        padding: 2rem;
                        text-align: center;
                        margin-top: 2rem;">
                <p style="color: #88d3ce; font-size: 1rem;">Generate an image first to convert it to a 3D model</p>
            </div>
        """, unsafe_allow_html=True)
    
    if st.session_state.current_model is not None:
        st.markdown("""
            <div style="margin-top: 1.5rem;
                        background: linear-gradient(90deg, rgba(110, 69, 226, 0.1), rgba(136, 211, 206, 0.1));
                        padding: 1rem;
                        border-radius: 12px;
                        border-left: 4px solid #88d3ce;">
                <h3 style="color: #88d3ce; margin-bottom: 0.5rem;">3D Model Preview</h3>
            </div>
        """, unsafe_allow_html=True)
        
        st.components.v1.html(
            create_model_viewer_html(st.session_state.current_model),
            height=400,
            scrolling=False
        )
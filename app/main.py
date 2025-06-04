import logging
from typing import Dict

from ontology_dc8f06af066e4a7880a5938933236037.config import ConfigClass
from ontology_dc8f06af066e4a7880a5938933236037.input import InputClass
from ontology_dc8f06af066e4a7880a5938933236037.output import OutputClass
from openfabric_pysdk.context import AppModel, State
from core.stub import Stub

# Configurations for the app
configurations: Dict[str, ConfigClass] = dict()

############################################################
# Config callback function
############################################################
def config(configuration: Dict[str, ConfigClass], state: State) -> None:
    """
    Stores user-specific configuration data.

    Args:
        configuration (Dict[str, ConfigClass]): A mapping of user IDs to configuration objects.
        state (State): The current state of the application (not used in this implementation).
    """
    for uid, conf in configuration.items():
        logging.info(f"Saving new config for user with id:'{uid}'")
        configurations[uid] = conf


############################################################
# Execution callback function
############################################################
def execute(model: AppModel) -> None:
    try:
        # Initialize components
        llm = LLM()
        memory = Memory()
        request: InputClass = model.request
        user_config: ConfigClass = configurations.get('super-user', None)  # Assumes configurations is defined
        app_ids = user_config.app_ids if user_config else []
        openfabric = OpenfabricClient(app_ids)

        # Get user prompt
        prompt = request.prompt
        if not prompt:
            raise ValueError("No prompt provided")
        logging.info(f"Received prompt: {prompt}")

        # Enhance prompt with LLM
        enhanced_prompt = llm.enhance_prompt(prompt)
        logging.info(f"Enhanced prompt: {enhanced_prompt}")

        # Generate image
        image_data = openfabric.generate_image(enhanced_prompt)
        os.makedirs('outputs', exist_ok=True)
        image_path = f"outputs/image_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
        with open(image_path, 'wb') as f:
            f.write(image_data)
        logging.info(f"Image saved to {image_path}")

        # Generate 3D model
        model_3d_data = openfabric.generate_3d_model(image_data)
        model_3d_path = f"outputs/model_3d_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.obj"
        with open(model_3d_path, 'wb') as f:
            f.write(model_3d_data)
        logging.info(f"3D model saved to {model_3d_path}")

        # Save to memory
        memory.save_creation(prompt, enhanced_prompt, image_path, model_3d_path)

        # Prepare response
        response: OutputClass = model.response
        response.message = f"Created image at {image_path} and 3D model at {model_3d_path}"
    except Exception as e:
        logging.error(f"Execution failed: {e}")
        response: OutputClass = model.response
        response.message = f"Error: {str(e)}"
    
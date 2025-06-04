import logging
import requests
import base64
import os
import time
from typing import Dict, Any, Optional, Tuple
from core.stub import Stub

class OpenfabricManager:
    """
    Manager class for handling Openfabric API interactions
    """
    def __init__(self):
       
        # App IDs 
        self.text_to_image_app_id = "c25dcd829d134ea98f5ae4dd311d13bc.node3.openfabric.network"
        self.image_to_3d_app_id = "f0b5f319156c4819b9827000b17e511a.node3.openfabric.network"
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 2  # in seconds
        
        # Initialize stub
        self.stub = Stub([self.text_to_image_app_id, self.image_to_3d_app_id])
    
    def _call_with_retry(self, app_id: str, data: Dict[str, Any], user_id: str = "super-user") -> Optional[Dict[str, Any]]:
        """
        Call Openfabric API with retry logic
        
        Args:
            app_id (str): The application ID to call
            data (Dict[str, Any]): The data to send
            user_id (str): User identifier for the request
            
        Returns:
            Optional[Dict[str, Any]]: Response data if successful, None otherwise
        """
        for attempt in range(self.max_retries):
            try:
                response = self.stub.call(app_id, data, user_id)
                if response:
                    return response
            except Exception as e:
                if "Resource not found" in str(e):
                    if attempt < self.max_retries - 1:
                        logging.info(f"Resource not ready, retrying in {self.retry_delay} seconds... (Attempt {attempt + 1}/{self.max_retries})")
                        time.sleep(self.retry_delay)
                        continue
                logging.error(f"Error calling Openfabric API: {e}")
            
        return None
        
    def generate_image(self, prompt: str, user_id: str = "super-user") -> Optional[bytes]:
        """
        Generate image from text prompt using Openfabric's text-to-image
        
        Args:
            prompt (str): Text prompt for image generation
            
        Returns:
            Optional[bytes]: Generated image data if successful, None otherwise
        """
        try:
            response = self._call_with_retry(
                self.text_to_image_app_id,
                {"prompt": prompt},
                user_id
            )
            
            if isinstance(response, dict) and 'result' in response:
                return response['result']
                
            logging.error(f"Invalid response format: {response}")
            return None
        except Exception as e:
            logging.error(f"Error generating image: {e}")
            return None
            
    def convert_to_3d(self, image_data: bytes, user_id: str = "super-user", image_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Convert image to 3D model using Openfabric's image-to-3D API
        
        Args:
            image_data (bytes): Input image data
            image_path (Optional[str]): Path to the input image file
            
        Returns:
            Optional[Dict[str, Any]]: 3D model data if successful, None otherwise
        """
        try:
            
            # Convert bytes to base64 string
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            response = self._call_with_retry(
                self.image_to_3d_app_id,
                {"input_image": image_base64},
                user_id
            )
            
            if response and isinstance(response, dict):
                result = {}
                if 'generated_object' in response:
                    result['model'] = response['generated_object']
                if 'video_object' in response:
                    # Include video if present
                    result['video'] = response['video_object']
                return result
            
            logging.error(f"Invalid response format: {response}")
            return None
        except Exception as e:
            logging.error(f"Error converting to 3D: {e}")
            return None 
import requests
import logging
from typing import Dict, Any

class LLMManager:
    """
    Manager class for handling interactions with Ollama LLM
    """
    def __init__(self, model_name: str = "llama3:latest"):
        self.model_name = model_name
        self.base_url = "http://localhost:11434"
        
    def generate(self, prompt: str) -> Dict[str, Any]:
        """
        Generate response from Ollama LLM
        
        Args:
            prompt (str): Input prompt for the LLM
            
        Returns:
            Dict[str, Any]: Response from LLM containing generated text
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                }
            )
            return response.json()
        except Exception as e:
            logging.error(f"Error generating LLM response: {e}")
            return {"error": str(e)}
    
    def enhance_prompt(self, prompt: str) -> str:
        """
        Enhance the user prompt for better image generation
        
        Args:
            prompt (str): Original user prompt
            
        Returns:
            str: Enhanced prompt for image generation
        """
        system_prompt = """You are an expert AI art director specializing in creating vivid, detailed image generation prompts.
            Your task is to enhance simple prompts into rich, detailed descriptions that will guide an AI image generator.

            Guidelines for enhancement:
            1. Visual Elements:
            - Lighting: Time of day, shadows, highlights, ambient effects
            - Colors: Specific color palettes, tones, and color relationships
            - Textures: Surface details, materials, and tactile qualities
            - Atmosphere: Weather, mood, environmental effects

            2. Composition:
            - Camera angle and perspective
            - Focal points and subject placement
            - Depth and layering
            - Scale and proportions

            3. Artistic Style:
            - Specific art movements or techniques
            - Rendering style and medium
            - Quality descriptors (photorealistic, painterly, etc.)

            Respond ONLY with the enhanced prompt, no explanations or additional text and it should not exceed 60 words."""
        
        try:
            response = self.generate(
                f"{system_prompt}\n\nUser prompt: {prompt}\nEnhanced prompt:"
            )
            return response.get("response", prompt)
        except Exception as e:
            logging.error(f"Error enhancing prompt: {e}")
            return prompt
        
    def enhance_edit_prompt(self, current_prompt: str, edit_request: str) -> str:
        """
        Create an enhanced prompt for image editing that maintains consistency
        while applying specific changes.
        
        Args:
            current_prompt (str): The prompt that generated the current image
            edit_request (str): The requested changes to make
            
        Returns:
            str: Enhanced prompt that incorporates the requested changes while
                maintaining consistency with the original
        """
        context_prompt = f"""You are an expert at maintaining image consistency while applying specific changes.

            CURRENT IMAGE PROMPT: "{current_prompt}"

            REQUESTED CHANGE: "{edit_request}"

            TASK:
            1. Analyze the current image prompt carefully
            2. Identify only the specific elements mentioned in the requested change
            3. Create a new prompt that:
            - Keeps ALL original elements not mentioned in the change request
            - Modifies ONLY the aspects explicitly mentioned in the change request
            - Maintains the same style and composition
            - Preserves the main subject and its key characteristics

            RULES:
            - Do NOT add new major elements unless explicitly requested
            - Do NOT change any aspects not mentioned in the change request
            - Do NOT alter the core subject's identity or main characteristics
            - DO preserve all specific details from the original prompt that aren't being modified

            Generate a new prompt that follows these rules and maintains maximum consistency with the original while applying only the requested changes.
            NEW PROMPT:"""

        return self.enhance_prompt(context_prompt) 
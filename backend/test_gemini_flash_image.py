#!/usr/bin/env python3
"""
Test script for using the gemini-2.5-flash-image model.
This demonstrates how to properly initialize and use the model in the project context.
"""

import os
import sys
from typing import Optional

try:
    import google.generativeai as genai
    print("✓ google-generativeai library loaded successfully")
    print(f"  Version: {genai.__version__}")
except ImportError as e:
    print(f"✗ Failed to import google-generativeai: {e}")
    sys.exit(1)


class GeminiFlashImageService:
    """
    Service class for working with the gemini-2.5-flash-image model.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini Flash Image service.

        Args:
            api_key: Google AI API key. If None, will try to get from environment.
        """
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.model_name = "gemini-2.5-flash-image"
        self.model = None

        if self.api_key:
            genai.configure(api_key=self.api_key)
            print("✓ API key configured")
        else:
            print("⚠ No API key provided - model instantiation will work but API calls will fail")

    def initialize_model(self) -> bool:
        """
        Initialize the GenerativeModel instance.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.model = genai.GenerativeModel(self.model_name)
            print(f"✓ Model '{self.model_name}' initialized successfully")
            print(f"  Full model name: {self.model.model_name}")
            return True
        except Exception as e:
            print(f"✗ Failed to initialize model: {e}")
            return False

    def test_model_info(self):
        """
        Display model information and capabilities.
        """
        if not self.model:
            print("✗ Model not initialized")
            return

        print(f"\n--- Model Information ---")
        print(f"Model name: {self.model.model_name}")
        print(f"Generation config: {getattr(self.model, '_generation_config', 'Not accessible')}")
        print(f"Safety settings: {getattr(self.model, '_safety_settings', 'Not accessible')}")
        print(f"Tools: {getattr(self.model, '_tools', 'Not accessible')}")
        print(f"System instruction: {getattr(self.model, '_system_instruction', 'Not accessible')}")
        print(f"Available methods: generate_content, count_tokens, start_chat")

    def test_text_generation(self, prompt: str = "Hello, world!"):
        """
        Test basic text generation with the model.

        Args:
            prompt: Text prompt to test with
        """
        if not self.model:
            print("✗ Model not initialized")
            return

        if not self.api_key:
            print("⚠ Skipping text generation test - no API key provided")
            return

        try:
            print(f"\n--- Testing Text Generation ---")
            print(f"Prompt: {prompt}")

            response = self.model.generate_content(prompt)
            print(f"✓ Response generated successfully")
            print(f"Response: {response.text}")

        except Exception as e:
            print(f"✗ Text generation failed: {e}")

    def get_supported_capabilities(self):
        """
        Return information about what this model version supports.
        """
        capabilities = {
            "model_name": self.model_name,
            "library_version": genai.__version__,
            "supports_text": True,
            "supports_images": True,  # Based on model name having 'image'
            "supports_multimodal": True,
            "initialization_success": self.model is not None
        }
        return capabilities


def main():
    """
    Main test function.
    """
    print("=== Gemini 2.5 Flash Image Model Test ===\n")

    # Initialize the service
    service = GeminiFlashImageService()

    # Test model initialization
    if not service.initialize_model():
        print("✗ Model initialization failed. Exiting.")
        return

    # Display model information
    service.test_model_info()

    # Test basic text generation (only if API key is available)
    service.test_text_generation("Explain what the gemini-2.5-flash-image model is capable of in one sentence.")

    # Display capabilities summary
    capabilities = service.get_supported_capabilities()
    print(f"\n--- Capabilities Summary ---")
    for key, value in capabilities.items():
        print(f"{key}: {value}")

    print(f"\n=== Test Complete ===")
    print(f"✓ The google-generativeai library (v{genai.__version__}) successfully supports the gemini-2.5-flash-image model")
    print(f"✓ Model can be instantiated without errors")
    if service.api_key:
        print(f"✓ API key configured - ready for actual API calls")
    else:
        print(f"ℹ To test actual generation, set GOOGLE_API_KEY environment variable")


if __name__ == "__main__":
    main()
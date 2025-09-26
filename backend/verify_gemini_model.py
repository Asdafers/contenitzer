#!/usr/bin/env python3
"""
Verification script to test google-generativeai library support for gemini-2.5-flash-image model.
"""

import os
import sys
from typing import Dict, Any
import traceback

try:
    import google.generativeai as genai
    print("✓ google-generativeai library imported successfully")
    print(f"  Version: {genai.__version__}")
except ImportError as e:
    print(f"✗ Failed to import google-generativeai: {e}")
    sys.exit(1)


def verify_model_support(model_name: str) -> Dict[str, Any]:
    """
    Verify if a specific model is supported by the google-generativeai library.

    Args:
        model_name: The name of the model to verify (e.g., "gemini-2.5-flash-image")

    Returns:
        Dict containing verification results
    """
    result = {
        "model_name": model_name,
        "supported": False,
        "error": None,
        "model_info": None
    }

    try:
        # Attempt to create a GenerativeModel instance
        model = genai.GenerativeModel(model_name)
        result["supported"] = True
        result["model_info"] = {
            "model_name": model.model_name,
            "model": str(model)
        }
        print(f"✓ Model '{model_name}' is supported")
        print(f"  Model instance created: {model}")

    except Exception as e:
        result["error"] = str(e)
        result["error_type"] = type(e).__name__
        print(f"✗ Model '{model_name}' verification failed: {e}")
        print(f"  Error type: {type(e).__name__}")

    return result


def list_available_models():
    """
    List available models to understand what's supported.
    """
    try:
        print("\n--- Attempting to list available models ---")
        models = genai.list_models()
        available_models = []

        for model in models:
            available_models.append(model.name)
            print(f"  - {model.name}")

        return available_models

    except Exception as e:
        print(f"✗ Failed to list models: {e}")
        print("  Note: This might require API key configuration")
        return []


def main():
    """
    Main verification function.
    """
    print("=== Google Generative AI Library Model Verification ===\n")

    # Test the specific model we're interested in
    target_model = "gemini-2.5-flash-image"
    result = verify_model_support(target_model)

    # Also test some known models for comparison
    known_models = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro",
        "gemini-pro-vision"
    ]

    print(f"\n--- Testing other known models for comparison ---")
    for model_name in known_models:
        verify_model_support(model_name)

    # Try to list available models (might require API key)
    available_models = list_available_models()

    # Summary
    print(f"\n=== Summary ===")
    print(f"Target model '{target_model}' supported: {result['supported']}")
    if result['error']:
        print(f"Error: {result['error']}")

    print(f"\nGoogle Generative AI library version: {genai.__version__}")

    if not result['supported']:
        print(f"\nRecommendations:")
        print(f"1. Check if '{target_model}' is the correct model name")
        print(f"2. Verify if the model requires API key configuration")
        print(f"3. Consider updating google-generativeai to the latest version")
        print(f"4. Check official Google documentation for supported models")

    return result


if __name__ == "__main__":
    main()
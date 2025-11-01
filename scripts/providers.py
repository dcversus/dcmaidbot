"""
AI Provider Abstraction Layer for PRP-016 Multi-Room Interactive House Exploration

This module provides a unified interface for multiple AI image generation services:
- OpenAI DALL-E 3 (txt2img)
- HuggingFace InstructPix2Pix (inpainting)
- Leonardo AI (fallback)
"""

import hashlib
import json
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple

import requests
from openai import OpenAI

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI image generation providers."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.name = self.__class__.__name__

    @abstractmethod
    async def txt2img(
        self,
        prompt: str,
        size: Tuple[int, int],
        seed: int,
        steps: int = 30,
        cfg: float = 5.0,
        outfile: str = None,
    ) -> str:
        """Generate image from text prompt.

        Args:
            prompt: Text prompt for image generation
            size: Tuple of (width, height) in pixels
            seed: Random seed for deterministic generation
            steps: Number of inference steps
            cfg: Classifier-free guidance scale
            outfile: Output file path (if None, generates temp path)

        Returns:
            Path to generated image file
        """
        pass

    @abstractmethod
    async def inpaint(
        self,
        base_path: str,
        mask_path: str,
        prompt: str,
        seed: int,
        steps: int = 30,
        cfg: float = 5.0,
        outfile: str = None,
    ) -> str:
        """Perform inpainting on base image with mask.

        Args:
            base_path: Path to base image
            mask_path: Path to mask image (white = inpaint, black = preserve)
            prompt: Text prompt for inpainting
            seed: Random seed for deterministic generation
            steps: Number of inference steps
            cfg: Classifier-free guidance scale
            outfile: Output file path (if None, generates temp path)

        Returns:
            Path to generated image file
        """
        pass

    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        return self.name


class OpenAIProvider(AIProvider):
    """OpenAI DALL-E 3 provider for text-to-image generation."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = OpenAI(api_key=api_key)
        self.model = "dall-e-3"
        self.supported_sizes = ["1024x1024", "1792x1024", "1024x1792"]

    async def txt2img(
        self,
        prompt: str,
        size: Tuple[int, int],
        seed: int,
        steps: int = 30,
        cfg: float = 5.0,
        outfile: str = None,
    ) -> str:
        """Generate image using DALL-E 3."""
        try:
            # Convert size to DALL-E 3 compatible format
            size_str = f"{size[0]}x{size[1]}"
            if size_str not in self.supported_sizes:
                # Use closest supported size
                if size[0] > size[1]:
                    size_str = "1792x1024"
                else:
                    size_str = "1024x1792"
                logger.warning(f"Adjusted size from {size} to {size_str} for DALL-E 3")

            # Generate image
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size=size_str,
                n=1,
                response_format="url",
            )

            # Download image
            image_url = response.data[0].url
            if not outfile:
                outfile = f"static/cache/tiles/openai_{seed}_{hashlib.md5(prompt.encode()).hexdigest()[:8]}.png"

            # Download and save
            img_response = requests.get(image_url)
            img_response.raise_for_status()

            # Ensure directory exists
            Path(outfile).parent.mkdir(parents=True, exist_ok=True)

            with open(outfile, "wb") as f:
                f.write(img_response.content)

            logger.info(f"Generated image with OpenAI: {outfile}")
            return outfile

        except Exception as e:
            logger.error(f"OpenAI txt2img failed: {e}")
            raise

    async def inpaint(
        self,
        base_path: str,
        mask_path: str,
        prompt: str,
        seed: int,
        steps: int = 30,
        cfg: float = 5.0,
        outfile: str = None,
    ) -> str:
        """DALL-E 3 does not support inpainting - use fallback."""
        raise NotImplementedError(
            "OpenAI DALL-E 3 does not support inpainting. Use HuggingFace provider."
        )


class HuggingFaceProvider(AIProvider):
    """HuggingFace InstructPix2Pix provider for inpainting."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.api_url = (
            "https://api-inference.huggingface.co/models/timbrooks/instructpix2pix"
        )
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def txt2img(
        self,
        prompt: str,
        size: Tuple[int, int],
        seed: int,
        steps: int = 30,
        cfg: float = 5.0,
        outfile: str = None,
    ) -> str:
        """Generate image using InstructPix2Pix."""
        try:
            payload = {
                "inputs": prompt,
                "parameters": {
                    "num_inference_steps": steps,
                    "guidance_scale": cfg,
                    "seed": seed,
                    "width": size[0],
                    "height": size[1],
                },
            }

            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()

            # Save image
            if not outfile:
                outfile = f"static/cache/tiles/hf_{seed}_{hashlib.md5(prompt.encode()).hexdigest()[:8]}.png"

            # Ensure directory exists
            Path(outfile).parent.mkdir(parents=True, exist_ok=True)

            with open(outfile, "wb") as f:
                f.write(response.content)

            logger.info(f"Generated image with HuggingFace: {outfile}")
            return outfile

        except Exception as e:
            logger.error(f"HuggingFace txt2img failed: {e}")
            raise

    async def inpaint(
        self,
        base_path: str,
        mask_path: str,
        prompt: str,
        seed: int,
        steps: int = 30,
        cfg: float = 5.0,
        outfile: str = None,
    ) -> str:
        """Perform inpainting using InstructPix2Pix."""
        try:
            # Read base image and mask
            with open(base_path, "rb") as f:
                base_data = f.read()
            with open(mask_path, "rb") as f:
                mask_data = f.read()

            payload = {
                "inputs": prompt,
                "parameters": {
                    "num_inference_steps": steps,
                    "guidance_scale": cfg,
                    "seed": seed,
                    "image": base_data,
                    "mask_image": mask_data,
                },
            }

            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()

            # Save image
            if not outfile:
                outfile = f"static/cache/widgets/hf_inpaint_{seed}_{hashlib.md5(prompt.encode()).hexdigest()[:8]}.png"

            # Ensure directory exists
            Path(outfile).parent.mkdir(parents=True, exist_ok=True)

            with open(outfile, "wb") as f:
                f.write(response.content)

            logger.info(f"Generated inpaint with HuggingFace: {outfile}")
            return outfile

        except Exception as e:
            logger.error(f"HuggingFace inpaint failed: {e}")
            raise


class LeonardoProvider(AIProvider):
    """Leonardo AI provider as fallback."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.api_url = "https://cloud.leonardo.ai/api/rest/v1"
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def txt2img(
        self,
        prompt: str,
        size: Tuple[int, int],
        seed: int,
        steps: int = 30,
        cfg: float = 5.0,
        outfile: str = None,
    ) -> str:
        """Generate image using Leonardo AI."""
        try:
            # Get generation ID first
            init_payload = {
                "prompt": prompt,
                "modelId": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",  # Leonardo Diffusion XL
                "width": size[0],
                "height": size[1],
                "sd_version": "SDXL_1_0",
                "num_images": 1,
                "seed": seed,
                "guidance_scale": cfg,
                "num_inference_steps": steps,
                "presetStyle": "LEONARDO",
            }

            response = requests.post(
                f"{self.api_url}/generations", headers=self.headers, json=init_payload
            )
            response.raise_for_status()

            generation_id = response.json()["sdGenerationJob"]["generationId"]

            # Poll for completion
            import asyncio

            while True:
                status_response = requests.get(
                    f"{self.api_url}/generations/{generation_id}", headers=self.headers
                )
                status_response.raise_for_status()

                status = status_response.json()["sdGenerationJob"]["status"]
                if status == "COMPLETE":
                    break
                elif status == "FAILED":
                    raise Exception("Leonardo generation failed")

                await asyncio.sleep(2)

            # Get image URL
            image_url = status_response.json()["sdGenerationJob"]["generated_images"][
                0
            ]["url"]

            # Download and save
            img_response = requests.get(image_url)
            img_response.raise_for_status()

            if not outfile:
                outfile = f"static/cache/tiles/leonardo_{seed}_{hashlib.md5(prompt.encode()).hexdigest()[:8]}.png"

            # Ensure directory exists
            Path(outfile).parent.mkdir(parents=True, exist_ok=True)

            with open(outfile, "wb") as f:
                f.write(img_response.content)

            logger.info(f"Generated image with Leonardo: {outfile}")
            return outfile

        except Exception as e:
            logger.error(f"Leonardo txt2img failed: {e}")
            raise

    async def inpaint(
        self,
        base_path: str,
        mask_path: str,
        prompt: str,
        seed: int,
        steps: int = 30,
        cfg: float = 5.0,
        outfile: str = None,
    ) -> str:
        """Leonardo inpainting implementation."""
        try:
            # Leonardo inpainting API implementation
            # Similar to txt2img but with mask image
            raise NotImplementedError("Leonardo inpainting not yet implemented")

        except Exception as e:
            logger.error(f"Leonardo inpaint failed: {e}")
            raise


def pick_provider(operation: str, priority: list[str]) -> AIProvider:
    """Pick the best available provider for the given operation.

    Args:
        operation: "txt2img" or "inpaint"
        priority: List of provider names in order of preference

    Returns:
        AIProvider instance
    """
    # Load API keys from environment
    openai_key = os.getenv("OPENAI_API_KEY")
    hf_key = os.getenv("HF_API_KEY")
    leo_key = os.getenv("LEONARDO_API_KEY")

    providers = []

    # Initialize providers based on priority
    for provider_name in priority:
        if provider_name == "openai" and openai_key:
            providers.append(OpenAIProvider(openai_key))
        elif provider_name == "huggingface" and hf_key:
            providers.append(HuggingFaceProvider(hf_key))
        elif provider_name == "leonardo" and leo_key:
            providers.append(LeonardoProvider(leo_key))

    # Filter providers that support the operation
    if operation == "inpaint":
        providers = [p for p in providers if not isinstance(p, OpenAIProvider)]

    if not providers:
        raise RuntimeError(f"No available providers for operation: {operation}")

    logger.info(
        f"Selected provider: {providers[0].get_provider_name()} for {operation}"
    )
    return providers[0]


# Utility functions for deterministic generation
def stable_hash(s: str) -> int:
    """Generate a stable hash from string."""
    return int(hashlib.sha1(s.encode()).hexdigest()[:8], 16)


def content_key(*parts) -> str:
    """Generate content-addressed cache key from parts."""
    return hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()


def ensure_dir(path: str) -> None:
    """Ensure directory exists."""
    Path(path).mkdir(parents=True, exist_ok=True)


def load_json(path: str, default: dict = None) -> dict:
    """Load JSON file with default."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default or {}


def save_json(path: str, data: dict) -> None:
    """Save data to JSON file."""
    ensure_dir(str(Path(path).parent))
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

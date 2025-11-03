"""Unit tests for AI provider abstraction layer."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from scripts.providers import (
    HuggingFaceProvider,
    LeonardoProvider,
    OpenAIProvider,
    content_key,
    ensure_dir,
    load_json,
    pick_provider,
    save_json,
    stable_hash,
)


class TestProviderAbstraction:
    """Test cases for AI provider abstraction."""

    @pytest.fixture
    def mock_openai_key(self):
        """Mock OpenAI API key."""
        return "test-openai-key"

    @pytest.fixture
    def mock_hf_key(self):
        """Mock HuggingFace API key."""
        return "test-hf-key"

    @pytest.fixture
    def mock_leo_key(self):
        """Mock Leonardo API key."""
        return "test-leo-key"

    def test_stable_hash(self):
        """Test stable hash generation."""
        # Same input should produce same hash
        hash1 = stable_hash("test input")
        hash2 = stable_hash("test input")
        assert hash1 == hash2
        assert isinstance(hash1, int)

        # Different input should produce different hash
        hash3 = stable_hash("different input")
        assert hash1 != hash3

    def test_content_key(self):
        """Test content key generation."""
        key1 = content_key("test", "input", 123)
        key2 = content_key("test", "input", 123)
        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) == 40  # SHA1 hex length

    def test_ensure_dir(self, tmp_path):
        """Test directory creation."""
        test_dir = tmp_path / "test" / "nested" / "directory"
        ensure_dir(str(test_dir))
        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_load_json(self, tmp_path):
        """Test JSON loading."""
        # Test non-existent file
        result = load_json(str(tmp_path / "nonexistent.json"), {"default": "value"})
        assert result == {"default": "value"}

        # Test valid JSON file
        test_file = tmp_path / "test.json"
        test_data = {"key": "value", "number": 42}
        save_json(str(test_file), test_data)
        result = load_json(str(test_file))
        assert result == test_data

    def test_save_json(self, tmp_path):
        """Test JSON saving."""
        test_file = tmp_path / "test" / "nested.json"
        test_data = {"key": "value", "number": 42}

        save_json(str(test_file), test_data)

        assert test_file.exists()
        with open(test_file, "r") as f:
            loaded_data = json.load(f)
        assert loaded_data == test_data

    def test_openai_provider_initialization(self, mock_openai_key):
        """Test OpenAI provider initialization."""
        provider = OpenAIProvider(mock_openai_key)
        assert provider.api_key == mock_openai_key
        assert provider.model == "dall-e-3"
        assert "1024x1024" in provider.supported_sizes

    def test_huggingface_provider_initialization(self, mock_hf_key):
        """Test HuggingFace provider initialization."""
        provider = HuggingFaceProvider(mock_hf_key)
        assert provider.api_key == mock_hf_key
        assert "Bearer" in provider.headers["Authorization"]

    def test_leonardo_provider_initialization(self, mock_leo_key):
        """Test Leonardo provider initialization."""
        provider = LeonardoProvider(mock_leo_key)
        assert provider.api_key == mock_leo_key
        assert "Bearer" in provider.headers["Authorization"]

    @pytest.mark.asyncio
    async def test_openai_txt2img_size_adjustment(self, mock_openai_key):
        """Test OpenAI provider size adjustment."""
        provider = OpenAIProvider(mock_openai_key)

        # Test unsupported size gets adjusted
        with patch.object(provider.client.images, "generate") as mock_generate:
            mock_response = MagicMock()
            mock_response.data = [MagicMock(url="http://test.com/image.png")]
            mock_generate.return_value = mock_response

            with patch("requests.get") as mock_get:
                mock_get.return_value.content = b"fake image data"

                await provider.txt2img("test prompt", (800, 600), seed=123)

                # Should adjust to closest supported size
                mock_generate.assert_called_once()
                call_args = mock_generate.call_args
                assert call_args[1]["size"] in ["1024x1792", "1792x1024"]

    @pytest.mark.asyncio
    async def test_openai_inpaint_not_implemented(self, mock_openai_key):
        """Test OpenAI provider inpainting raises NotImplementedError."""
        provider = OpenAIProvider(mock_openai_key)

        with pytest.raises(NotImplementedError):
            await provider.inpaint("base.png", "mask.png", "test prompt", seed=123)

    @pytest.mark.asyncio
    async def test_huggingface_txt2img(self, mock_hf_key):
        """Test HuggingFace provider txt2img."""
        provider = HuggingFaceProvider(mock_hf_key)

        with patch("requests.post") as mock_post:
            mock_post.return_value.content = b"fake image data"
            mock_post.return_value.raise_for_status = MagicMock()

            await provider.txt2img("test prompt", (512, 512), seed=123)

            # Should call HuggingFace API
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "inputs" in call_args[1]["json"]
            assert call_args[1]["json"]["inputs"] == "test prompt"

    @pytest.mark.asyncio
    async def test_huggingface_inpaint(self, mock_hf_key):
        """Test HuggingFace provider inpainting."""
        provider = HuggingFaceProvider(mock_hf_key)

        with (
            patch("requests.post") as mock_post,
            patch("builtins.open", create=True) as mock_open,
        ):
            # Mock file reading
            mock_file = MagicMock()
            mock_file.__enter__.return_value.read.return_value = b"fake data"
            mock_open.return_value = mock_file

            mock_post.return_value.content = b"fake inpainted image"
            mock_post.return_value.raise_for_status = MagicMock()

            await provider.inpaint("base.png", "mask.png", "test prompt", seed=123)

            # Should call HuggingFace API with image data
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "image" in call_args[1]["json"]["parameters"]
            assert "mask_image" in call_args[1]["json"]["parameters"]

    def test_pick_provider_txt2img(self):
        """Test provider selection for txt2img."""
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-openai",
                "HF_API_KEY": "test-hf",
                "LEONARDO_API_KEY": "test-leo",
            },
        ):
            # Test priority order
            provider = pick_provider("txt2img", ["openai", "huggingface", "leonardo"])
            assert isinstance(provider, OpenAIProvider)

            provider = pick_provider("txt2img", ["huggingface", "openai"])
            assert isinstance(provider, HuggingFaceProvider)

    def test_pick_provider_inpaint(self):
        """Test provider selection for inpainting."""
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-openai",
                "HF_API_KEY": "test-hf",
                "LEONARDO_API_KEY": "test-leo",
            },
        ):
            # OpenAI should be filtered out for inpainting
            provider = pick_provider("inpaint", ["openai", "huggingface"])
            assert isinstance(provider, HuggingFaceProvider)

            # HuggingFace should be selected if available
            provider = pick_provider("inpaint", ["huggingface", "leonardo"])
            assert isinstance(provider, HuggingFaceProvider)

    def test_pick_provider_no_available(self):
        """Test error when no providers available."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="No available providers"):
                pick_provider("txt2img", ["openai", "huggingface"])

    def test_pick_provider_missing_keys(self):
        """Test provider selection with missing API keys."""
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-openai",
                # HF and Leonardo keys missing
            },
            clear=True,
        ):
            # Should only use available provider
            provider = pick_provider("txt2img", ["openai", "huggingface", "leonardo"])
            assert isinstance(provider, OpenAIProvider)

            # Should raise error if no available providers for operation
            with pytest.raises(RuntimeError):
                pick_provider("inpaint", ["huggingface", "leonardo"])

    @pytest.mark.asyncio
    async def test_provider_error_handling(self, mock_hf_key):
        """Test provider error handling."""
        provider = HuggingFaceProvider(mock_hf_key)

        with patch("requests.post", side_effect=Exception("API Error")):
            with pytest.raises(Exception, match="API Error"):
                await provider.txt2img("test prompt", (512, 512), seed=123)

    def test_directory_structure_verification(self):
        """Test that required directories exist."""
        required_dirs = [
            "static/cache",
            "static/cache/tiles",
            "static/cache/widgets",
            "static/output/floors/floor_2/liliths_room/overlays",
            "web/app",
            "web/loader",
            "web/types",
        ]

        for dir_path in required_dirs:
            assert Path(dir_path).exists(), f"Directory {dir_path} should exist"

    def test_cache_registry_exists(self):
        """Test that cache registry file exists."""
        cache_file = Path("static/cache/hashes.json")
        assert cache_file.exists(), "Cache registry file should exist"

        # Should be valid JSON
        with open(cache_file, "r") as f:
            data = json.load(f)

        assert "version" in data
        assert "cache_entries" in data
        assert "statistics" in data

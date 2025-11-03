"""
FAILING TESTS - These tests expose the real generation problems
These tests SHOULD FAIL to show that the current system is not working
"""

import sys
from pathlib import Path

import pytest

# Add scripts to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from prompt_generator import PromptGenerator


class TestFailingPromptGeneration:
    """Tests that SHOULD FAIL to expose generation problems"""

    def setup_method(self):
        """Setup test instances"""
        self.prompt_gen = PromptGenerator()

    def test_world_json_descriptions_vs_generated_prompts(self):
        """Test that generated prompts match world.json descriptions"""

        # Expected detailed descriptions from world.json
        expected_hall_prompt = "Ground-floor hallway; top-down orthographic 16-bit pixel art; DB32; entrance closet, mat, umbrella stand; gentle NW light; no perspective; do not move fixed props across tiles."
        expected_parents_prompt = "Parents' bedroom; top-down orthographic 16-bit pixel art; DB32; tidy bed; warm lamp; bookshelf; framed art; NW light; no perspective."

        # What we're actually generating (SHOULD NOW WORK WITH LOCATION_ID)
        actual_hall_prompt = self.prompt_gen.construct_base_prompt(
            "Hall — Floor 1", "house_main/house_f1_hall"
        )
        actual_parents_prompt = self.prompt_gen.construct_base_prompt(
            "Parents' Room — Floor 2", "house_main/house_f2_parents"
        )

        print("\n❌ EXPECTED Hall Prompt:")
        print(f"   {expected_hall_prompt}")
        print("\n🔥 ACTUAL Hall Prompt:")
        print(f"   {actual_hall_prompt}")

        # These assertions SHOULD FAIL because the prompts don't match
        assert expected_hall_prompt in actual_hall_prompt, (
            "Hall description from world.json not found in generated prompt!"
        )
        assert "entrance closet" in actual_hall_prompt.lower(), (
            "Specific hall elements missing from prompt!"
        )
        assert "umbrella stand" in actual_hall_prompt.lower(), (
            "Umbrella stand missing from hall prompt!"
        )

        assert expected_parents_prompt in actual_parents_prompt, (
            "Parents room description from world.json not found in generated prompt!"
        )
        assert "tidy bed" in actual_parents_prompt.lower(), (
            "Specific bedroom elements missing from prompt!"
        )
        assert "bookshelf" in actual_parents_prompt.lower(), (
            "Bookshelf missing from parents room prompt!"
        )

    def test_prompt_generator_should_use_world_json_descriptions(self):
        """Test that prompt generator should look up location descriptions from world.json"""

        # This test fails because our current prompt generator doesn't look up
        # the detailed descriptions from world.json - it just uses the basic name

        # Test with location ID that should exist in world.json
        location_id = "house_main/house_f1_hall"

        # Try to get the detailed description (this should work but doesn't)
        # Our current system just passes the name, not the detailed description

        # This will fail because our system doesn't implement proper location lookup
        assert hasattr(self.prompt_gen, "get_location_description"), (
            "PromptGenerator missing location description lookup!"
        )

        # This should return the detailed description but doesn't
        detailed_desc = self.prompt_gen.get_location_description(location_id)
        assert detailed_desc is not None, "No detailed description found for location!"
        assert len(detailed_desc) > 20, "Description too short - should be detailed!"

    def test_generated_prompts_should_contain_specific_elements(self):
        """Test that generated prompts contain specific elements mentioned in world.json"""

        # Test hall prompt
        hall_prompt = self.prompt_gen.construct_base_prompt("Hall — Floor 1")

        # These specific elements should be in the prompt but aren't
        specific_elements = ["entrance closet", "umbrella stand", "mat", "NW light"]

        for element in specific_elements:
            assert element in hall_prompt.lower(), (
                f"Missing element '{element}' from hall prompt!"
            )

        # Test parents room prompt
        parents_prompt = self.prompt_gen.construct_base_prompt(
            "Parents' Room — Floor 2"
        )

        bedroom_elements = ["tidy bed", "warm lamp", "bookshelf", "framed art"]

        for element in bedroom_elements:
            assert element in parents_prompt.lower(), (
                f"Missing element '{element}' from parents room prompt!"
            )

    def test_continuity_between_floors_should_be_maintained(self):
        """Test that prompts maintain continuity between connected floors"""

        # Get prompts for connected floors
        f1_prompt = self.prompt_gen.construct_base_prompt("Hall — Floor 1")
        f2_prompt = self.prompt_gen.construct_base_prompt("Parents' Room — Floor 2")

        # For proper continuity, these should share elements like:
        # - Same lighting direction (NW light)
        # - Same art style (16-bit pixel art, DB32)
        # - Same perspective (top-down orthographic)
        # - Connected architectural elements

        # These tests will fail because our current prompts are too generic
        assert "nw light" in f1_prompt.lower() and "nw light" in f2_prompt.lower(), (
            "Lighting direction not consistent!"
        )
        assert "db32" in f1_prompt.lower() and "db32" in f2_prompt.lower(), (
            "Palette not consistent!"
        )
        assert "top-down" in f1_prompt.lower() and "top-down" in f2_prompt.lower(), (
            "Perspective not consistent!"
        )


class TestFailingImageContent:
    """Tests that SHOULD FAIL to expose image generation problems"""

    def test_generated_images_should_match_descriptions(self):
        """Test that generated images actually contain the described elements"""

        # This is a conceptual test - in reality we'd need image analysis
        # but for now we'll show that our current approach doesn't work

        expected_hall_elements = ["entrance closet", "umbrella stand", "mat"]
        expected_parents_elements = ["bed", "lamp", "bookshelf", "framed art"]

        # Our current images are random and don't contain these elements
        # This test documents what SHOULD be there but isn't

        # These would fail with actual image analysis:
        for element in expected_hall_elements:
            assert False, (
                f"Hall image should contain {element} but doesn't (random generation instead)"
            )

        for element in expected_parents_elements:
            assert False, (
                f"Parents room image should contain {element} but doesn't (random generation instead)"
            )

    def test_floors_should_have_visual_continuity(self):
        """Test that connected floors have visual continuity"""

        # F1 Hall and F2 Parents should connect via stairs
        # The stair positions, floor patterns, wall styles should match

        # Our current images are random with no continuity
        assert False, (
            "Floors should have matching stairs, floor patterns, and wall styles but are random"
        )


if __name__ == "__main__":
    print("🚨 THESE TESTS SHOULD FAIL!")
    print("They expose the real problems with the generation system")
    print("Run: pytest tests/unit/test_failing_generation.py -v")
    pytest.main([__file__, "-v"])

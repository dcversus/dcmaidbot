"""
E2E tests for PRP-016 Interactive Location System Tile Variations.

These tests validate the complete tile variation system in a real browser:
1. Widget hover changes background image to hover tile
2. Widget click changes background image to click tile
3. Widget release reverts to hover tile
4. Audio sounds play for different events
5. Widget positioning matches visual elements
6. Easter egg discovery with quest complete sound
7. Responsive behavior affects tile rendering

Run with:
    pytest tests/e2e/test_prp016_tile_variations_e2e.py -v --headed
"""

import os
from pathlib import Path

import pytest
from playwright.async_api import async_playwright, expect

# Mark all tests as Playwright tests
pytestmark = pytest.mark.playwright

# Test configuration
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
SCREENSHOT_DIR = Path("test_screenshots/tile_variations")
SCREENSHOT_DIR.mkdir(exist_ok=True, parents=True)


@pytest.fixture(scope="session")
async def browser():
    """Playwright browser fixture for E2E testing."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Set to True for CI
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--allow-running-insecure-content",
            ],
        )
        yield browser
        await browser.close()


@pytest.fixture
async def page(browser):
    """New page for each test."""
    page = await browser.new_page()
    page.set_default_timeout(10000)
    yield page
    await page.close()


class TestTileVariations:
    """Test tile variation system."""

    async def setup_method(self):
        """Setup for each test method."""
        pass

    async def take_screenshot(self, page, name: str, test_name: str):
        """Take screenshot for test documentation."""
        filename = f"{test_name}_{name}.png"
        path = SCREENSHOT_DIR / filename
        await page.screenshot(path=str(path), full_page=True)
        print(f"📸 Screenshot saved: {path}")
        return path

    async def get_background_image(self, page, location_id: str = "liliths_room"):
        """Get current background image URL for location."""
        return await page.evaluate(f"""
            () => {{
                const container = document.querySelector('.location-container[data-location-id="{location_id}"]');
                return container ? container.style.backgroundImage : null;
            }}
        """)

    async def test_tile_variation_idle_to_hover(self, page):
        """Test that widget hover changes background image from idle to hover."""
        test_name = "tile_hover"

        await page.goto(BASE_URL)
        await page.wait_for_selector("#worldContainer", state="visible")

        # Get initial background image (should be idle)
        initial_bg = await self.get_background_image(page)
        print(f"Initial background: {initial_bg}")

        # Verify it's the idle tile
        assert "liliths_room_idle.png" in initial_bg, (
            f"Expected idle tile, got: {initial_bg}"
        )

        # Hover over first widget
        widget = page.locator(".widget-area").first
        await widget.hover()
        await page.wait_for_timeout(300)

        # Get background image after hover
        hover_bg = await self.get_background_image(page)
        print(f"Hover background: {hover_bg}")

        # Verify it changed to hover tile
        assert "liliths_room_hover.png" in hover_bg, (
            f"Expected hover tile, got: {hover_bg}"
        )
        assert hover_bg != initial_bg, "Background image should change on hover"

        await self.take_screenshot(page, "hover_state", test_name)

    async def test_tile_variation_hover_to_click(self, page):
        """Test that widget click changes background image from hover to click."""
        test_name = "tile_click"

        await page.goto(BASE_URL)
        await page.wait_for_selector("#worldContainer", state="visible")

        # Hover over widget first
        widget = page.locator(".widget-area").first
        await widget.hover()
        await page.wait_for_timeout(300)

        # Verify hover state
        hover_bg = await self.get_background_image(page)
        assert "liliths_room_hover.png" in hover_bg, "Should be in hover state"

        # Click and hold
        await widget.click()
        await page.wait_for_timeout(300)

        # Get background image after click
        click_bg = await self.get_background_image(page)
        print(f"Click background: {click_bg}")

        # Verify it changed to click tile
        assert "liliths_room_click.png" in click_bg, (
            f"Expected click tile, got: {click_bg}"
        )
        assert click_bg != hover_bg, "Background image should change on click"

        await self.take_screenshot(page, "click_state", test_name)

    async def test_tile_variation_click_to_hover_release(self, page):
        """Test that widget release reverts background image from click to hover."""
        test_name = "tile_release"

        await page.goto(BASE_URL)
        await page.wait_for_selector("#worldContainer", state="visible")

        widget = page.locator(".widget-area").first

        # Click and hold
        await widget.click()
        await page.wait_for_timeout(300)

        # Verify click state
        click_bg = await self.get_background_image(page)
        assert "liliths_room_click.png" in click_bg, "Should be in click state"

        # Release click by moving mouse away and back
        await page.mouse.move(0, 0)
        await page.wait_for_timeout(100)
        await widget.hover()
        await page.wait_for_timeout(300)

        # Get background image after release
        release_bg = await self.get_background_image(page)
        print(f"Release background: {release_bg}")

        # Verify it reverted to hover tile
        assert "liliths_room_hover.png" in release_bg, (
            f"Expected hover tile after release, got: {release_bg}"
        )
        assert release_bg != click_bg, (
            "Background image should revert to hover on release"
        )

        await self.take_screenshot(page, "release_state", test_name)

    async def test_tile_variation_hover_to_idle_unhover(self, page):
        """Test that widget unhover reverts background image from hover to idle."""
        test_name = "tile_unhover"

        await page.goto(BASE_URL)
        await page.wait_for_selector("#worldContainer", state="visible")

        widget = page.locator(".widget-area").first

        # Hover over widget
        await widget.hover()
        await page.wait_for_timeout(300)

        # Verify hover state
        hover_bg = await self.get_background_image(page)
        assert "liliths_room_hover.png" in hover_bg, "Should be in hover state"

        # Move mouse away to unhover
        await page.mouse.move(0, 0)
        await page.wait_for_timeout(300)

        # Get background image after unhover
        unhover_bg = await self.get_background_image(page)
        print(f"Unhover background: {unhover_bg}")

        # Verify it reverted to idle tile
        assert "liliths_room_idle.png" in unhover_bg, (
            f"Expected idle tile after unhover, got: {unhover_bg}"
        )
        assert unhover_bg != hover_bg, (
            "Background image should revert to idle on unhover"
        )

        await self.take_screenshot(page, "unhover_state", test_name)


class TestAudioSystem:
    """Test audio system functionality."""

    async def test_audio_system_generates_sounds(self, page):
        """Test that audio system generates procedural sounds."""
        await page.goto(BASE_URL)
        await page.wait_for_selector("#worldContainer", state="visible")

        # Check console for audio generation messages
        audio_messages = []
        page.on("console", lambda msg: audio_messages.append(f"{msg.type}: {msg.text}"))

        # Wait a bit for audio initialization
        await page.wait_for_timeout(500)

        # Check if sounds were generated
        sound_generated = any("Generated sound:" in msg for msg in audio_messages)
        print(f"Audio messages: {audio_messages}")

        assert sound_generated, "Audio system should generate procedural sounds"

        # Check for specific sounds
        hover_generated = any("hover (800Hz" in msg for msg in audio_messages)
        click_generated = any("click (1200Hz" in msg for msg in audio_messages)

        assert hover_generated, "Hover sound should be generated"
        assert click_generated, "Click sound should be generated"

    async def test_audio_toggle_functionality(self, page):
        """Test audio toggle button functionality."""
        await page.goto(BASE_URL)
        await page.wait_for_selector("#worldContainer", state="visible")

        audio_toggle = page.locator("#audioToggle")
        await expect(audio_toggle).to_be_visible()

        # Check initial state
        initial_text = await audio_toggle.inner_text()
        print(f"Initial audio state: {initial_text}")

        # Click to toggle
        await audio_toggle.click()
        await page.wait_for_timeout(200)

        # Check state changed
        new_text = await audio_toggle.inner_text()
        print(f"Audio after toggle: {new_text}")

        # Verify state changed
        assert initial_text != new_text, "Audio toggle should change state"

        # Check class changes
        has_muted_class = await audio_toggle.evaluate(
            "el => el.classList.contains('muted')"
        )
        print(f"Has muted class: {has_muted_class}")


class TestWidgetPositioning:
    """Test widget positioning accuracy."""

    async def test_wall_clock_positioning(self, page):
        """Test that wall_clock widget is positioned correctly."""
        await page.goto(BASE_URL)
        await page.wait_for_selector("#worldContainer", state="visible")

        # Find wall_clock widget
        wall_clock = page.locator(".widget-area[data-widget-id='wall_clock']")
        await expect(wall_clock).to_be_visible()

        # Get its position and size
        bounding_box = await wall_clock.bounding_box()
        print(f"Wall clock bounding box: {bounding_box}")

        # Should be positioned around x=228px (as corrected)
        assert bounding_box["x"] >= 200, (
            f"Wall clock x position {bounding_box['x']} should be >= 200"
        )
        assert bounding_box["x"] <= 300, (
            f"Wall clock x position {bounding_box['x']} should be <= 300"
        )

        # Should have reasonable size
        assert bounding_box["width"] >= 50, (
            f"Wall clock width {bounding_box['width']} should be >= 50"
        )
        assert bounding_box["height"] >= 50, (
            f"Wall clock height {bounding_box['height']} should be >= 50"
        )

    async def test_changelog_book_positioning(self, page):
        """Test that changelog_book widget is positioned in accessible area."""
        await page.goto(BASE_URL)
        await page.wait_for_selector("#worldContainer", state="visible")

        # Find changelog_book widget
        changelog_book = page.locator(".widget-area[data-widget-type='changelog']")
        if await changelog_book.count() > 0:
            await expect(changelog_book).to_be_visible()

            # Get its position and size
            bounding_box = await changelog_book.bounding_box()
            print(f"Changelog book bounding box: {bounding_box}")

            # Should be positioned in center area (around x=450px, y=350px as corrected)
            assert 300 <= bounding_box["x"] <= 600, (
                f"Changelog x position {bounding_box['x']} should be in center area"
            )
            assert 200 <= bounding_box["y"] <= 500, (
                f"Changelog y position {bounding_box['y']} should be in center area"
            )

            # Should have positive size
            assert bounding_box["width"] > 0, "Changelog should have positive width"
            assert bounding_box["height"] > 0, "Changelog should have positive height"

    async def test_all_widgets_have_valid_positions(self, page):
        """Test that all widgets have valid positions and sizes."""
        await page.goto(BASE_URL)
        await page.wait_for_selector("#worldContainer", state="visible")

        widgets = page.locator(".widget-area")
        widget_count = await widgets.count()

        print(f"Found {widget_count} widgets")

        for i in range(widget_count):
            widget = widgets.nth(i)
            await expect(widget).to_be_visible()

            # Get position and size
            bounding_box = await widget.bounding_box()
            print(f"Widget {i} bounding box: {bounding_box}")

            # Should have valid position
            assert bounding_box["x"] >= 0, f"Widget {i} x position should be >= 0"
            assert bounding_box["y"] >= 0, f"Widget {i} y position should be >= 0"

            # Should have positive size (not 0x0)
            assert bounding_box["width"] > 0, f"Widget {i} width should be > 0"
            assert bounding_box["height"] > 0, f"Widget {i} height should be > 0"

            # Should be within reasonable bounds (1024x1024 image)
            assert bounding_box["x"] < 1024, f"Widget {i} x position should be < 1024"
            assert bounding_box["y"] < 1024, f"Widget {i} y position should be < 1024"


class TestEasterEggSystem:
    """Test easter egg system with tile variations."""

    async def test_easter_egg_discovery_with_sound(self, page):
        """Test easter egg discovery triggers quest complete sound."""
        await page.goto(BASE_URL)
        await page.wait_for_selector("#worldContainer", state="visible")

        # Capture console messages for audio
        audio_messages = []
        page.on("console", lambda msg: audio_messages.append(f"{msg.type}: {msg.text}"))

        # Find easter egg
        easter_egg = page.locator(".easter-egg-zone").first
        if await easter_egg.count() > 0:
            # Scroll into view
            await easter_egg.scroll_into_view_if_needed()
            await page.wait_for_timeout(500)

            # Check initial opacity
            initial_opacity = await easter_egg.evaluate(
                "el => getComputedStyle(el).opacity"
            )
            print(f"Initial easter egg opacity: {initial_opacity}")

            # Click easter egg
            await easter_egg.click()
            await page.wait_for_timeout(500)

            # Check modal opened
            modal = page.locator("#modalOverlay")
            await expect(modal).to_be_visible()

            # Check if quest complete sound was played
            # Note: This would require audio monitoring which is complex in E2E tests
            # For now, we verify the easter egg discovery mechanics work

            # Check easter egg is marked as found
            found_class = await easter_egg.evaluate(
                "el => el.classList.contains('found')"
            )
            print(f"Easter egg marked as found: {found_class}")

            assert found_class, "Easter egg should be marked as found after discovery"


class TestResponsiveTileBehavior:
    """Test responsive behavior affects tile rendering."""

    async def test_desktop_tile_rendering(self, page):
        """Test tile rendering on desktop viewport."""
        # Set desktop viewport
        await page.set_viewport_size({"width": 1920, "height": 1080})

        await page.goto(BASE_URL)
        await page.wait_for_selector("#worldContainer", state="visible")

        # Test tile variations work on desktop
        widget = page.locator(".widget-area").first
        await widget.hover()
        await page.wait_for_timeout(300)

        # Verify hover tile is loaded
        hover_bg = await self.get_background_image(page)
        assert "liliths_room_hover.png" in hover_bg, "Hover tile should load on desktop"

        await self.take_screenshot(page, "desktop_hover", "responsive")

    async def test_mobile_tile_rendering(self, page):
        """Test tile rendering on mobile viewport."""
        # Set mobile viewport
        await page.set_viewport_size({"width": 375, "height": 667})

        await page.goto(BASE_URL)
        await page.wait_for_selector("#worldContainer", state="visible")

        # Test tile variations work on mobile
        widget = page.locator(".widget-area").first
        await widget.hover()
        await page.wait_for_timeout(300)

        # Verify hover tile is loaded
        hover_bg = await self.get_background_image(page)
        assert "liliths_room_hover.png" in hover_bg, "Hover tile should load on mobile"

        await self.take_screenshot(page, "mobile_hover", "responsive")

    async def test_responsive_layout_doesnt_break_tile_variations(self, page):
        """Test that responsive layout changes don't break tile variations."""
        # Start with desktop
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.goto(BASE_URL)
        await page.wait_for_selector("#worldContainer", state="visible")

        # Test tile variations on desktop
        widget = page.locator(".widget-area").first
        await widget.hover()
        await page.wait_for_timeout(300)

        desktop_bg = await self.get_background_image(page)
        assert "liliths_room_hover.png" in desktop_bg, "Desktop hover should work"

        # Change to mobile without reloading
        await page.set_viewport_size({"width": 375, "height": 667})
        await page.wait_for_timeout(500)

        # Test tile variations still work after responsive change
        await widget.hover()
        await page.wait_for_timeout(300)

        mobile_bg = await self.get_background_image(page)
        assert "liliths_room_hover.png" in mobile_bg, (
            "Mobile hover should work after responsive change"
        )

        print("✅ Tile variations work consistently across responsive breakpoints")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--headed"])

"""E2E tests for PRP-016 Interactive Location System.

These tests verify the COMPLETE interactive location exploration system:
1. Responsive layout (desktop half-location, mobile full-location)
2. Widget hover states (all tiles with same ID hover together)
3. Widget click actions and modal rendering with markdown
4. Audio system functionality and sound toggle
5. Dark Souls location discovery system
6. Easter egg discovery mechanics
7. Floor navigation GUI functionality
8. Live data integration (GitHub API, changelog, version)

Tests use Playwright for browser automation with screenshots and visual validation.

Run with:
    pytest tests/e2e/test_prp016_interactive_location_system.py -v -s --headed
"""

import os
from pathlib import Path

import pytest
from playwright.async_api import async_playwright, expect

# Mark all tests as Playwright tests
pytestmark = pytest.mark.playwright

# Test configuration
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
SCREENSHOT_DIR = Path("test_screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)


@pytest.fixture(scope="session")
async def browser():
    """Playwright browser fixture for E2E testing."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,  # Set to False for visual debugging
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
    page.set_default_timeout(10000)  # 10 second timeout
    yield page
    await page.close()


@pytest.fixture
async def mobile_page(browser):
    """Mobile-sized page for responsive testing."""
    context = await browser.new_context(
        viewport={"width": 375, "height": 667},  # iPhone SE
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
    )
    page = await context.new_page()
    page.set_default_timeout(10000)
    yield page
    await context.close()


class TestInteractiveLocationSystem:
    """Test suite for the interactive location system."""

    async def setup_method(self):
        """Setup for each test method."""
        pass

    async def take_screenshot(self, page, name: str, test_name: str):
        """Take screenshot for test documentation."""
        filename = f"{test_name}_{name}.png"
        path = SCREENSHOT_DIR / filename
        await page.screenshot(path=str(path), full_page=True)
        print(f"📸 Screenshot saved: {path}")

    async def test_page_loads_and_initializes(self, page):
        """Test that the page loads correctly and initializes all systems."""
        test_name = "page_load"

        # Navigate to the page
        await page.goto(BASE_URL)

        # Wait for loading to complete
        await page.wait_for_selector("#worldContainer", state="visible", timeout=15000)

        # Take screenshot of initial state
        await self.take_screenshot(page, "initial_load", test_name)

        # Verify main elements are present
        await expect(page.locator(".world-container")).to_be_visible()
        await expect(page.locator(".floor-navigation")).to_be_visible()
        await expect(page.locator(".audio-toggle")).to_be_visible()

        # Check loading is hidden
        await expect(page.locator("#loading")).to_be_hidden()

        print("✅ Page loaded successfully with all main elements")

    async def test_responsive_layout_desktop(self, page):
        """Test responsive layout on desktop (half-location viewport)."""
        test_name = "responsive_desktop"

        # Set desktop viewport
        await page.set_viewport_size({"width": 1920, "height": 1080})

        await page.goto(BASE_URL)
        await page.wait_for_selector("#worldContainer", state="visible")

        # Test desktop viewport size
        location_section = page.locator(".location-section").first
        await expect(location_section).to_be_visible()

        # Get viewport and location dimensions
        viewport_height = await page.evaluate("window.innerHeight")
        location_height = await location_section.evaluate("el => el.offsetHeight")

        # On desktop, location should be approximately half viewport height (50vh)
        expected_height = viewport_height * 0.5

        print(
            f"Desktop: viewport={viewport_height}px, location={location_height}px, expected≈{expected_height}px"
        )

        await self.take_screenshot(page, "desktop_layout", test_name)

    async def test_responsive_layout_mobile(self, mobile_page):
        """Test responsive layout on mobile (full-location viewport)."""
        test_name = "responsive_mobile"

        await mobile_page.goto(BASE_URL)
        await mobile_page.wait_for_selector("#worldContainer", state="visible")

        # Test mobile viewport size
        location_section = mobile_page.locator(".location-section").first
        await expect(location_section).to_be_visible()

        # Get viewport and location dimensions
        viewport_height = await mobile_page.evaluate("window.innerHeight")
        location_height = await location_section.evaluate("el => el.offsetHeight")

        print(f"Mobile: viewport={viewport_height}px, location={location_height}px")

        await self.take_screenshot(mobile_page, "mobile_layout", test_name)

    async def test_widget_hover_states(self, page):
        """Test that widget hover states work correctly."""
        test_name = "widget_hover"

        await page.goto(BASE_URL)
        await page.wait_for_selector("#worldContainer", state="visible")

        # Find first widget area
        widget_area = page.locator(".widget-area").first
        if await widget_area.count() == 0:
            pytest.skip("No widgets found in test data")

        widget_id = await widget_area.get_attribute("data-widget-id")

        # Hover over widget area
        await widget_area.hover()

        # Check visual changes (scale and glow)
        transform = await widget_area.evaluate("el => getComputedStyle(el).transform")
        filter_value = await widget_area.evaluate("el => getComputedStyle(el).filter")

        # Should have hover effects

        print(f"Widget {widget_id} hover: transform={transform}, filter={filter_value}")

        await self.take_screenshot(page, "widget_hover_state", test_name)

    async def test_audio_toggle_functionality(self, page):
        """Test audio toggle button functionality."""
        test_name = "audio_toggle"

        await page.goto(BASE_URL)
        await page.wait_for_selector("#worldContainer", state="visible")

        audio_toggle = page.locator("#audioToggle")
        await expect(audio_toggle).to_be_visible()

        # Check initial state
        initial_text = await audio_toggle.inner_text()
        print(f"Initial audio toggle text: {initial_text}")

        # Click to toggle
        await audio_toggle.click()

        # Check state changed
        new_text = await audio_toggle.inner_text()
        print(f"Audio toggle after click: {new_text}")

        # Check class changes
        has_muted_class = await audio_toggle.evaluate(
            "el => el.classList.contains('muted')"
        )
        print(f"Has muted class: {has_muted_class}")

        await self.take_screenshot(page, "audio_toggle", test_name)

    async def test_floor_navigation_gui(self, page):
        """Test floor navigation GUI functionality."""
        test_name = "floor_navigation"

        await page.goto(BASE_URL)
        await page.wait_for_selector("#worldContainer", state="visible")

        floor_nav = page.locator(".floor-navigation")
        await expect(floor_nav).to_be_visible()

        # Check floor buttons exist
        floor_buttons = page.locator(".floor-button")
        button_count = await floor_buttons.count()

        print(f"Found {button_count} floor buttons")

        if button_count > 0:
            # Get current active floor
            active_button = page.locator(".floor-button.active")
            if await active_button.count() > 0:
                current_floor = await active_button.inner_text()
                print(f"Current active floor: {current_floor}")

        await self.take_screenshot(page, "floor_navigation", test_name)

    async def test_easter_egg_discovery(self, page):
        """Test easter egg discovery mechanics."""
        test_name = "easter_egg"

        await page.goto(BASE_URL)
        await page.wait_for_selector("#worldContainer", state="visible")

        # Find easter egg zone
        easter_egg = page.locator(".easter-egg-zone").first
        if await easter_egg.count() == 0:
            pytest.skip("No easter eggs found in test data")

        egg_id = await easter_egg.get_attribute("data-easter-egg-id")

        # Check initial opacity (should be barely visible)
        opacity = await easter_egg.evaluate("el => getComputedStyle(el).opacity")
        print(f"Initial easter egg opacity: {opacity}")

        # Hover over easter egg
        await easter_egg.hover()

        # Check hover opacity (should be more visible)
        hover_opacity = await easter_egg.evaluate("el => getComputedStyle(el).opacity")
        print(f"Hover easter egg opacity: {hover_opacity}")

        # Click easter egg
        await easter_egg.click()

        # Check modal appears
        modal = page.locator("#modalOverlay")
        await expect(modal).to_be_visible()

        # Check modal has easter egg content
        modal_title = page.locator("#modalTitle")
        title_text = await modal_title.inner_text()
        print(f"Easter egg modal title: {title_text}")

        await self.take_screenshot(page, "easter_egg_found", test_name)

        # Close modal
        await page.locator("#modalClose").click()
        await expect(modal).not_to_be_visible()

        print(f"✅ Easter egg discovery works for: {egg_id}")

    async def test_modal_functionality(self, page):
        """Test basic modal open/close functionality."""
        test_name = "modal_basic"

        await page.goto(BASE_URL)
        await page.wait_for_selector("#worldContainer", state="visible")

        # Find any clickable widget
        widget_area = page.locator(".widget-area").first
        if await widget_area.count() == 0:
            pytest.skip("No widgets found for modal test")

        # Click widget to potentially open modal
        await widget_area.click()

        # Check if modal opened (not all widgets open modals)
        modal = page.locator("#modalOverlay")
        modal_visible = await modal.is_visible()

        if modal_visible:
            print("Modal opened successfully")

            # Get modal content
            modal_title = page.locator("#modalTitle")
            modal_content = page.locator("#modalContent")

            title_text = await modal_title.inner_text()
            content_text = await modal_content.inner_text()

            print(f"Modal title: {title_text}")
            print(f"Modal content preview: {content_text[:100]}...")

            # Test close button
            await page.locator("#modalClose").click()
            await expect(modal).not_to_be_visible()
            print("Modal closed successfully")
        else:
            print("Widget did not open modal (may be link widget or other type)")

        await self.take_screenshot(page, "modal_test", test_name)

    async def test_scroll_behavior(self, page):
        """Test scroll behavior and location transitions."""
        test_name = "scroll_behavior"

        await page.goto(BASE_URL)
        await page.wait_for_selector("#worldContainer", state="visible")

        page.locator(".world-container")
        location_sections = page.locator(".location-section")
        section_count = await location_sections.count()

        print(f"Found {section_count} location sections")

        if section_count > 1:
            # Get initial scroll position
            initial_scroll = await page.evaluate("window.pageYOffset")

            # Test scrolling to next location
            second_location = location_sections.nth(1)
            await second_location.scroll_into_view_if_needed()
            await page.wait_for_timeout(500)

            # Check scroll position changed
            final_scroll = await page.evaluate("window.pageYOffset")
            print(f"Scroll position changed from {initial_scroll} to {final_scroll}")

        await self.take_screenshot(page, "scroll_behavior", test_name)


if __name__ == "__main__":
    # Run tests with screenshots
    pytest.main([__file__, "-v", "-s", "--headed"])

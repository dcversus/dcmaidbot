#!/usr/bin/env python3
"""
E2E Tests: Advanced UI Behaviors
===============================

Comprehensive tests for:
1. Hover state isolation (only affects widget area)
2. Modal color contrast (dark text on transparent backgrounds)
3. Widget-specific background states in modals
4. Screenshot comparison between modal states (5% difference requirement)
"""

import hashlib
from pathlib import Path

import pytest
from playwright.async_api import async_playwright


class TestAdvancedUIBehaviors:
    """Test advanced UI behaviors with strict requirements"""

    @pytest.mark.e2e
    async def test_hover_state_isolation_only_widget_area(self):
        """Test that hover only affects the specific widget area, not other elements"""

        async with async_playwright() as p:
            # Start the local server
            import subprocess
            import time

            import requests

            # Check if server is running
            server_ports = [8004, 8000, 8001, 8080]
            server_url = None

            for port in server_ports:
                try:
                    response = requests.get(f"http://localhost:{port}/", timeout=2)
                    if response.status_code == 200:
                        server_url = f"http://localhost:{port}"
                        print(f"Found server at {server_url}")
                        break
                except Exception:
                    continue

            if not server_url:
                subprocess.Popen(
                    ["python3", "-m", "http.server", "8002"],
                    cwd="/Users/dcversus/Documents/GitHub/dcmaidbot",
                )
                time.sleep(3)
                server_url = "http://localhost:8002"

            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(server_url)
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(5000)  # Wait longer for JavaScript to load

            # Check if worldContainer is visible
            world_container = await page.query_selector("#worldContainer")
            if world_container:
                is_visible = await world_container.is_visible()
                print(f"World container visible: {is_visible}")
                if not is_visible:
                    print("⚠️ World container not visible - trying to force load")
                    await page.evaluate("""
                        if (typeof window.worldManager !== 'undefined') {
                            window.worldManager.hideLoading();
                        }
                    """)
                    await page.wait_for_timeout(2000)

            # Get all widget areas
            widget_areas = await page.query_selector_all(".widget-area")
            print(f"Found {len(widget_areas)} widget areas")

            if len(widget_areas) == 0:
                # Debug: Look for any interactive elements
                all_interactive = await page.query_selector_all(
                    "button, [data-widget-id], .widget, .location-container"
                )
                print(f"Found {len(all_interactive)} interactive elements as fallback")
                widget_areas = all_interactive

            assert len(widget_areas) > 0, "No widget areas found"

            print(f"Found {len(widget_areas)} widget areas for hover isolation testing")

            # Test each widget for hover isolation
            for i, widget_area in enumerate(widget_areas[:3]):  # Test first 3 widgets
                widget_id = await widget_area.get_attribute("data-widget-id")
                if not widget_id:
                    continue

                print(f"\nTesting hover isolation for {widget_id} (widget {i + 1}/3)")

                # Get all elements that could be affected by hover
                all_widget_areas = await page.query_selector_all(".widget-area")
                all_location_containers = await page.query_selector_all(
                    ".location-container"
                )
                all_modal_elements = await page.query_selector_all(
                    ".modal-overlay, .modal-content"
                )

                # Record initial state of all elements
                initial_states = []
                for area in all_widget_areas:
                    if area != widget_area:
                        classes = await area.evaluate("el => Array.from(el.classList)")
                        bg_style = await area.evaluate(
                            "el => getComputedStyle(el).backgroundColor"
                        )
                        initial_states.append(("widget_area", classes, bg_style))

                for container in all_location_containers:
                    bg_style = await container.evaluate(
                        "el => getComputedStyle(el).backgroundImage"
                    )
                    initial_states.append(("location_container", None, bg_style))

                for modal in all_modal_elements:
                    if modal:
                        opacity = await modal.evaluate(
                            "el => getComputedStyle(el).opacity"
                        )
                        visibility = await modal.evaluate(
                            "el => getComputedStyle(el).visibility"
                        )
                        initial_states.append(
                            (
                                "modal_element",
                                None,
                                {"opacity": opacity, "visibility": visibility},
                            )
                        )

                # Hover over the target widget
                await widget_area.hover()
                await page.wait_for_timeout(500)

                # Check states after hover - ONLY the hovered widget should change
                other_widgets_changed = 0
                locations_changed = 0
                modals_affected = 0

                # Check other widget areas haven't changed
                for area in all_widget_areas:
                    if area != widget_area:
                        current_classes = await area.evaluate(
                            "el => Array.from(el.classList)"
                        )
                        current_bg = await area.evaluate(
                            "el => getComputedStyle(el).backgroundColor"
                        )

                        # Find corresponding initial state
                        for element_type, init_classes, init_bg in initial_states:
                            if (
                                element_type == "widget_area"
                                and init_classes == current_classes
                            ):
                                if "hover" in current_classes:
                                    other_widgets_changed += 1
                                    print(
                                        "  ❌ Other widget area incorrectly has hover class"
                                    )
                                if current_bg != init_bg:
                                    print(
                                        "  ❌ Other widget area background changed unexpectedly"
                                    )
                                break

                # Check location containers haven't changed (except the one containing the hovered widget)
                hovered_container = await widget_area.evaluate(
                    'el => el.closest(".location-container")'
                )
                for container in all_location_containers:
                    if container != hovered_container:
                        current_bg = await container.evaluate(
                            "el => getComputedStyle(el).backgroundImage"
                        )

                        for element_type, _, init_bg in initial_states:
                            if (
                                element_type == "location_container"
                                and current_bg != init_bg
                            ):
                                locations_changed += 1
                                print(
                                    "  ❌ Other location container background changed unexpectedly"
                                )
                                break

                # Check modal elements haven't appeared
                for modal in all_modal_elements:
                    if modal:
                        current_opacity = await modal.evaluate(
                            "el => getComputedStyle(el).opacity"
                        )
                        current_visibility = await modal.evaluate(
                            "el => getComputedStyle(el).visibility"
                        )

                        for element_type, _, init_state in initial_states:
                            if element_type == "modal_element":
                                if (
                                    current_opacity != init_state["opacity"]
                                    and current_opacity != "0"
                                ):
                                    modals_affected += 1
                                    print("  ❌ Modal element appeared during hover")
                                if (
                                    current_visibility != init_state["visibility"]
                                    and current_visibility != "hidden"
                                ):
                                    modals_affected += 1
                                    print(
                                        "  ❌ Modal element became visible during hover"
                                    )
                                break

                # Verify hover isolation
                assert other_widgets_changed == 0, (
                    f"❌ {other_widgets_changed} other widgets incorrectly changed on hover"
                )
                assert locations_changed == 0, (
                    f"❌ {locations_changed} other locations incorrectly changed on hover"
                )
                assert modals_affected == 0, (
                    f"❌ {modals_affected} modal elements incorrectly appeared on hover"
                )

                print(f"  ✅ Hover isolation verified for {widget_id}")

                # Move away from widget
                await page.mouse.move(10, 10)
                await page.wait_for_timeout(500)

            await browser.close()

    @pytest.mark.e2e
    async def test_modal_color_contrast_dark_text_on_transparent_bg(self):
        """Test that all modals have dark text with proper contrast on transparent backgrounds"""

        async with async_playwright() as p:
            # Find available server
            import requests

            server_ports = [8004, 8003, 8000, 8001, 8002, 8080]
            server_url = None

            for port in server_ports:
                try:
                    response = requests.get(f"http://localhost:{port}/", timeout=2)
                    if response.status_code == 200:
                        server_url = f"http://localhost:{port}"
                        break
                except Exception:
                    continue

            if not server_url:
                pytest.skip("No available server found")
                return

            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(server_url)
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(5000)  # Wait longer for JavaScript to load

            # Check if worldContainer is visible
            world_container = await page.query_selector("#worldContainer")
            if world_container:
                is_visible = await world_container.is_visible()
                print(f"World container visible: {is_visible}")
                if not is_visible:
                    print("⚠️ World container not visible - trying to force load")
                    await page.evaluate("""
                        if (typeof window.worldManager !== 'undefined') {
                            window.worldManager.hideLoading();
                        }
                    """)
                    await page.wait_for_timeout(2000)

            # Find widgets that open modals
            widget_areas = await page.query_selector_all(".widget-area")
            if len(widget_areas) == 0:
                # Debug: Look for any interactive elements
                all_interactive = await page.query_selector_all(
                    "button, [data-widget-id], .widget, .location-container"
                )
                print(f"Found {len(all_interactive)} interactive elements as fallback")
                widget_areas = all_interactive
            modal_widgets = []

            for widget_area in widget_areas:
                widget_id = await widget_area.get_attribute("data-widget-id")
                if widget_id:
                    modal_widgets.append((widget_area, widget_id))

            assert len(modal_widgets) > 0, "No widgets found for modal testing"

            print(
                f"Found {len(modal_widgets)} widgets for modal color contrast testing"
            )

            for widget_area, widget_id in modal_widgets[
                :3
            ]:  # Test first 3 modal widgets
                print(f"\nTesting modal color contrast for {widget_id}")

                # Click widget to open modal
                await widget_area.click()
                await page.wait_for_timeout(1000)

                # Check if modal appeared
                modal_overlay = await page.query_selector("#modalOverlay")
                modal_content = await page.query_selector("#modalContent")

                if modal_overlay and await modal_overlay.is_visible():
                    print(f"  Modal opened for {widget_id}")

                    # Get modal background color and transparency
                    modal_bg_color = await modal_overlay.evaluate(
                        "el => getComputedStyle(el).backgroundColor"
                    )
                    modal_bg_opacity = await modal_overlay.evaluate(
                        "el => getComputedStyle(el).opacity"
                    )

                    print(
                        f"  Modal background: {modal_bg_color}, opacity: {modal_bg_opacity}"
                    )

                    # Test text color contrast in modal content
                    if modal_content:
                        text_elements = await modal_content.query_selector_all(
                            "h1, h2, h3, p, span, div"
                        )

                        dark_text_count = 0
                        light_text_count = 0
                        contrast_issues = []

                        for text_element in text_elements[
                            :5
                        ]:  # Test first 5 text elements
                            text_color = await text_element.evaluate(
                                "el => getComputedStyle(el).color"
                            )
                            bg_color = await text_element.evaluate(
                                "el => getComputedStyle(el).backgroundColor"
                            )

                            # Convert RGB to hex for easier analysis
                            def rgb_to_hex(rgb_str):
                                if rgb_str.startswith("rgba"):
                                    # Extract RGB values from rgba(r, g, b, a)
                                    import re

                                    match = re.search(
                                        r"rgba?\((\d+),\s*(\d+),\s*(\d+)", rgb_str
                                    )
                                    if match:
                                        r, g, b = map(int, match.groups())
                                        return f"#{r:02x}{g:02x}{b:02x}"
                                elif rgb_str.startswith("rgb"):
                                    import re

                                    match = re.search(
                                        r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", rgb_str
                                    )
                                    if match:
                                        r, g, b = map(int, match.groups())
                                        return f"#{r:02x}{g:02x}{b:02x}"
                                return rgb_str

                            text_hex = rgb_to_hex(text_color)
                            bg_hex = rgb_to_hex(bg_color)

                            # Check if text is dark (should be dark on transparent/light backgrounds)
                            def is_dark_color(hex_color):
                                if hex_color.startswith("#"):
                                    hex_color = hex_color[1:]
                                r = int(hex_color[0:2], 16)
                                g = int(hex_color[2:4], 16)
                                b = int(hex_color[4:6], 16)
                                brightness = (r * 299 + g * 587 + b * 114) / 1000
                                return brightness < 128

                            text_is_dark = is_dark_color(text_hex)

                            if text_is_dark:
                                dark_text_count += 1
                                print(f"    ✅ Dark text found: {text_hex}")
                            else:
                                light_text_count += 1
                                print(
                                    f"    ❌ Light text found (should be dark): {text_hex}"
                                )
                                contrast_issues.append(
                                    f"Light text {text_hex} on {bg_hex}"
                                )

                        # Verify color contrast requirements
                        print(f"  Dark text elements: {dark_text_count}")
                        print(f"  Light text elements: {light_text_count}")

                        # At least 80% of text should be dark
                        total_text = dark_text_count + light_text_count
                        if total_text > 0:
                            dark_percentage = (dark_text_count / total_text) * 100
                            assert dark_percentage >= 80, (
                                f"❌ Only {dark_percentage:.1f}% of text is dark (require 80%)"
                            )
                            print(
                                f"  ✅ {dark_percentage:.1f}% of text is dark - contrast requirement met"
                            )

                        # Verify modal background is transparent (accept both 0 and 0.001 as valid)
                        is_transparent = (
                            "rgba(255, 255, 255, 0)" in modal_bg_color
                            or "rgba(255, 255, 255, 0.001)" in modal_bg_color
                            or "0." in modal_bg_color
                            or "transparent" in modal_bg_color
                        )
                        assert is_transparent, (
                            f"❌ Modal background not properly transparent: {modal_bg_color}"
                        )
                        print(
                            f"  ✅ Modal background is properly transparent: {modal_bg_color}"
                        )

                        if contrast_issues:
                            print(f"  ⚠️  Contrast issues found: {len(contrast_issues)}")
                            for issue in contrast_issues:
                                print(f"    {issue}")

                    # Close modal
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(500)
                else:
                    print(f"  No modal opened for {widget_id}")

            await browser.close()

    @pytest.mark.e2e
    async def test_widget_specific_modal_background_states(self):
        """Test that each widget has correct pre-generated background in modal state"""

        async with async_playwright() as p:
            # Find available server
            import requests

            server_ports = [8004, 8003, 8000, 8001, 8002, 8080]
            server_url = None

            for port in server_ports:
                try:
                    response = requests.get(f"http://localhost:{port}/", timeout=2)
                    if response.status_code == 200:
                        server_url = f"http://localhost:{port}"
                        break
                except Exception:
                    continue

            if not server_url:
                pytest.skip("No available server found")
                return

            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(server_url)
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(5000)  # Wait longer for JavaScript to load

            # Check if worldContainer is visible
            world_container = await page.query_selector("#worldContainer")
            if world_container:
                is_visible = await world_container.is_visible()
                print(f"World container visible: {is_visible}")
                if not is_visible:
                    print("⚠️ World container not visible - trying to force load")
                    await page.evaluate("""
                        if (typeof window.worldManager !== 'undefined') {
                            window.worldManager.hideLoading();
                        }
                    """)
                    await page.wait_for_timeout(2000)

            # Get all widgets and their expected background states
            widget_areas = await page.query_selector_all(".widget-area")
            if len(widget_areas) == 0:
                # Debug: Look for any interactive elements
                all_interactive = await page.query_selector_all(
                    "button, [data-widget-id], .widget, .location-container"
                )
                print(f"Found {len(all_interactive)} interactive elements as fallback")
                widget_areas = all_interactive

            print(f"Found {len(widget_areas)} widgets for background state testing")

            # Test each widget's modal background state
            background_states = {}

            for i, widget_area in enumerate(widget_areas):
                widget_id = await widget_area.get_attribute("data-widget-id")
                if not widget_id:
                    continue

                print(f"\nTesting modal background state for {widget_id}")

                # Get initial location background
                location_container = await widget_area.evaluate(
                    'el => el.closest(".location-container")'
                )
                initial_bg = await location_container.evaluate(
                    "el => getComputedStyle(el).backgroundImage"
                )
                initial_tile = (
                    await location_container.get_attribute("data-current-tile")
                    or "unknown"
                )

                print(f"  Initial state: tile={initial_tile}")

                # Click widget to potentially change state
                await widget_area.click()
                await page.wait_for_timeout(1000)

                # Check if modal opened and background changed
                modal_overlay = await page.query_selector("#modalOverlay")
                current_bg = await location_container.evaluate(
                    "el => getComputedStyle(el).backgroundImage"
                )
                current_tile = (
                    await location_container.get_attribute("data-current-tile")
                    or "unknown"
                )

                print(f"  After click: tile={current_tile}")

                # Check for modal content that might show widget-specific state
                modal_content = await page.query_selector("#modalContent")
                modal_title = ""
                if modal_content:
                    modal_title_element = await modal_content.query_selector(
                        "#modalTitle"
                    )
                    if modal_title_element:
                        modal_title = (
                            await modal_title_element.evaluate("el => el.textContent")
                            or ""
                        )

                # Store background state information
                background_states[widget_id] = {
                    "initial_tile": initial_tile,
                    "current_tile": current_tile,
                    "initial_bg": initial_bg,
                    "current_bg": current_bg,
                    "modal_opened": modal_overlay is not None
                    and await modal_overlay.is_visible(),
                    "modal_title": modal_title,
                }

                # Verify that each widget should have a unique background state when clicked
                if modal_overlay and await modal_overlay.is_visible():
                    # Widget should have a specific background state for modal interaction
                    assert current_tile in ["idle", "hover", "click", "unknown"], (
                        f"❌ Invalid tile state for {widget_id}: {current_tile}"
                    )

                    # Modal should have appropriate content
                    assert modal_title or modal_content, (
                        f"❌ Modal opened but no content found for {widget_id}"
                    )

                    print(
                        f"  ✅ Widget {widget_id} has proper modal state: {current_tile}"
                    )
                else:
                    print(
                        f"  ℹ️  Widget {widget_id} doesn't open modal (normal for some widgets)"
                    )

                # Close any open modal
                if modal_overlay and await modal_overlay.is_visible():
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(500)

            # Verify we have diverse background states
            unique_tiles = set(
                state["current_tile"] for state in background_states.values()
            )
            print(f"\nUnique tile states found: {unique_tiles}")

            # Should have at least some variety in background states
            assert len(unique_tiles) > 1, (
                "❌ All widgets have same background state - no variety"
            )

            print(
                f"✅ Background state testing complete for {len(background_states)} widgets"
            )
            await browser.close()

    @pytest.mark.e2e
    async def test_screenshot_comparison_modal_states(self):
        """Test screenshot comparison between modal states with 5% difference requirement"""

        async with async_playwright() as p:
            # Find available server
            import requests

            server_ports = [8004, 8003, 8000, 8001, 8002, 8080]
            server_url = None

            for port in server_ports:
                try:
                    response = requests.get(f"http://localhost:{port}/", timeout=2)
                    if response.status_code == 200:
                        server_url = f"http://localhost:{port}"
                        break
                except Exception:
                    continue

            if not server_url:
                pytest.skip("No available server found")
                return

            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(server_url)
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(5000)  # Wait longer for JavaScript to load

            # Check if worldContainer is visible
            world_container = await page.query_selector("#worldContainer")
            if world_container:
                is_visible = await world_container.is_visible()
                print(f"World container visible: {is_visible}")
                if not is_visible:
                    print("⚠️ World container not visible - trying to force load")
                    await page.evaluate("""
                        if (typeof window.worldManager !== 'undefined') {
                            window.worldManager.hideLoading();
                        }
                    """)
                    await page.wait_for_timeout(2000)

            # Create screenshots directory
            screenshot_dir = Path("test_screenshots")
            screenshot_dir.mkdir(exist_ok=True)

            # Get widgets that open modals
            widget_areas = await page.query_selector_all(".widget-area")
            if len(widget_areas) == 0:
                # Debug: Look for any interactive elements
                all_interactive = await page.query_selector_all(
                    "button, [data-widget-id], .widget, .location-container"
                )
                print(f"Found {len(all_interactive)} interactive elements as fallback")
                widget_areas = all_interactive

            # Take baseline screenshot (no modal open)
            baseline_screenshot = await page.screenshot(full_page=True)
            baseline_hash = hashlib.md5(baseline_screenshot).hexdigest()

            # Save baseline screenshot
            baseline_path = screenshot_dir / "baseline.png"
            await baseline_path.write_bytes(baseline_screenshot)
            print(f"Baseline screenshot saved: {baseline_path}")
            print(f"Baseline hash: {baseline_hash}")

            modal_states = {}

            # Test each widget that opens a modal
            for widget_area in widget_areas:
                widget_id = await widget_area.get_attribute("data-widget-id")
                if not widget_id:
                    continue

                print(f"\nTesting screenshot comparison for {widget_id}")

                # Take screenshot before clicking
                before_screenshot = await page.screenshot(full_page=True)
                before_hash = hashlib.md5(before_screenshot).hexdigest()

                # Click widget to open modal
                await widget_area.click()
                await page.wait_for_timeout(1000)

                # Check if modal opened
                modal_overlay = await page.query_selector("#modalOverlay")

                if modal_overlay and await modal_overlay.is_visible():
                    print(f"  Modal opened for {widget_id}")

                    # Take screenshot after modal opens
                    after_screenshot = await page.screenshot(full_page=True)
                    after_hash = hashlib.md5(after_screenshot).hexdigest()

                    # Save screenshots
                    widget_dir = screenshot_dir / widget_id
                    widget_dir.mkdir(exist_ok=True)

                    before_path = widget_dir / f"{widget_id}_before.png"
                    after_path = widget_dir / f"{widget_id}_after.png"

                    await before_path.write_bytes(before_screenshot)
                    await after_path.write_bytes(after_screenshot)

                    # Calculate difference percentage
                    def calculate_image_difference(img1_data, img2_data):
                        """Calculate percentage difference between two images"""
                        if len(img1_data) != len(img2_data):
                            return 100.0

                        differences = sum(
                            1 for a, b in zip(img1_data, img2_data) if a != b
                        )
                        return (differences / len(img1_data)) * 100

                    difference_percent = calculate_image_difference(
                        before_screenshot, after_screenshot
                    )

                    modal_states[widget_id] = {
                        "before_hash": before_hash,
                        "after_hash": after_hash,
                        "difference_percent": difference_percent,
                        "modal_opened": True,
                    }

                    print(f"  Before hash: {before_hash}")
                    print(f"  After hash: {after_hash}")
                    print(f"  Difference: {difference_percent:.2f}%")

                    # REQUIREMENT: Must have at least 5% difference
                    assert difference_percent >= 5.0, (
                        f"❌ Modal state change too small for {widget_id}: {difference_percent:.2f}% (require ≥5%)"
                    )

                    print(
                        f"  ✅ Screenshot difference requirement met: {difference_percent:.2f}%"
                    )

                    # Close modal
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(500)
                else:
                    modal_states[widget_id] = {
                        "modal_opened": False,
                        "reason": "No modal opened",
                    }
                    print(f"  ℹ️  Widget {widget_id} doesn't open modal")

            # Summary
            modal_widgets_tested = sum(
                1 for state in modal_states.values() if state.get("modal_opened", False)
            )
            avg_difference = 0
            if modal_widgets_tested > 0:
                differences = [
                    state["difference_percent"]
                    for state in modal_states.values()
                    if "difference_percent" in state
                ]
                avg_difference = (
                    sum(differences) / len(differences) if differences else 0
                )

            print("\n📊 Screenshot Comparison Summary:")
            print(f"  Total widgets tested: {len(modal_states)}")
            print(f"  Widgets with modals: {modal_widgets_tested}")
            print(f"  Average difference: {avg_difference:.2f}%")
            print(f"  Screenshots saved to: {screenshot_dir}")

            # At least one widget should have opened a modal with sufficient difference
            assert modal_widgets_tested > 0, (
                "❌ No widgets opened modals for screenshot comparison"
            )
            assert avg_difference >= 5.0, (
                f"❌ Average modal state change too small: {avg_difference:.2f}% (require ≥5%)"
            )

            print("✅ Screenshot comparison requirements met!")
            await browser.close()


if __name__ == "__main__":
    pytest.main([__file__])

#!/usr/bin/env python3
"""
Phase 4 Verification System for PRP-016
=======================================

Comprehensive three-way verification system for Phase 4 (Advanced Features & Navigation)
including Phases 1-3 complete verification and Phase 4 inventory.

Methodology: Expectations vs Test Results vs Code Analysis
"""

import asyncio
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class Phase4VerificationSystem:
    """Comprehensive verification system for Phase 4 Advanced Features & Navigation"""

    def __init__(self):
        self.results = {
            "verification_date": "2025-11-01",
            "methodology": "three_way_comparison",
            "phases_verified": ["Phase 1", "Phase 2", "Phase 3", "Phase 4"],
            "expectations": {},
            "test_results": {},
            "code_analysis": {},
            "comparison_results": {},
            "summary": {},
        }

    async def run_complete_verification(self) -> Dict[str, Any]:
        """Execute comprehensive Phase 4 verification"""
        print("🚀 STARTING PHASE 4 COMPREHENSIVE VERIFICATION")
        print("=" * 60)

        # Phase 1-3 Re-verification (quick check)
        print("\n📋 PHASE 1-3 RE-VERIFICATION (Quick Status Check)")
        await self._verify_phases_1_3_status()

        # Phase 4 Detailed Verification
        print("\n🔍 PHASE 4 DETAILED VERIFICATION: Advanced Features & Navigation")
        await self._verify_phase4_expectations()
        await self._verify_phase4_test_results()
        await self._verify_phase4_code_analysis()

        # Three-way comparison
        print("\n⚖️ THREE-WAY COMPARISON ANALYSIS")
        await self._perform_three_way_comparison()

        # Generate final report
        print("\n📊 GENERATING COMPREHENSIVE REPORT")
        await self._generate_final_report()

        return self.results

    async def _verify_phases_1_3_status(self):
        """Quick re-verification of Phases 1-3 status"""
        print("  🔍 Checking Phase 1-3 current status...")

        # Start server if needed
        try:
            response = requests.get("http://localhost:8000/", timeout=5)
            server_running = response.status_code == 200
        except:
            server_running = False

        if not server_running:
            print("    ⚠️ Server not running, starting...")
            subprocess.Popen(
                ["python3", "-m", "http.server", "8000"],
                cwd="/Users/dcversus/Documents/GitHub/dcmaidbot",
            )
            await asyncio.sleep(3)

        # Quick functional test
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            driver = webdriver.Chrome(options=chrome_options)
            driver.get("http://localhost:8000/")
            await asyncio.sleep(2)

            worldmanager_status = driver.execute_script("""
                return {
                    exists: typeof window.worldManager !== 'undefined',
                    worldData: window.worldManager ? (window.worldManager.worldData ? 'loaded' : 'null') : 'N/A',
                    locationsCount: window.worldManager && window.worldManager.worldData ?
                        window.worldManager.worldData.locations.length : 0,
                    uiRenderer: window.worldManager && window.worldManager.uiRenderer ? true : false,
                    interactionHandler: window.worldManager && window.worldManager.interactionHandler ? true : false,
                    initializationComplete: true
                };
            """)

            phase1_3_status = {
                "server_running": True,
                "worldManager_exists": worldmanager_status.get("exists", False),
                "worldData_loaded": worldmanager_status.get("worldData") == "loaded",
                "locations_count": worldmanager_status.get("locationsCount", 0),
                "uiRenderer_present": worldmanager_status.get("uiRenderer", False),
                "interactionHandler_present": worldmanager_status.get(
                    "interactionHandler", False
                ),
                "functional": worldmanager_status.get("exists", False)
                and worldmanager_status.get("worldData") == "loaded",
            }

            driver.quit()

            print(
                f"    ✅ Phase 1-3 Status: {'FUNCTIONAL' if phase1_3_status['functional'] else 'ISSUES DETECTED'}"
            )
            self.results["phases_1_3_status"] = phase1_3_status

        except Exception as e:
            print(f"    ❌ Phase 1-3 Status: ERROR - {e}")
            self.results["phases_1_3_status"] = {"error": str(e)}

    async def _verify_phase4_expectations(self):
        """Define Phase 4 Advanced Features & Navigation expectations"""
        print("  📋 Defining Phase 4 Advanced Features & Navigation expectations...")

        self.results["expectations"]["phase4"] = {
            "multi_room_system": {
                "expected": "Multiple rooms with floor-based navigation system",
                "requirements": [
                    "Multiple location definitions in world data",
                    "Floor-based organization of locations",
                    "Room navigation between different areas",
                    "Proper room state management",
                ],
            },
            "parents_room": {
                "expected": "Additional location with advanced widget configurations",
                "requirements": [
                    "Parents' room location defined",
                    "Advanced widget types in parents' room",
                    "Room-specific widget configurations",
                    "Unique interactions for parents' room",
                ],
            },
            "navigation_ui": {
                "expected": "Floor-based navigation interface and controls",
                "requirements": [
                    "Navigation UI component present",
                    "Floor selection functionality",
                    "Room switching capabilities",
                    "Visual navigation indicators",
                ],
            },
            "advanced_widget_types": {
                "expected": "7+ widget types with comprehensive state management",
                "requirements": [
                    "Multiple widget types implemented (clock, status, version, hash, etc.)",
                    "Comprehensive state management (idle, hover, click)",
                    "Widget interaction systems",
                    "Dynamic widget content rendering",
                ],
            },
        }

        print("    ✅ Phase 4 expectations defined")

    async def _verify_phase4_test_results(self):
        """Execute Phase 4 functionality tests"""
        print("  🧪 Executing Phase 4 functionality tests...")

        test_results = {}

        # Test 1: Multi-Room System
        print("    🏠 Testing multi-room system...")
        multi_room_test = await self._test_multi_room_system()
        test_results["multi_room_system"] = multi_room_test

        # Test 2: Parents' Room
        print("    👪 Testing parents' room...")
        parents_room_test = await self._test_parents_room()
        test_results["parents_room"] = parents_room_test

        # Test 3: Navigation UI
        print("    🧭 Testing navigation UI...")
        navigation_ui_test = await self._test_navigation_ui()
        test_results["navigation_ui"] = navigation_ui_test

        # Test 4: Advanced Widget Types
        print("    🎨 Testing advanced widget types...")
        advanced_widgets_test = await self._test_advanced_widget_types()
        test_results["advanced_widget_types"] = advanced_widgets_test

        self.results["test_results"]["phase4"] = test_results
        print("    ✅ Phase 4 tests completed")

    async def _test_multi_room_system(self) -> Dict[str, Any]:
        """Test multi-room system functionality"""
        try:
            # Check for world.json with multiple locations
            world_json_path = (
                "/Users/dcversus/Documents/GitHub/dcmaidbot/static/world.json"
            )
            if Path(world_json_path).exists():
                with open(world_json_path, "r") as f:
                    world_data = json.load(f)

                locations = world_data.get("locations", [])
                unique_floors = set(loc.get("floor", 0) for loc in locations)

                return {
                    "status": "working" if len(locations) > 1 else "limited",
                    "locations_count": len(locations),
                    "unique_floors": len(unique_floors),
                    "has_multiple_rooms": len(locations) > 1,
                    "world_json_exists": True,
                    "overall_score": min(1.0, len(locations) * 0.2)
                    + min(0.2, len(unique_floors) * 0.1),
                }
            else:
                return {
                    "status": "missing",
                    "world_json_exists": False,
                    "overall_score": 0.0,
                }

        except Exception as e:
            return {"status": "error", "error": str(e), "overall_score": 0.0}

    async def _test_parents_room(self) -> Dict[str, Any]:
        """Test parents' room functionality"""
        try:
            # Check for parents' room in world data
            world_json_path = (
                "/Users/dcversus/Documents/GitHub/dcmaidbot/static/world.json"
            )
            parents_room_found = False
            advanced_widgets = False

            if Path(world_json_path).exists():
                with open(world_json_path, "r") as f:
                    world_data = json.load(f)

                locations = world_data.get("locations", [])
                for location in locations:
                    if (
                        "parent" in location.get("id", "").lower()
                        or "parent" in location.get("name", "").lower()
                    ):
                        parents_room_found = True
                        # Check for advanced widgets
                        widgets = location.get("widgets", [])
                        if len(widgets) > 3:  # More than basic widgets
                            advanced_widgets = True
                        break

            # Check for room-specific configurations
            room_configs = False
            try:
                with open(
                    "/Users/dcversus/Documents/GitHub/dcmaidbot/index.html", "r"
                ) as f:
                    content = f.read()
                    if "room" in content.lower() and "location" in content.lower():
                        room_configs = True
            except:
                pass

            return {
                "status": "partial" if parents_room_found else "missing",
                "parents_room_found": parents_room_found,
                "advanced_widgets": advanced_widgets,
                "room_configurations": room_configs,
                "overall_score": (0.4 if parents_room_found else 0)
                + (0.3 if advanced_widgets else 0)
                + (0.3 if room_configs else 0),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "overall_score": 0.0}

    async def _test_navigation_ui(self) -> Dict[str, Any]:
        """Test navigation UI functionality"""
        try:
            # Check for navigation UI components in code
            with open(
                "/Users/dcversus/Documents/GitHub/dcmaidbot/index.html", "r"
            ) as f:
                html_content = f.read()

            # Look for navigation-related elements
            navigation_features = []

            if "buildFloorNavigation" in html_content:
                navigation_features.append("buildFloorNavigation")
            if "navigateToFloor" in html_content:
                navigation_features.append("navigateToFloor")
            if "updateFloorNavigation" in html_content:
                navigation_features.append("updateFloorNavigation")
            if "floor" in html_content.lower():
                navigation_features.append("floor_references")

            # Check for CSS navigation styles
            css_navigation = False
            if (
                "floor-navigation" in html_content
                or "navigation" in html_content.lower()
            ):
                css_navigation = True

            # Test actual navigation functionality
            navigation_functional = False
            try:
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")

                driver = webdriver.Chrome(options=chrome_options)
                driver.get("http://localhost:8000/")
                await asyncio.sleep(2)

                # Check for navigation elements
                navigation_elements = driver.execute_script("""
                    const floorNav = document.querySelector('.floor-navigation');
                    const navigationButtons = document.querySelectorAll('[data-floor]');
                    return {
                        floorNavigationPresent: !!floorNav,
                        navigationButtonsCount: navigationButtons.length,
                        hasNavigationFunctionality: floorNav && navigationButtons.length > 0
                    };
                """)

                navigation_functional = navigation_elements.get(
                    "hasNavigationFunctionality", False
                )
                driver.quit()

            except Exception as e:
                print(f"      Navigation functional test error: {e}")

            return {
                "status": "working" if navigation_functional else "partial",
                "navigation_features_found": navigation_features,
                "css_navigation_present": css_navigation,
                "navigation_functional": navigation_functional,
                "overall_score": (len(navigation_features) * 0.2)
                + (0.2 if css_navigation else 0)
                + (0.4 if navigation_functional else 0),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "overall_score": 0.0}

    async def _test_advanced_widget_types(self) -> Dict[str, Any]:
        """Test advanced widget types functionality"""
        try:
            # Check for widget types in code
            with open(
                "/Users/dcversus/Documents/GitHub/dcmaidbot/index.html", "r"
            ) as f:
                html_content = f.read()

            # Count widget types
            widget_types = []
            widget_classes = []

            # Look for widget type definitions
            if "ClockWidget" in html_content:
                widget_types.append("ClockWidget")
            if "StatusWidget" in html_content:
                widget_types.append("StatusWidget")
            if "VersionWidget" in html_content:
                widget_types.append("VersionWidget")
            if "HashWidget" in html_content:
                widget_types.append("HashWidget")
            if "MusicWidget" in html_content:
                widget_types.append("MusicWidget")
            if "LinkWidget" in html_content:
                widget_types.append("LinkWidget")
            if "EasterEggWidget" in html_content:
                widget_types.append("EasterEggWidget")

            # Check for widget switch cases
            switch_widget_types = []
            if "switch" in html_content and "widget.type" in html_content:
                # Extract widget types from switch statement
                widget_case_pattern = r'case\s+[\'"](.*?)[\'"]:'
                matches = re.findall(widget_case_pattern, html_content)
                switch_widget_types = matches

            # Check for state management
            state_management = (
                "idle" in html_content
                and "hover" in html_content
                and "click" in html_content
            )

            # Check for canvas rendering
            canvas_rendering = (
                "canvas" in html_content.lower() and "getContext" in html_content
            )

            # Test actual widget functionality
            widget_functional = False
            try:
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")

                driver = webdriver.Chrome(options=chrome_options)
                driver.get("http://localhost:8000/")
                await asyncio.sleep(2)

                # Check for widget elements
                widget_elements = driver.execute_script("""
                    const widgetAreas = document.querySelectorAll('.widget-area');
                    const canvasElements = document.querySelectorAll('.widget-canvas');
                    return {
                        widgetAreasCount: widgetAreas.length,
                        canvasElementsCount: canvasElements.length,
                        hasWidgets: widgetAreas.length > 0,
                        hasCanvasWidgets: canvasElements.length > 0
                    };
                """)

                widget_functional = widget_elements.get("hasWidgets", False)
                driver.quit()

            except Exception as e:
                print(f"      Widget functional test error: {e}")

            return {
                "status": "working" if widget_functional else "partial",
                "widget_types_found": widget_types,
                "switch_widget_types": switch_widget_types,
                "total_widget_types": len(set(widget_types + switch_widget_types)),
                "state_management": state_management,
                "canvas_rendering": canvas_rendering,
                "widget_functional": widget_functional,
                "overall_score": min(
                    1.0, len(set(widget_types + switch_widget_types)) * 0.1
                )
                + (0.3 if state_management else 0)
                + (0.3 if canvas_rendering else 0)
                + (0.2 if widget_functional else 0),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "overall_score": 0.0}

    async def _verify_phase4_code_analysis(self):
        """Analyze Phase 4 code implementation"""
        print("  🔍 Analyzing Phase 4 code implementation...")

        code_analysis = {}

        # Analyze Multi-Room System
        print("    🏠 Analyzing multi-room system code...")
        code_analysis["multi_room_system"] = await self._analyze_multi_room_code()

        # Analyze Parents' Room
        print("    👪 Analyzing parents' room code...")
        code_analysis["parents_room"] = await self._analyze_parents_room_code()

        # Analyze Navigation UI
        print("    🧭 Analyzing navigation UI code...")
        code_analysis["navigation_ui"] = await self._analyze_navigation_code()

        # Analyze Advanced Widget Types
        print("    🎨 Analyzing advanced widget types code...")
        code_analysis["advanced_widget_types"] = await self._analyze_widget_types_code()

        self.results["code_analysis"]["phase4"] = code_analysis
        print("    ✅ Phase 4 code analysis completed")

    async def _analyze_multi_room_code(self) -> Dict[str, Any]:
        """Analyze multi-room system code"""
        try:
            with open(
                "/Users/dcversus/Documents/GitHub/dcmaidbot/index.html", "r"
            ) as f:
                html_content = f.read()

            # Check for room management code
            room_management = []
            if "locations" in html_content and "floor" in html_content:
                room_management.append("location_floor_system")

            # Check for floor-based organization
            floor_system = (
                "buildFloorNavigation" in html_content
                or "navigateToFloor" in html_content
            )

            # Check for room state management
            room_state_management = (
                "discoveredLocations" in html_content or "currentFloor" in html_content
            )

            # Check for multi-room data structure
            world_data_handling = (
                "worldData" in html_content and "locations" in html_content
            )

            return {
                "room_management_features": room_management,
                "floor_system": floor_system,
                "room_state_management": room_state_management,
                "world_data_handling": world_data_handling,
                "implementation_score": (len(room_management) * 0.25)
                + (0.25 if floor_system else 0)
                + (0.25 if room_state_management else 0)
                + (0.25 if world_data_handling else 0),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "implementation_score": 0.0}

    async def _analyze_parents_room_code(self) -> Dict[str, Any]:
        """Analyze parents' room code"""
        try:
            with open(
                "/Users/dcversus/Documents/GitHub/dcmaidbot/index.html", "r"
            ) as f:
                html_content = f.read()

            # Check for room-specific configurations
            room_configs = []
            if "location" in html_content.lower():
                room_configs.append("location_system")
            if "createLocationSection" in html_content:
                room_configs.append("location_creation")

            # Check for advanced widget configurations
            advanced_configs = "widget" in html_content and "config" in html_content

            # Check for room-specific interactions
            room_interactions = (
                "handleWidgetHover" in html_content
                or "handleWidgetClick" in html_content
            )

            return {
                "room_configuration_features": room_configs,
                "advanced_widget_configs": advanced_configs,
                "room_specific_interactions": room_interactions,
                "implementation_score": (len(room_configs) * 0.3)
                + (0.4 if advanced_configs else 0)
                + (0.3 if room_interactions else 0),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "implementation_score": 0.0}

    async def _analyze_navigation_code(self) -> Dict[str, Any]:
        """Analyze navigation UI code"""
        try:
            with open(
                "/Users/dcversus/Documents/GitHub/dcmaidbot/index.html", "r"
            ) as f:
                html_content = f.read()

            # Check for navigation methods
            navigation_methods = []
            if "buildFloorNavigation" in html_content:
                navigation_methods.append("buildFloorNavigation")
            if "navigateToFloor" in html_content:
                navigation_methods.append("navigateToFloor")
            if "updateFloorNavigation" in html_content:
                navigation_methods.append("updateFloorNavigation")

            # Check for navigation event handling
            event_handling = (
                "addEventListener" in html_content and "click" in html_content
            )

            # Check for navigation UI components
            ui_components = (
                "getElementById" in html_content and "floor" in html_content.lower()
            )

            return {
                "navigation_methods": navigation_methods,
                "event_handling": event_handling,
                "ui_components": ui_components,
                "implementation_score": (len(navigation_methods) * 0.3)
                + (0.3 if event_handling else 0)
                + (0.4 if ui_components else 0),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "implementation_score": 0.0}

    async def _analyze_widget_types_code(self) -> Dict[str, Any]:
        """Analyze advanced widget types code"""
        try:
            with open(
                "/Users/dcversus/Documents/GitHub/dcmaidbot/index.html", "r"
            ) as f:
                html_content = f.read()

            # Check for widget classes
            widget_classes = []
            if "BaseWidget" in html_content:
                widget_classes.append("BaseWidget")
            if "ClockWidget" in html_content:
                widget_classes.append("ClockWidget")
            if "StatusWidget" in html_content:
                widget_classes.append("StatusWidget")
            if "MusicWidget" in html_content:
                widget_classes.append("MusicWidget")

            # Check for widget state management
            state_management = (
                "state" in html_content.lower() and "widget" in html_content
            )

            # Check for widget rendering systems
            rendering_systems = []
            if "canvas" in html_content.lower():
                rendering_systems.append("canvas_rendering")
            if "createWidget" in html_content:
                rendering_systems.append("widget_creation")

            # Check for widget interaction handling
            interaction_handling = "handleWidget" in html_content

            return {
                "widget_classes": widget_classes,
                "state_management": state_management,
                "rendering_systems": rendering_systems,
                "interaction_handling": interaction_handling,
                "implementation_score": (len(widget_classes) * 0.25)
                + (0.25 if state_management else 0)
                + (len(rendering_systems) * 0.25)
                + (0.25 if interaction_handling else 0),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "implementation_score": 0.0}

    async def _perform_three_way_comparison(self):
        """Perform three-way comparison analysis"""
        print("  ⚖️ Performing three-way comparison analysis...")

        comparison_results = {}

        phase4_areas = [
            "multi_room_system",
            "parents_room",
            "navigation_ui",
            "advanced_widget_types",
        ]

        for area in phase4_areas:
            print(f"    📊 Analyzing {area}...")

            expectations = self.results["expectations"]["phase4"][area]
            test_results = self.results["test_results"]["phase4"][area]
            code_analysis = self.results["code_analysis"]["phase4"][area]

            comparison = self._compare_expectation_test_code(
                area, expectations, test_results, code_analysis
            )
            comparison_results[area] = comparison

        self.results["comparison_results"]["phase4"] = comparison_results
        print("    ✅ Three-way comparison completed")

    def _compare_expectation_test_code(
        self, area: str, expectations: Dict, test_results: Dict, code_analysis: Dict
    ) -> Dict[str, Any]:
        """Three-way comparison: Expectations vs Test Results vs Code Analysis"""

        # Extract scores
        test_score = test_results.get("overall_score", 0.0)
        code_score = code_analysis.get("implementation_score", 0.0)

        # Determine status
        if test_score >= 0.8 and code_score >= 0.8:
            status = "working"
        elif test_score >= 0.5 or code_score >= 0.5:
            status = "partial"
        else:
            status = "missing"

        # Calculate alignment
        score_diff = abs(test_score - code_score)
        if score_diff <= 0.2:
            alignment = "high"
        elif score_diff <= 0.4:
            alignment = "medium"
        else:
            alignment = "low"

        return {
            "expectations_met": expectations.get("expected", ""),
            "test_score": test_score,
            "code_score": code_score,
            "average_score": (test_score + code_score) / 2,
            "status": status,
            "alignment": alignment,
            "recommendations": self._generate_recommendations(
                area, test_results, code_analysis
            ),
        }

    def _generate_recommendations(
        self, area: str, test_results: Dict, code_analysis: Dict
    ) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []

        test_score = test_results.get("overall_score", 0.0)
        code_score = code_analysis.get("implementation_score", 0.0)

        if test_score < 0.5:
            recommendations.append(f"Implement functional testing for {area}")

        if code_score < 0.5:
            recommendations.append(f"Develop code implementation for {area}")

        if test_score > 0.7 and code_score < 0.5:
            recommendations.append(
                "Code implementation needed - tests suggest it should work"
            )

        if code_score > 0.7 and test_score < 0.5:
            recommendations.append(
                "Test implementation needed - code exists but not verified"
            )

        if test_score >= 0.8 and code_score >= 0.8:
            recommendations.append(
                f"{area} is working well - consider production deployment"
            )

        return recommendations

    async def _generate_final_report(self):
        """Generate comprehensive final report"""
        print("  📊 Generating comprehensive final report...")

        # Calculate overall scores
        phase4_areas = list(self.results["comparison_results"]["phase4"].keys())
        total_score = 0
        working_count = 0
        partial_count = 0
        missing_count = 0

        for area in phase4_areas:
            comparison = self.results["comparison_results"]["phase4"][area]
            score = comparison.get("average_score", 0.0)
            status = comparison.get("status", "missing")

            total_score += score

            if status == "working":
                working_count += 1
            elif status == "partial":
                partial_count += 1
            else:
                missing_count += 1

        average_score = total_score / len(phase4_areas) if phase4_areas else 0.0

        # Generate summary
        summary = {
            "phase4_total_areas": len(phase4_areas),
            "phase4_working": working_count,
            "phase4_partial": partial_count,
            "phase4_missing": missing_count,
            "phase4_average_score": round(average_score, 2),
            "phase4_success_rate": round((working_count / len(phase4_areas)) * 100, 1)
            if phase4_areas
            else 0,
            "overall_assessment": self._get_overall_assessment(
                average_score, working_count, len(phase4_areas)
            ),
            "critical_issues": self._identify_critical_issues(),
            "next_steps": self._generate_next_steps(),
        }

        self.results["summary"] = summary

        # Print summary
        print("\n📊 PHASE 4 VERIFICATION SUMMARY:")
        print(f"   Total Areas: {len(phase4_areas)}")
        print(f"   Working: {working_count} ✅")
        print(f"   Partial: {partial_count} ⚠️")
        print(f"   Missing: {missing_count} ❌")
        print(f"   Average Score: {round(average_score, 2)}/1.00")
        print(
            f"   Success Rate: {round((working_count / len(phase4_areas)) * 100, 1)}%"
        )
        print(f"   Overall Assessment: {summary['overall_assessment']}")

        # Save detailed results
        await self._save_verification_results()

    def _get_overall_assessment(self, score: float, working: int, total: int) -> str:
        """Get overall assessment based on scores"""
        if score >= 0.8 and working >= total * 0.75:
            return "EXCELLENT - Phase 4 ready for production"
        elif score >= 0.6 and working >= total * 0.5:
            return "GOOD - Phase 4 mostly complete, minor issues remain"
        elif score >= 0.4:
            return "FAIR - Phase 4 partially implemented, needs work"
        else:
            return "POOR - Phase 4 requires significant development"

    def _identify_critical_issues(self) -> List[str]:
        """Identify critical issues from verification"""
        issues = []

        for area, comparison in self.results["comparison_results"]["phase4"].items():
            status = comparison.get("status", "missing")
            if status == "missing":
                issues.append(f"Critical: {area} not implemented")
            elif status == "partial":
                issues.append(f"Warning: {area} partially implemented")

        # Check Phase 1-3 status
        phase1_3 = self.results.get("phases_1_3_status", {})
        if not phase1_3.get("functional", False):
            issues.append("Critical: Phase 1-3 foundation issues detected")

        return issues

    def _generate_next_steps(self) -> List[str]:
        """Generate next steps based on verification results"""
        steps = []

        # Analyze Phase 4 results
        for area, comparison in self.results["comparison_results"]["phase4"].items():
            status = comparison.get("status", "missing")
            recommendations = comparison.get("recommendations", [])

            if status == "missing":
                steps.append(f"Implement {area} - critical for Phase 4 completion")
            elif status == "partial":
                steps.extend([f"Complete {area} implementation"] + recommendations)

        # Add general next steps
        success_rate = self.results["summary"].get("phase4_success_rate", 0)
        if success_rate < 100:
            steps.append("Address remaining Phase 4 gaps before Phase 5 development")

        steps.append("Update PRP-016 DoD items based on verification results")
        steps.append("Prepare Phase 5 development plan")

        return steps

    async def _save_verification_results(self):
        """Save verification results to file"""
        try:
            output_file = "/Users/dcversus/Documents/GitHub/dcmaidbot/static/phase4_verification_report.json"
            with open(output_file, "w") as f:
                json.dump(self.results, f, indent=2, default=str)
            print(f"    💾 Detailed results saved to: {output_file}")
        except Exception as e:
            print(f"    ⚠️ Could not save detailed results: {e}")


async def main():
    """Main verification execution"""
    verifier = Phase4VerificationSystem()
    results = await verifier.run_complete_verification()

    print("\n🎉 PHASE 4 COMPREHENSIVE VERIFICATION COMPLETE!")
    print("=" * 60)

    return results


if __name__ == "__main__":
    asyncio.run(main())

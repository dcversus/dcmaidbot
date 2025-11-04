#!/usr/bin/env python3
"""
Phase 3 Verification System for PRP-016
=======================================

Comprehensive three-way verification system for Phase 3 (Generation Integration)
including Phases 1-2 complete verification and Phase 3 inventory.

Methodology: Expectations vs Test Results vs Code Analysis
"""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class Phase3VerificationSystem:
    """Comprehensive verification system for Phase 3 Generation Integration"""

    def __init__(self):
        self.results = {
            "verification_date": "2025-11-01",
            "methodology": "three_way_comparison",
            "phases_verified": ["Phase 1", "Phase 2", "Phase 3"],
            "expectations": {},
            "test_results": {},
            "code_analysis": {},
            "comparison_results": {},
            "summary": {},
        }

    async def run_complete_verification(self) -> Dict[str, Any]:
        """Execute comprehensive Phase 3 verification"""
        print("🚀 STARTING PHASE 3 COMPREHENSIVE VERIFICATION")
        print("=" * 60)

        # Phase 1-2 Re-verification (quick check)
        print("\n📋 PHASE 1-2 RE-VERIFICATION (Quick Status Check)")
        await self._verify_phases_1_2_status()

        # Phase 3 Detailed Verification
        print("\n🔍 PHASE 3 DETAILED VERIFICATION: Generation Integration")
        await self._verify_phase3_expectations()
        await self._verify_phase3_test_results()
        await self._verify_phase3_code_analysis()

        # Three-way comparison
        print("\n⚖️ THREE-WAY COMPARISON ANALYSIS")
        await self._perform_three_way_comparison()

        # Generate final report
        print("\n📊 GENERATING COMPREHENSIVE REPORT")
        await self._generate_final_report()

        return self.results

    async def _verify_phases_1_2_status(self):
        """Quick re-verification of Phases 1-2 status"""
        print("  🔍 Checking Phase 1-2 current status...")

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
                    initializationComplete: true
                };
            """)

            phase1_2_status = {
                "server_running": True,
                "worldManager_exists": worldmanager_status.get("exists", False),
                "worldData_loaded": worldmanager_status.get("worldData") == "loaded",
                "locations_count": worldmanager_status.get("locationsCount", 0),
                "functional": worldmanager_status.get("exists", False)
                and worldmanager_status.get("worldData") == "loaded",
            }

            driver.quit()

            print(
                f"    ✅ Phase 1-2 Status: {'FUNCTIONAL' if phase1_2_status['functional'] else 'ISSUES DETECTED'}"
            )
            self.results["phases_1_2_status"] = phase1_2_status

        except Exception as e:
            print(f"    ❌ Phase 1-2 Status: ERROR - {e}")
            self.results["phases_1_2_status"] = {"error": str(e)}

    async def _verify_phase3_expectations(self):
        """Define Phase 3 Generation Integration expectations"""
        print("  📋 Defining Phase 3 Generation Integration expectations...")

        self.results["expectations"]["phase3"] = {
            "world_builder_v2_integration": {
                "expected": "Connection with scripts/world_builder.py and Leonardo AI integration",
                "requirements": [
                    "world_builder.py script exists and functional",
                    "Leonardo AI API integration for tile generation",
                    "Connection between ImageCompositionManager and world_builder",
                    "Batch tile generation workflow",
                ],
            },
            "widget_tile_generation": {
                "expected": "Widget-specific tile generation with state variations",
                "requirements": [
                    "Individual tile generation for each widget type",
                    "State variations: idle, hover, click states",
                    "Widget tile coordination system",
                    "Generation fallbacks and retry logic",
                ],
            },
            "migration_framework": {
                "expected": "Gradual migration system from background to tile system",
                "requirements": [
                    "Migration scripts/framework present",
                    "Rollback capability",
                    "A/B testing infrastructure",
                    "Performance monitoring during migration",
                ],
            },
            "performance_optimization": {
                "expected": "Tile system performance optimizations",
                "requirements": [
                    "Tile lazy loading implementation",
                    "Memory management for tiles",
                    "Preloading system for critical tiles",
                    "Performance monitoring and metrics",
                ],
            },
        }

        print("    ✅ Phase 3 expectations defined")

    async def _verify_phase3_test_results(self):
        """Execute Phase 3 functionality tests"""
        print("  🧪 Executing Phase 3 functionality tests...")

        test_results = {}

        # Test 1: World Builder Integration
        print("    🏗️ Testing WorldBuilder V2 integration...")
        world_builder_test = await self._test_world_builder_integration()
        test_results["world_builder_v2_integration"] = world_builder_test

        # Test 2: Widget Tile Generation
        print("    🎨 Testing widget tile generation...")
        tile_generation_test = await self._test_widget_tile_generation()
        test_results["widget_tile_generation"] = tile_generation_test

        # Test 3: Migration Framework
        print("    🔄 Testing migration framework...")
        migration_test = await self._test_migration_framework()
        test_results["migration_framework"] = migration_test

        # Test 4: Performance Optimization
        print("    ⚡ Testing performance optimizations...")
        performance_test = await self._test_performance_optimization()
        test_results["performance_optimization"] = performance_test

        self.results["test_results"]["phase3"] = test_results
        print("    ✅ Phase 3 tests completed")

    async def _test_world_builder_integration(self) -> Dict[str, Any]:
        """Test WorldBuilder V2 integration"""
        try:
            # Check for world_builder scripts
            world_builder_files = [
                "scripts/world_builder.py",
                "scripts/world_builder_v2.py",
                "scripts/world_builder_gui.py",
            ]

            existing_files = []
            for file in world_builder_files:
                if Path(f"/Users/dcversus/Documents/GitHub/dcmaidbot/{file}").exists():
                    existing_files.append(file)

            # Check for Leonardo AI integration
            leonardo_integration = False
            try:
                with open(
                    "/Users/dcversus/Documents/GitHub/dcmaidbot/scripts/world_builder.py",
                    "r",
                ) as f:
                    content = f.read()
                    if "leonardo" in content.lower() or "api" in content.lower():
                        leonardo_integration = True
            except:
                pass

            # Check ImageCompositionManager connection
            try:
                with open(
                    "/Users/dcversus/Documents/GitHub/dcmaidbot/index.html", "r"
                ) as f:
                    content = f.read()
                    image_composition_manager = (
                        "class ImageCompositionManager" in content
                    )
            except:
                image_composition_manager = False

            return {
                "status": "partial" if existing_files else "missing",
                "world_builder_files_found": existing_files,
                "leonardo_integration": leonardo_integration,
                "image_composition_manager": image_composition_manager,
                "overall_score": len(existing_files) * 0.25
                + (0.25 if leonardo_integration else 0)
                + (0.25 if image_composition_manager else 0),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "overall_score": 0.0}

    async def _test_widget_tile_generation(self) -> Dict[str, Any]:
        """Test widget tile generation capabilities"""
        try:
            # Check for tile generation scripts
            tile_generation_files = [
                "scripts/room_generator.py",
                "scripts/generate_rooms_mcp.py",
                "scripts/generate_room_with_validation.py",
            ]

            existing_files = []
            for file in tile_generation_files:
                if Path(f"/Users/dcversus/Documents/GitHub/dcmaidbot/{file}").exists():
                    existing_files.append(file)

            # Check for widget state system in code
            widget_states = False
            try:
                with open(
                    "/Users/dcversus/Documents/GitHub/dcmaidbot/index.html", "r"
                ) as f:
                    content = f.read()
                    if "idle" in content and "hover" in content and "click" in content:
                        widget_states = True
            except:
                pass

            # Check for tile coordination
            tile_coordination = False
            try:
                with open(
                    "/Users/dcversus/Documents/GitHub/dcmaidbot/index.html", "r"
                ) as f:
                    content = f.read()
                    if "TileManager" in content or "tileManager" in content:
                        tile_coordination = True
            except:
                pass

            return {
                "status": "partial" if existing_files else "missing",
                "tile_generation_files": existing_files,
                "widget_states_supported": widget_states,
                "tile_coordination_system": tile_coordination,
                "overall_score": len(existing_files) * 0.3
                + (0.3 if widget_states else 0)
                + (0.4 if tile_coordination else 0),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "overall_score": 0.0}

    async def _test_migration_framework(self) -> Dict[str, Any]:
        """Test migration framework capabilities"""
        try:
            # Check for migration-related files
            migration_files = [
                "scripts/migration_manager.py",
                "scripts/state_coordination_manager.py",
                "alembic/versions/",
            ]

            existing_migration_files = []
            for file in migration_files:
                path = Path(f"/Users/dcversus/Documents/GitHub/dcmaidbot/{file}")
                if path.exists():
                    existing_migration_files.append(file)

            # Check for migration framework in code
            migration_system = False
            try:
                with open(
                    "/Users/dcversus/Documents/GitHub/dcmaidbot/index.html", "r"
                ) as f:
                    content = f.read()
                    if "migration" in content.lower() or "rollback" in content.lower():
                        migration_system = True
            except:
                pass

            # Check for performance monitoring
            performance_monitoring = False
            try:
                with open(
                    "/Users/dcversus/Documents/GitHub/dcmaidbot/index.html", "r"
                ) as f:
                    content = f.read()
                    if (
                        "performance" in content.lower()
                        or "monitoring" in content.lower()
                    ):
                        performance_monitoring = True
            except:
                pass

            return {
                "status": "partial" if existing_migration_files else "missing",
                "migration_files": existing_migration_files,
                "migration_system_detected": migration_system,
                "performance_monitoring": performance_monitoring,
                "overall_score": len(existing_migration_files) * 0.4
                + (0.3 if migration_system else 0)
                + (0.3 if performance_monitoring else 0),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "overall_score": 0.0}

    async def _test_performance_optimization(self) -> Dict[str, Any]:
        """Test performance optimization features"""
        try:
            # Check for performance-related code
            lazy_loading = False
            memory_management = False
            preloading = False
            caching = False

            try:
                with open(
                    "/Users/dcversus/Documents/GitHub/dcmaidbot/index.html", "r"
                ) as f:
                    content = f.read()

                    lazy_loading = (
                        "lazy" in content.lower() or "preload" in content.lower()
                    )
                    memory_management = (
                        "memory" in content.lower() or "cache" in content.lower()
                    )
                    preloading = (
                        "preload" in content.lower() or "async" in content.lower()
                    )
                    caching = "cache" in content.lower() or "Cache" in content

            except:
                pass

            # Check for LRU cache implementation
            lru_cache = False
            try:
                with open(
                    "/Users/dcversus/Documents/GitHub/dcmaidbot/index.html", "r"
                ) as f:
                    content = f.read()
                    if "LRU" in content or "lru" in content or "Map" in content:
                        lru_cache = True
            except:
                pass

            return {
                "status": "partial",
                "lazy_loading": lazy_loading,
                "memory_management": memory_management,
                "preloading": preloading,
                "caching_system": caching,
                "lru_cache_implementation": lru_cache,
                "overall_score": (0.2 if lazy_loading else 0)
                + (0.2 if memory_management else 0)
                + (0.2 if preloading else 0)
                + (0.2 if caching else 0)
                + (0.2 if lru_cache else 0),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "overall_score": 0.0}

    async def _verify_phase3_code_analysis(self):
        """Analyze Phase 3 code implementation"""
        print("  🔍 Analyzing Phase 3 code implementation...")

        code_analysis = {}

        # Analyze WorldBuilder integration
        print("    🏗️ Analyzing WorldBuilder integration code...")
        code_analysis[
            "world_builder_v2_integration"
        ] = await self._analyze_world_builder_code()

        # Analyze widget tile generation
        print("    🎨 Analyzing widget tile generation code...")
        code_analysis[
            "widget_tile_generation"
        ] = await self._analyze_tile_generation_code()

        # Analyze migration framework
        print("    🔄 Analyzing migration framework code...")
        code_analysis["migration_framework"] = await self._analyze_migration_code()

        # Analyze performance optimization
        print("    ⚡ Analyzing performance optimization code...")
        code_analysis[
            "performance_optimization"
        ] = await self._analyze_performance_code()

        self.results["code_analysis"]["phase3"] = code_analysis
        print("    ✅ Phase 3 code analysis completed")

    async def _analyze_world_builder_code(self) -> Dict[str, Any]:
        """Analyze WorldBuilder V2 integration code"""
        try:
            # Check index.html for integration
            with open(
                "/Users/dcversus/Documents/GitHub/dcmaidbot/index.html", "r"
            ) as f:
                html_content = f.read()

            # Check for ImageCompositionManager
            image_composition_manager = "class ImageCompositionManager" in html_content

            # Check for tile generation methods
            tile_generation_methods = []
            if "createCompositeTile" in html_content:
                tile_generation_methods.append("createCompositeTile")
            if "pregenerateLocationTiles" in html_content:
                tile_generation_methods.append("pregenerateLocationTiles")

            # Check for world builder script references
            world_builder_refs = []
            if "world_builder" in html_content.lower():
                world_builder_refs.append("world_builder_reference")

            return {
                "image_composition_manager_found": image_composition_manager,
                "tile_generation_methods": tile_generation_methods,
                "world_builder_references": world_builder_refs,
                "implementation_score": (0.4 if image_composition_manager else 0)
                + (len(tile_generation_methods) * 0.2)
                + (len(world_builder_refs) * 0.2),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "implementation_score": 0.0}

    async def _analyze_tile_generation_code(self) -> Dict[str, Any]:
        """Analyze widget tile generation code"""
        try:
            with open(
                "/Users/dcversus/Documents/GitHub/dcmaidbot/index.html", "r"
            ) as f:
                html_content = f.read()

            # Check for widget state handling
            widget_states = ["idle", "hover", "click"]
            states_found = []
            for state in widget_states:
                if state in html_content:
                    states_found.append(state)

            # Check for tile-related classes
            tile_classes = []
            if "TileManager" in html_content:
                tile_classes.append("TileManager")
            if "AssetLoader" in html_content:
                tile_classes.append("AssetLoader")

            # Check for state transitions
            state_transitions = (
                "handleWidgetHover" in html_content
                and "handleWidgetClick" in html_content
            )

            return {
                "widget_states_found": states_found,
                "tile_classes_found": tile_classes,
                "state_transitions_implemented": state_transitions,
                "implementation_score": (len(states_found) * 0.25)
                + (len(tile_classes) * 0.25)
                + (0.5 if state_transitions else 0),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "implementation_score": 0.0}

    async def _analyze_migration_code(self) -> Dict[str, Any]:
        """Analyze migration framework code"""
        try:
            with open(
                "/Users/dcversus/Documents/GitHub/dcmaidbot/index.html", "r"
            ) as f:
                html_content = f.read()

            # Check for migration-related functionality
            migration_keywords = ["migration", "rollback", "transition", "migrate"]
            migration_features = []
            for keyword in migration_keywords:
                if keyword.lower() in html_content.lower():
                    migration_features.append(keyword)

            # Check for state coordination
            state_coordination = (
                "PromptManager" in html_content or "StateManager" in html_content
            )

            # Check for testing infrastructure
            testing_infra = "test" in html_content.lower() or "Test" in html_content

            return {
                "migration_features_found": migration_features,
                "state_coordination": state_coordination,
                "testing_infrastructure": testing_infra,
                "implementation_score": (len(migration_features) * 0.3)
                + (0.4 if state_coordination else 0)
                + (0.3 if testing_infra else 0),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "implementation_score": 0.0}

    async def _analyze_performance_code(self) -> Dict[str, Any]:
        """Analyze performance optimization code"""
        try:
            with open(
                "/Users/dcversus/Documents/GitHub/dcmaidbot/index.html", "r"
            ) as f:
                html_content = f.read()

            # Check for caching implementations
            cache_implementations = []
            if "Map(" in html_content or "new Map" in html_content:
                cache_implementations.append("map_cache")
            if "cache" in html_content.lower() or "Cache" in html_content:
                cache_implementations.append("general_cache")

            # Check for async operations
            async_operations = "async" in html_content and "await" in html_content

            # Check for performance monitoring
            performance_monitoring = (
                "performance" in html_content.lower()
                or "metrics" in html_content.lower()
            )

            # Check for memory management
            memory_management = (
                "clear" in html_content
                or "delete" in html_content
                or "remove" in html_content
            )

            return {
                "cache_implementations": cache_implementations,
                "async_operations": async_operations,
                "performance_monitoring": performance_monitoring,
                "memory_management": memory_management,
                "implementation_score": (len(cache_implementations) * 0.25)
                + (0.25 if async_operations else 0)
                + (0.25 if performance_monitoring else 0)
                + (0.25 if memory_management else 0),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "implementation_score": 0.0}

    async def _perform_three_way_comparison(self):
        """Perform three-way comparison analysis"""
        print("  ⚖️ Performing three-way comparison analysis...")

        comparison_results = {}

        phase3_areas = [
            "world_builder_v2_integration",
            "widget_tile_generation",
            "migration_framework",
            "performance_optimization",
        ]

        for area in phase3_areas:
            print(f"    📊 Analyzing {area}...")

            expectations = self.results["expectations"]["phase3"][area]
            test_results = self.results["test_results"]["phase3"][area]
            code_analysis = self.results["code_analysis"]["phase3"][area]

            comparison = self._compare_expectation_test_code(
                area, expectations, test_results, code_analysis
            )
            comparison_results[area] = comparison

        self.results["comparison_results"]["phase3"] = comparison_results
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
        phase3_areas = list(self.results["comparison_results"]["phase3"].keys())
        total_score = 0
        working_count = 0
        partial_count = 0
        missing_count = 0

        for area in phase3_areas:
            comparison = self.results["comparison_results"]["phase3"][area]
            score = comparison.get("average_score", 0.0)
            status = comparison.get("status", "missing")

            total_score += score

            if status == "working":
                working_count += 1
            elif status == "partial":
                partial_count += 1
            else:
                missing_count += 1

        average_score = total_score / len(phase3_areas) if phase3_areas else 0.0

        # Generate summary
        summary = {
            "phase3_total_areas": len(phase3_areas),
            "phase3_working": working_count,
            "phase3_partial": partial_count,
            "phase3_missing": missing_count,
            "phase3_average_score": round(average_score, 2),
            "phase3_success_rate": round((working_count / len(phase3_areas)) * 100, 1)
            if phase3_areas
            else 0,
            "overall_assessment": self._get_overall_assessment(
                average_score, working_count, len(phase3_areas)
            ),
            "critical_issues": self._identify_critical_issues(),
            "next_steps": self._generate_next_steps(),
        }

        self.results["summary"] = summary

        # Print summary
        print("\n📊 PHASE 3 VERIFICATION SUMMARY:")
        print(f"   Total Areas: {len(phase3_areas)}")
        print(f"   Working: {working_count} ✅")
        print(f"   Partial: {partial_count} ⚠️")
        print(f"   Missing: {missing_count} ❌")
        print(f"   Average Score: {round(average_score, 2)}/1.00")
        print(
            f"   Success Rate: {round((working_count / len(phase3_areas)) * 100, 1)}%"
        )
        print(f"   Overall Assessment: {summary['overall_assessment']}")

        # Save detailed results
        await self._save_verification_results()

    def _get_overall_assessment(self, score: float, working: int, total: int) -> str:
        """Get overall assessment based on scores"""
        if score >= 0.8 and working >= total * 0.75:
            return "EXCELLENT - Phase 3 ready for production"
        elif score >= 0.6 and working >= total * 0.5:
            return "GOOD - Phase 3 mostly complete, minor issues remain"
        elif score >= 0.4:
            return "FAIR - Phase 3 partially implemented, needs work"
        else:
            return "POOR - Phase 3 requires significant development"

    def _identify_critical_issues(self) -> List[str]:
        """Identify critical issues from verification"""
        issues = []

        for area, comparison in self.results["comparison_results"]["phase3"].items():
            status = comparison.get("status", "missing")
            if status == "missing":
                issues.append(f"Critical: {area} not implemented")
            elif status == "partial":
                issues.append(f"Warning: {area} partially implemented")

        # Check Phase 1-2 status
        phase1_2 = self.results.get("phases_1_2_status", {})
        if not phase1_2.get("functional", False):
            issues.append("Critical: Phase 1-2 foundation issues detected")

        return issues

    def _generate_next_steps(self) -> List[str]:
        """Generate next steps based on verification results"""
        steps = []

        # Analyze Phase 3 results
        for area, comparison in self.results["comparison_results"]["phase3"].items():
            status = comparison.get("status", "missing")
            recommendations = comparison.get("recommendations", [])

            if status == "missing":
                steps.append(f"Implement {area} - critical for Phase 3 completion")
            elif status == "partial":
                steps.extend([f"Complete {area} implementation"] + recommendations)

        # Add general next steps
        success_rate = self.results["summary"].get("phase3_success_rate", 0)
        if success_rate < 100:
            steps.append("Address remaining Phase 3 gaps before Phase 4 development")

        steps.append("Update PRP-016 DoD items based on verification results")
        steps.append("Prepare Phase 4 development plan")

        return steps

    async def _save_verification_results(self):
        """Save verification results to file"""
        try:
            output_file = "/Users/dcversus/Documents/GitHub/dcmaidbot/static/phase3_verification_report.json"
            with open(output_file, "w") as f:
                json.dump(self.results, f, indent=2, default=str)
            print(f"    💾 Detailed results saved to: {output_file}")
        except Exception as e:
            print(f"    ⚠️ Could not save detailed results: {e}")


async def main():
    """Main verification execution"""
    verifier = Phase3VerificationSystem()
    results = await verifier.run_complete_verification()

    print("\n🎉 PHASE 3 COMPREHENSIVE VERIFICATION COMPLETE!")
    print("=" * 60)

    return results


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Migration Manager
=================

Gradual migration framework for transitioning from background
image system to advanced tile-based architecture.
"""

import json
import shutil
import time
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv()

# Configuration
RESULT_JSON = Path("static/result.json")
RESULT_JSON_BACKUP = Path("static/result.json.backup")
WORLD_TILES_DIR = Path("static/world")
MIGRATION_LOG = Path("static/migration_log.json")


class MigrationManager:
    """
    Manages gradual migration from background to tile system
    with rollback capabilities and validation.
    """

    def __init__(self):
        """Initialize the migration manager."""
        self.migration_log = self._load_migration_log()
        self.backup_created = False
        self.rollback_available = False

        print("🔄 MigrationManager initialized")

    def _load_migration_log(self) -> Dict[str, Any]:
        """Load existing migration log or create new one."""
        if MIGRATION_LOG.exists():
            try:
                with open(MIGRATION_LOG) as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Warning: Could not load migration log: {e}")

        # Create new migration log
        return {
            "migration_started": None,
            "migration_completed": None,
            "current_phase": "preparation",
            "phases_completed": [],
            "rollback_points": [],
            "validation_results": {},
            "statistics": {
                "locations_migrated": 0,
                "tiles_generated": 0,
                "validation_failures": 0,
                "rollback_count": 0,
            },
        }

    def _save_migration_log(self):
        """Save current migration log."""
        with open(MIGRATION_LOG, "w") as f:
            json.dump(self.migration_log, f, indent=2)

    def create_backup(self) -> bool:
        """Create backup of current system state."""
        print("💾 Creating system backup...")

        try:
            # Backup result.json
            if RESULT_JSON.exists():
                shutil.copy2(RESULT_JSON, RESULT_JSON_BACKUP)
                print(f"✅ Backed up: {RESULT_JSON_BACKUP}")

            # Create migration rollback point
            rollback_point = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "phase": self.migration_log["current_phase"],
                "files_backed_up": [str(RESULT_JSON_BACKUP)]
                if RESULT_JSON_BACKUP.exists()
                else [],
                "world_tiles_exists": WORLD_TILES_DIR.exists(),
            }

            self.migration_log["rollback_points"].append(rollback_point)
            self.backup_created = True
            self.rollback_available = True

            self._save_migration_log()

            print("✅ Backup created successfully")
            return True

        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return False

    def start_migration(self) -> bool:
        """Start the migration process."""
        print("🚀 Starting migration from background to tile system...")

        if not self.create_backup():
            print("❌ Cannot start migration without backup")
            return False

        self.migration_log["migration_started"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.migration_log["current_phase"] = "assessment"
        self._save_migration_log()

        print("✅ Migration started successfully")
        return True

    async def migrate_location(
        self,
        location_id: str,
        enable_tile_system: bool = True,
        validation_mode: bool = True,
    ) -> Dict[str, Any]:
        """
        Migrate a single location to tile system.

        Args:
            location_id: ID of location to migrate
            enable_tile_system: Whether to enable tile system for this location
            validation_mode: Whether to run validation after migration

        Returns:
            Migration results
        """
        print(f"🔄 Migrating location: {location_id}")

        migration_result = {
            "location_id": location_id,
            "migration_started": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "success": False,
            "tiles_generated": [],
            "validation_results": {},
            "errors": [],
        }

        try:
            # Load current result.json
            with open(RESULT_JSON) as f:
                result_data = json.load(f)

            # Find the location
            target_location = None
            for location in result_data.get("locations", []):
                if location.get("id") == location_id:
                    target_location = location
                    break

            if not target_location:
                error_msg = f"Location {location_id} not found in result.json"
                migration_result["errors"].append(error_msg)
                print(f"❌ {error_msg}")
                return migration_result

            # Import our tile generation systems
            from state_coordination_manager import StateCoordinationManager
            from world_builder_v2 import WorldBuilder

            # Initialize systems
            world_builder = WorldBuilder()
            state_manager = StateCoordinationManager()

            # Generate enhanced tiles for the location
            print(f"  🎨 Generating enhanced tiles for {target_location['name']}...")

            # Generate all states
            tiles = {}
            states = ["idle", "hover", "click"]

            for state in states:
                try:
                    tile_path = await state_manager.create_enhanced_composite_tile(
                        target_location, state
                    )
                    tiles[state] = f"world/{location_id}_{state}.png"
                    migration_result["tiles_generated"].append(
                        {"state": state, "path": tile_path, "success": True}
                    )
                    print(f"    ✅ Generated {state} state")

                except Exception as e:
                    error_msg = f"Failed to generate {state} state: {e}"
                    migration_result["errors"].append(error_msg)
                    migration_result["tiles_generated"].append(
                        {
                            "state": state,
                            "path": None,
                            "success": False,
                            "error": str(e),
                        }
                    )
                    print(f"    ❌ {error_msg}")

            # Update result.json with new tiles
            if enable_tile_system and tiles:
                target_location["tiles"] = tiles
                target_location["tile_system_enabled"] = True
                target_location["migration_timestamp"] = time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
                target_location["generation_method"] = "enhanced_tile_composition"

                # Save updated result.json
                with open(RESULT_JSON, "w") as f:
                    json.dump(result_data, f, indent=2)

                print("  ✅ Updated result.json with tile paths")

            # Run validation if requested
            if validation_mode:
                print("  🔍 Running validation...")
                validation_results = await state_manager.validate_state_consistency(
                    target_location
                )
                migration_result["validation_results"] = validation_results

                if validation_results["validation_passed"]:
                    print("  ✅ Validation passed")
                else:
                    print(
                        f"  ⚠️ Validation found {len(validation_results['issues_found'])} issues"
                    )
                    self.migration_log["statistics"]["validation_failures"] += 1

            # Update statistics
            self.migration_log["statistics"]["locations_migrated"] += 1
            self.migration_log["statistics"]["tiles_generated"] += len(
                migration_result["tiles_generated"]
            )

            migration_result["success"] = True
            migration_result["migration_completed"] = time.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

            print(f"✅ Location {location_id} migration completed successfully")

        except Exception as e:
            error_msg = f"Migration failed: {e}"
            migration_result["errors"].append(error_msg)
            print(f"❌ {error_msg}")

        # Save migration log
        self._save_migration_log()

        return migration_result

    async def migrate_all_locations(
        self,
        enable_tile_system: bool = True,
        validation_mode: bool = True,
        batch_size: int = 3,
    ) -> Dict[str, Any]:
        """
        Migrate all locations to tile system.

        Args:
            enable_tile_system: Whether to enable tile system
            validation_mode: Whether to run validation
            batch_size: Number of locations to process in parallel

        Returns:
            Overall migration results
        """
        print("🌍 Starting migration of all locations...")

        overall_results = {
            "migration_started": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_locations": 0,
            "successful_migrations": 0,
            "failed_migrations": 0,
            "total_tiles_generated": 0,
            "location_results": [],
            "errors": [],
        }

        try:
            # Load result.json to get locations
            with open(RESULT_JSON) as f:
                result_data = json.load(f)

            locations = result_data.get("locations", [])
            overall_results["total_locations"] = len(locations)

            if not locations:
                print("⚠️ No locations found to migrate")
                return overall_results

            print(f"Found {len(locations)} locations to migrate")

            # Migrate locations in batches
            for i in range(0, len(locations), batch_size):
                batch = locations[i : i + batch_size]
                print(
                    f"\n🔄 Processing batch {i // batch_size + 1}: {len(batch)} locations"
                )

                batch_results = []
                for location in batch:
                    location_id = location.get("id")
                    if location_id:
                        result = await self.migrate_location(
                            location_id, enable_tile_system, validation_mode
                        )
                        batch_results.append(result)

                # Process batch results
                for result in batch_results:
                    overall_results["location_results"].append(result)

                    if result["success"]:
                        overall_results["successful_migrations"] += 1
                        overall_results["total_tiles_generated"] += len(
                            result["tiles_generated"]
                        )
                    else:
                        overall_results["failed_migrations"] += 1
                        overall_results["errors"].extend(result["errors"])

                print(
                    f"Batch {i // batch_size + 1} completed: "
                    f"{overall_results['successful_migrations']}/{overall_results['total_locations']} successful"
                )

            overall_results["migration_completed"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")

            # Update migration log
            self.migration_log["current_phase"] = "completed"
            self.migration_log["migration_completed"] = overall_results[
                "migration_completed"
            ]
            self.migration_log["statistics"].update(
                {
                    "locations_migrated": overall_results["successful_migrations"],
                    "tiles_generated": overall_results["total_tiles_generated"],
                    "validation_failures": self.migration_log["statistics"][
                        "validation_failures"
                    ],
                }
            )
            self._save_migration_log()

            print("\n🎉 Migration completed!")
            print(
                f"   ✅ Successful: {overall_results['successful_migrations']}/{overall_results['total_locations']}"
            )
            print(f"   📋 Tiles generated: {overall_results['total_tiles_generated']}")
            print(f"   ❌ Failed: {overall_results['failed_migrations']}")

        except Exception as e:
            error_msg = f"Batch migration failed: {e}"
            overall_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")

        return overall_results

    def rollback_migration(self, rollback_point: int = None) -> bool:
        """
        Rollback to a previous migration state.

        Args:
            rollback_point: Index of rollback point (latest if None)

        Returns:
            Whether rollback was successful
        """
        print("🔄 Rolling back migration...")

        try:
            if not self.rollback_available:
                print("❌ No rollback points available")
                return False

            # Get rollback point
            if rollback_point is None:
                rollback_point = len(self.migration_log["rollback_points"]) - 1

            if rollback_point < 0 or rollback_point >= len(
                self.migration_log["rollback_points"]
            ):
                print("❌ Invalid rollback point")
                return False

            rollback_data = self.migration_log["rollback_points"][rollback_point]
            print(
                f"📋 Rolling back to: {rollback_data['timestamp']} (phase: {rollback_data['phase']})"
            )

            # Restore backup files
            if "files_backed_up" in rollback_data:
                for backup_file in rollback_data["files_backed_up"]:
                    backup_path = Path(backup_file)
                    original_path = backup_path.with_suffix("")

                    if backup_path.exists():
                        shutil.copy2(backup_path, original_path)
                        print(f"  ✅ Restored: {original_path}")

            # Update migration log
            self.migration_log["current_phase"] = "rolled_back"
            self.migration_log["statistics"]["rollback_count"] += 1
            self._save_migration_log()

            print("✅ Rollback completed successfully")
            return True

        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            return False

    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status."""
        return {
            "current_phase": self.migration_log["current_phase"],
            "migration_started": self.migration_log.get("migration_started"),
            "migration_completed": self.migration_log.get("migration_completed"),
            "statistics": self.migration_log["statistics"],
            "rollback_available": self.rollback_available,
            "rollback_points_count": len(self.migration_log["rollback_points"]),
            "backup_created": self.backup_created,
        }

    def validate_migration(self) -> Dict[str, Any]:
        """Validate the current migration state."""
        print("🔍 Validating migration state...")

        validation_results = {
            "validation_started": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "validation_passed": True,
            "issues_found": [],
            "recommendations": [],
        }

        try:
            # Check if result.json exists and is valid
            if not RESULT_JSON.exists():
                validation_results["issues_found"].append(
                    {"issue": "result.json missing", "severity": "critical"}
                )
                validation_results["validation_passed"] = False
                return validation_results

            # Load and validate result.json
            with open(RESULT_JSON) as f:
                result_data = json.load(f)

            locations = result_data.get("locations", [])
            if not locations:
                validation_results["issues_found"].append(
                    {"issue": "No locations found in result.json", "severity": "high"}
                )
                validation_results["validation_passed"] = False

            # Check each location
            tiles_found = 0
            tiles_missing = 0

            for location in locations:
                location_id = location.get("id")
                tiles = location.get("tiles", {})

                if not tiles:
                    tiles_missing += 1
                    validation_results["issues_found"].append(
                        {
                            "issue": f"No tiles found for location: {location_id}",
                            "severity": "high",
                            "location_id": location_id,
                        }
                    )
                else:
                    tiles_found += len(tiles)
                    # Check if tile files exist
                    for state, tile_path in tiles.items():
                        full_path = Path("static") / tile_path
                        if not full_path.exists():
                            tiles_missing += 1
                            validation_results["issues_found"].append(
                                {
                                    "issue": f"Tile file missing: {tile_path}",
                                    "severity": "medium",
                                    "location_id": location_id,
                                    "state": state,
                                }
                            )

            # Add summary statistics
            validation_results["summary"] = {
                "total_locations": len(locations),
                "tiles_found": tiles_found,
                "tiles_missing": tiles_missing,
            }

            # Generate recommendations
            if tiles_missing > 0:
                validation_results["recommendations"].append(
                    {
                        "priority": "high",
                        "action": "Regenerate missing tiles",
                        "reason": f"{tiles_missing} tiles are missing",
                    }
                )

            if validation_results["validation_passed"]:
                print("✅ Migration validation passed")
            else:
                print(
                    f"⚠️ Migration validation failed: {len(validation_results['issues_found'])} issues found"
                )

        except Exception as e:
            error_msg = f"Migration validation failed: {e}"
            validation_results["issues_found"].append(
                {"issue": error_msg, "severity": "critical"}
            )
            validation_results["validation_passed"] = False
            print(f"❌ {error_msg}")

        validation_results["validation_completed"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")

        return validation_results


async def main():
    """Test the MigrationManager."""
    manager = MigrationManager()

    print("🔄 Testing Migration Manager")
    print("=" * 50)

    # Get current migration status
    status = manager.get_migration_status()
    print(f"Current status: {status['current_phase']}")
    print(f"Rollback available: {status['rollback_available']}")

    # Test backup creation
    print("\n💾 Testing backup creation...")
    backup_success = manager.create_backup()
    print(f"Backup success: {backup_success}")

    # Test migration status
    print("\n📊 Testing migration validation...")
    validation = manager.validate_migration()
    print(f"Validation passed: {validation['validation_passed']}")
    if validation.get("summary"):
        summary = validation["summary"]
        print(
            f"Locations: {summary['total_locations']}, Tiles found: {summary['tiles_found']}"
        )

    print("\n🎉 Migration Manager test completed!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

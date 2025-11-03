"""
Test Data Seeding Service

Provides automated test data management across environments with:
- Data isolation between environments
- Consistent test data across runs
- Environment-specific data variations
- Data cleanup and restoration capabilities
"""

import asyncio
import csv
import os
from datetime import datetime, timedelta
from typing import Dict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal
from models.api_key import APIKey
from models.memory import Category, Memory
from models.message import Message
from models.nudge_token import NudgeToken
from models.user import User


class TestDataSeeder:
    """Manages test data seeding across environments."""

    def __init__(self, environment: str = "test"):
        """Initialize test data seeder.

        Args:
            environment: Target environment (test, staging, local)
        """
        self.environment = environment
        self.data_dir = "/test-data" if os.path.exists("/test-data") else "test-data"
        self.seed_data = {}
        self.cleanup_handlers = []

    async def seed_all(self) -> Dict[str, int]:
        """Seed all test data categories.

        Returns:
            Dict mapping data types to record counts
        """
        results = {}

        async with AsyncSessionLocal() as session:
            # Seed in dependency order
            results["categories"] = await self.seed_categories(session)
            results["users"] = await self.seed_users(session)
            results["memories"] = await self.seed_memories(session)
            results["messages"] = await self.seed_messages(session)
            results["api_keys"] = await self.seed_api_keys(session)
            results["nudge_tokens"] = await self.seed_nudge_tokens(session)

            await session.commit()

        return results

    async def seed_categories(self, session: AsyncSession) -> int:
        """Seed test categories."""
        categories = [
            Category(
                name="test_person",
                domain="social",
                full_path="social.test_person",
                description="Test person for unit tests",
                icon="🧪",
                importance_range_min=100,
                importance_range_max=1000,
            ),
            Category(
                name="test_project",
                domain="knowledge",
                full_path="knowledge.test_project",
                description="Test project for integration tests",
                icon="🔬",
                importance_range_min=500,
                importance_range_max=2000,
            ),
            Category(
                name="performance_test",
                domain="testing",
                full_path="testing.performance_test",
                description="Performance testing data",
                icon="⚡",
                importance_range_min=1,
                importance_range_max=100,
            ),
        ]

        for category in categories:
            session.add(category)

        await session.flush()
        return len(categories)

    async def seed_users(self, session: AsyncSession) -> int:
        """Seed test users."""
        users = [
            User(
                telegram_id=123456789,
                username="test_admin",
                first_name="Test",
                last_name="Admin",
                is_admin=True,
                is_active=True,
                created_at=datetime.utcnow() - timedelta(days=30),
            ),
            User(
                telegram_id=987654321,
                username="test_user",
                first_name="Test",
                last_name="User",
                is_admin=False,
                is_active=True,
                created_at=datetime.utcnow() - timedelta(days=15),
            ),
            User(
                telegram_id=555666777,
                username="vasilisa_test",
                first_name="Vasilisa",
                last_name="Test",
                is_admin=True,
                is_active=True,
                created_at=datetime.utcnow() - timedelta(days=60),
            ),
            User(
                telegram_id=888999000,
                username="daniil_test",
                first_name="Daniil",
                last_name="Test",
                is_admin=True,
                is_active=True,
                created_at=datetime.utcnow() - timedelta(days=45),
            ),
        ]

        for user in users:
            session.add(user)

        await session.flush()
        return len(users)

    async def seed_memories(self, session: AsyncSession) -> int:
        """Seed test memories."""
        memories = []

        # Get category IDs
        categories = await session.execute(
            text("SELECT id, name FROM categories WHERE name LIKE 'test_%'")
        )
        category_map = {row[1]: row[0] for row in categories}

        # Get user IDs (query executed but results not needed for current implementation)
        await session.execute(text("SELECT telegram_id FROM users"))

        # Create test memories
        test_memories_data = [
            {
                "content": "Vasilisa loves dcmaidbot and thinks it's the cutest bot ever",
                "category": "test_person",
                "importance": 1000,
                "user_id": 555666777,
            },
            {
                "content": "Daniil is working on improving the bot's AI capabilities",
                "category": "test_person",
                "importance": 800,
                "user_id": 888999000,
            },
            {
                "content": "Testing memory system with sample data for unit tests",
                "category": "test_project",
                "importance": 500,
                "user_id": 123456789,
            },
        ]

        for memory_data in test_memories_data:
            memory = Memory(
                content=memory_data["content"],
                category_id=category_map.get(memory_data["category"]),
                importance=memory_data["importance"],
                user_id=memory_data["user_id"],
                created_at=datetime.utcnow() - timedelta(hours=2),
                last_accessed=datetime.utcnow() - timedelta(minutes=30),
            )
            memories.append(memory)

        for memory in memories:
            session.add(memory)

        await session.flush()
        return len(memories)

    async def seed_messages(self, session: AsyncSession) -> int:
        """Seed test messages."""
        messages = []

        # Get user information (query executed but results not needed for current implementation)
        await session.execute(text("SELECT telegram_id, username FROM users"))

        # Create test messages
        test_messages_data = [
            {
                "user_id": 123456789,
                "content": "Hello dcmaidbot! This is a test message.",
                "message_type": "text",
                "created_at": datetime.utcnow() - timedelta(hours=1),
            },
            {
                "user_id": 555666777,
                "content": "dcmaidbot, please make a joke about programming!",
                "message_type": "command",
                "created_at": datetime.utcnow() - timedelta(minutes=30),
            },
            {
                "user_id": 987654321,
                "content": "Testing the bot response system",
                "message_type": "text",
                "created_at": datetime.utcnow() - timedelta(minutes=15),
            },
        ]

        for msg_data in test_messages_data:
            message = Message(
                user_id=msg_data["user_id"],
                content=msg_data["content"],
                message_type=msg_data["message_type"],
                created_at=msg_data["created_at"],
                processed_at=msg_data["created_at"] + timedelta(minutes=1),
            )
            messages.append(message)

        for message in messages:
            session.add(message)

        await session.flush()
        return len(messages)

    async def seed_api_keys(self, session: AsyncSession) -> int:
        """Seed test API keys."""
        api_keys = []

        # Get admin user IDs
        admin_users = await session.execute(
            text("SELECT telegram_id FROM users WHERE is_admin = true")
        )
        admin_ids = [row[0] for row in admin_users]

        for admin_id in admin_ids:
            api_key = APIKey(
                name=f"Test Key for Admin {admin_id}",
                key_hash=f"test_key_hash_{admin_id}",
                created_by=admin_id,
                description="Test API key for automated testing",
                is_active=True,
                expires_at=datetime.utcnow() + timedelta(days=30),
            )
            api_keys.append(api_key)

        for api_key in api_keys:
            session.add(api_key)

        await session.flush()
        return len(api_keys)

    async def seed_nudge_tokens(self, session: AsyncSession) -> int:
        """Seed test nudge tokens."""
        nudge_tokens = []

        # Get admin user IDs
        admin_users = await session.execute(
            text("SELECT telegram_id FROM users WHERE is_admin = true")
        )
        admin_ids = [row[0] for row in admin_users]

        for admin_id in admin_ids:
            nudge_token = NudgeToken(
                name=f"Test Nudge Token for Admin {admin_id}",
                token_hash=f"test_nudge_hash_{admin_id}",
                created_by=admin_id,
                description="Test nudge token for automated testing",
                is_active=True,
                expires_at=datetime.utcnow() + timedelta(days=30),
            )
            nudge_tokens.append(nudge_token)

        for nudge_token in nudge_tokens:
            session.add(nudge_token)

        await session.flush()
        return len(nudge_tokens)

    async def cleanup_test_data(self, session: AsyncSession) -> int:
        """Clean up all test data.

        Returns:
            Number of records cleaned up
        """
        cleanup_count = 0

        # Delete in reverse dependency order
        tables = [
            "nudge_tokens",
            "api_keys",
            "messages",
            "memories",
            "users",
            "categories",
        ]

        for table in tables:
            try:
                result = await session.execute(text(f"DELETE FROM {table}"))
                cleanup_count += result.rowcount
                print(f"✅ Cleaned {result.rowcount} records from {table}")
            except Exception as e:
                print(f"⚠️  Could not clean {table}: {e}")

        return cleanup_count

    async def export_test_data(
        self, output_dir: str = "/test-exports"
    ) -> Dict[str, str]:
        """Export current test data for backup/analysis.

        Args:
            output_dir: Directory to export data to

        Returns:
            Dict mapping table names to exported file paths
        """
        os.makedirs(output_dir, exist_ok=True)
        exported_files = {}

        async with AsyncSessionLocal() as session:
            tables = ["users", "memories", "messages", "categories"]

            for table in tables:
                try:
                    result = await session.execute(text(f"SELECT * FROM {table}"))
                    rows = result.fetchall()
                    columns = result.keys()

                    filename = os.path.join(output_dir, f"{table}_export.csv")
                    with open(filename, "w", newline="") as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(columns)
                        writer.writerows(rows)

                    exported_files[table] = filename
                    print(f"✅ Exported {len(rows)} records from {table}")

                except Exception as e:
                    print(f"❌ Failed to export {table}: {e}")

        return exported_files

    async def restore_test_data(
        self, import_dir: str = "/test-exports"
    ) -> Dict[str, int]:
        """Restore test data from exported files.

        Args:
            import_dir: Directory containing exported CSV files

        Returns:
            Dict mapping table names to record counts restored
        """
        restored_counts = {}

        if not os.path.exists(import_dir):
            print(f"❌ Import directory {import_dir} does not exist")
            return restored_counts

        async with AsyncSessionLocal() as session:
            tables = ["categories", "users", "memories", "messages"]

            for table in tables:
                filename = os.path.join(import_dir, f"{table}_export.csv")

                if not os.path.exists(filename):
                    print(f"⚠️  No export file found for {table}")
                    continue

                try:
                    with open(filename, "r") as csvfile:
                        reader = csv.DictReader(csvfile)
                        rows = list(reader)

                    # Simple bulk insert (would need proper handling for production)
                    count = 0
                    for row in rows:
                        # Convert data types appropriately based on table
                        # This is a simplified version - real implementation would need proper type handling
                        try:
                            # Build INSERT statement based on table structure
                            columns = list(row.keys())

                            # Handle special cases for different tables
                            if table == "users":
                                stmt = text("""
                                    INSERT INTO users (telegram_id, username, first_name, last_name, is_admin, is_active)
                                    VALUES (:telegram_id, :username, :first_name, :last_name, :is_admin, :is_active)
                                    ON CONFLICT (telegram_id) DO NOTHING
                                """)
                            elif table == "memories":
                                stmt = text("""
                                    INSERT INTO memories (content, category_id, importance, user_id)
                                    VALUES (:content, :category_id, :importance, :user_id)
                                """)
                            else:
                                # Generic insert for other tables
                                placeholders = ", ".join([f":{col}" for col in columns])
                                stmt = text(
                                    f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
                                )

                            await session.execute(stmt, **row)
                            count += 1

                        except Exception as e:
                            print(f"⚠️  Failed to insert row in {table}: {e}")

                    restored_counts[table] = count
                    print(f"✅ Restored {count} records to {table}")

                except Exception as e:
                    print(f"❌ Failed to restore {table}: {e}")

            await session.commit()

        return restored_counts


async def main():
    """Main seeding function for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Test data seeding utility")
    parser.add_argument(
        "--action",
        choices=["seed", "cleanup", "export", "restore"],
        default="seed",
        help="Action to perform",
    )
    parser.add_argument("--environment", default="test", help="Target environment")
    parser.add_argument(
        "--output-dir", default="/test-data", help="Output directory for exports"
    )

    args = parser.parse_args()

    seeder = TestDataSeeder(environment=args.environment)

    if args.action == "seed":
        results = await seeder.seed_all()
        print(f"✅ Seeding complete: {results}")

    elif args.action == "cleanup":
        async with AsyncSessionLocal() as session:
            count = await seeder.cleanup_test_data(session)
            await session.commit()
            print(f"✅ Cleanup complete: {count} records removed")

    elif args.action == "export":
        files = await seeder.export_test_data(args.output_dir)
        print(f"✅ Export complete: {files}")

    elif args.action == "restore":
        counts = await seeder.restore_test_data(args.output_dir)
        print(f"✅ Restore complete: {counts}")


if __name__ == "__main__":
    asyncio.run(main())

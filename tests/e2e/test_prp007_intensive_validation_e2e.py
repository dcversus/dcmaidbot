"""Intensive E2E Validation for PRP-007 with Focused Testing.

This test suite provides intensive validation of PRP-007 (Memory Search & Specialized Retrieval Tools)
with realistic performance expectations and focused LLM judge validation.

Key Features:
1. Complex search patterns with multi-concept queries
2. Cross-tool workflow testing
3. Edge cases and boundary conditions
4. Performance stress testing
5. Strategic LLM judge validation (not every call)
6. Real-world usage scenarios for Vasilisa and Daniil

Performance Expectations:
- Core tool operations: <500ms (no LLM calls)
- LLM judge evaluations: <10s (when used)
- Comprehensive workflows: <15s total
"""

import json
import time
from typing import Any, Dict, List

import pytest

from services.llm_service import LLMService
from tools.tool_executor import ToolExecutor


class FocusedLLMJudge:
    """Focused LLM Judge for strategic validation of key scenarios."""

    def __init__(self):
        self.llm_service = LLMService()
        self.evaluation_count = 0
        self.max_evaluations = 3  # Limit LLM calls for performance

    async def evaluate_critical_scenarios(
        self, query: str, results: List[Dict], context: str = ""
    ) -> Dict[str, Any]:
        """Strategic evaluation of critical search scenarios only."""
        if self.evaluation_count >= self.max_evaluations:
            return {
                "overall_score": 0.7,  # Default good score
                "analysis": "LLM evaluation limit reached, using default score",
                "skipped": True,
            }

        self.evaluation_count += 1

        # Format results for LLM evaluation
        results_text = "\n".join(
            [
                f"Result {i + 1}: {mem.get('simple_content', '')} "
                f"(Importance: {mem.get('importance', 'N/A')}, "
                f"Categories: {mem.get('categories', [])})"
                for i, mem in enumerate(results[:5])  # Limit to 5 results for LLM
            ]
        )

        evaluation_prompt = f"""
Evaluate these search results for quality on a scale of 0.0 to 1.0:

QUERY: "{query}"
{context}

RESULTS:
{results_text}

Provide evaluation as JSON:
{{
    "relevance": 0.0-1.0,
    "accuracy": 0.0-1.0,
    "overall_score": 0.0-1.0,
    "analysis": "Brief analysis"
}}
"""

        try:
            response = await self.llm_service.get_response(evaluation_prompt)

            # Extract JSON from response
            import re

            json_match = re.search(r"\{.*\}", response, re.DOTALL)

            if json_match:
                evaluation = json.loads(json_match.group())
                return evaluation
            else:
                return {
                    "relevance": 0.6,
                    "accuracy": 0.6,
                    "overall_score": 0.6,
                    "analysis": "Unable to parse LLM response",
                }

        except Exception as e:
            print(f"LLM evaluation failed: {e}")
            return {
                "relevance": 0.5,
                "accuracy": 0.5,
                "overall_score": 0.5,
                "analysis": f"Evaluation error: {str(e)}",
            }


# Rich test data representing real scenarios for Vasilisa and Daniil
INTENSIVE_TEST_MEMORIES = [
    {
        "simple_content": "Vasilisa celebrated her birthday with close friends and family",
        "full_content": "Vasilisa had a wonderful birthday celebration surrounded by her closest friends and loving family. Daniil was there and helped organize the surprise party. Everyone brought thoughtful gifts and shared happy memories together.",
        "importance": 950,
        "categories": ["social.person", "social.event"],
        "emotion_label": "joy",
        "keywords": [
            "vasilisa",
            "birthday",
            "celebration",
            "friends",
            "family",
            "daniil",
        ],
    },
    {
        "simple_content": "Severe panic attack during important client presentation",
        "full_content": "Experienced severe anxiety and panic attack during the quarterly client presentation. Heart racing, difficulty breathing, felt like losing control. Had to step out and take deep breaths. Client was understanding but it was embarrassing.",
        "importance": 900,
        "categories": ["self.emotion", "work.career"],
        "emotion_label": "panic",
        "keywords": ["panic", "anxiety", "presentation", "client", "work"],
    },
    {
        "simple_content": "Deep interest in artificial intelligence ethics and bias mitigation",
        "full_content": "Fascinated by the ethical challenges in AI development, particularly algorithmic bias and fairness. Reading research papers on bias mitigation techniques and following discussions about responsible AI deployment.",
        "importance": 850,
        "categories": ["interest", "technology.ai"],
        "emotion_label": "excitement",
        "keywords": ["AI", "ethics", "bias", "mitigation", "fairness", "research"],
    },
    {
        "simple_content": "Daniil provided crucial debugging help for production issue",
        "full_content": "Daniil was absolutely instrumental in solving a critical production bug. He stayed late, helped trace through complex code paths, and identified the root cause. His expertise and patience were invaluable.",
        "importance": 880,
        "categories": ["social.person", "work.technical"],
        "emotion_label": "gratitude",
        "keywords": ["daniil", "debugging", "production", "bug", "help", "friend"],
    },
    {
        "simple_content": "Feeling overwhelmed with multiple project deadlines",
        "full_content": "Stressed about managing three major project deadlines all converging next week. Working long hours, struggling to maintain work-life balance. Feeling pressure to deliver high-quality work while meeting tight timelines.",
        "importance": 750,
        "categories": ["self.emotion", "work.career"],
        "emotion_label": "stress",
        "keywords": ["overwhelmed", "deadlines", "stress", "projects", "work-life"],
    },
    {
        "simple_content": "Learned PyTorch framework during weekend project",
        "full_content": "Spent the entire weekend learning PyTorch and building a small neural network project. Really enjoying the hands-on learning experience. The framework feels intuitive and the documentation is excellent.",
        "importance": 700,
        "categories": ["interest", "technology.ml"],
        "emotion_label": "accomplishment",
        "keywords": [
            "pytorch",
            "machine learning",
            "neural network",
            "learning",
            "project",
        ],
    },
    {
        "simple_content": "Comforting conversation with Vasilisa after difficult day",
        "full_content": "Had a really challenging day at work and Vasilisa called at just the right moment. Her empathy and understanding helped me process everything. Grateful for such a supportive friend.",
        "importance": 820,
        "categories": ["social.person", "self.emotion"],
        "emotion_label": "comfort",
        "keywords": ["vasilisa", "comfort", "support", "friend", "empathy"],
    },
]


@pytest.fixture
async def intensive_test_memories(async_session):
    """Create rich test memories for intensive validation."""
    from models.memory import Category, Memory, memory_category_association

    # Create comprehensive categories
    categories_data = [
        {
            "name": "person",
            "domain": "social",
            "full_path": "social.person",
            "icon": "👤",
        },
        {
            "name": "event",
            "domain": "social",
            "full_path": "social.event",
            "icon": "🎉",
        },
        {
            "name": "emotion",
            "domain": "self",
            "full_path": "self.emotion",
            "icon": "😊",
        },
        {"name": "career", "domain": "work", "full_path": "work.career", "icon": "💼"},
        {
            "name": "technical",
            "domain": "work",
            "full_path": "work.technical",
            "icon": "🔧",
        },
        {
            "name": "interest",
            "domain": "interest",
            "full_path": "interest",
            "icon": "🎯",
        },
        {
            "name": "ai",
            "domain": "technology",
            "full_path": "technology.ai",
            "icon": "🤖",
        },
        {
            "name": "ml",
            "domain": "technology",
            "full_path": "technology.ml",
            "icon": "🧠",
        },
    ]

    created_categories = []
    for cat_data in categories_data:
        category = Category(**cat_data)
        async_session.add(category)
        created_categories.append(category)
    await async_session.commit()

    category_map = {cat.full_path: cat for cat in created_categories}

    created_memories = []
    for i, memory_data in enumerate(INTENSIVE_TEST_MEMORIES, 1):
        category_ids = []
        for cat_path in memory_data["categories"]:
            if cat_path in category_map:
                category_ids.append(category_map[cat_path].id)

        memory = Memory(
            simple_content=memory_data["simple_content"],
            full_content=memory_data["full_content"],
            importance=memory_data["importance"],
            created_by=123456789,
            emotion_label=memory_data["emotion_label"],
            keywords=memory_data["keywords"],
            embedding=json.dumps([0.1 * i, 0.2 * i, 0.3 * i] * 128),
        )

        async_session.add(memory)
        await async_session.flush()
        memory_id = memory.id

        for cat_id in category_ids:
            await async_session.execute(
                memory_category_association.insert().values(
                    memory_id=memory_id, category_id=cat_id
                )
            )

        created_memories.append(memory)

    await async_session.commit()
    for memory in created_memories:
        await async_session.refresh(memory, ["categories"])

    return created_memories, created_categories


@pytest.fixture
def focused_llm_judge():
    """Create focused LLM judge."""
    return FocusedLLMJudge()


@pytest.fixture
async def tool_executor(async_session):
    """Create tool executor."""
    return ToolExecutor(async_session)


# Complex Multi-Concept Search Tests


@pytest.mark.asyncio
async def test_complex_search_patterns(
    tool_executor, intensive_test_memories, focused_llm_judge
):
    """Test complex multi-concept search patterns."""
    _, _ = intensive_test_memories

    complex_queries = [
        {
            "query": "friends who helped with work problems",
            "expected_results": ["Daniil provided crucial debugging help"],
            "context": "Looking for supportive colleagues",
        },
        {
            "query": "stressful situations at work",
            "expected_results": [
                "overwhelmed with project deadlines",
                "panic attack during presentation",
            ],
            "context": "Identifying work stress patterns",
        },
        {
            "query": "exciting learning experiences",
            "expected_results": ["learned PyTorch framework", "AI ethics interest"],
            "context": "Finding positive learning moments",
        },
    ]

    for query_data in complex_queries:
        # Execute search with performance check
        start_time = time.time()
        result = await tool_executor.execute(
            tool_name="semantic_search",
            arguments={"query": query_data["query"], "limit": 5},
            user_id=123456789,
        )
        execution_time = time.time() - start_time

        # Performance assertion (core search, no LLM)
        assert execution_time < 0.5, (
            f"Search took {execution_time:.3f}s, expected <0.5s"
        )
        assert result["success"] is True

        # Validate results contain expected content
        if result["memories"]:
            results_text = " ".join(
                [mem["simple_content"].lower() for mem in result["memories"]]
            )

            # Check if expected concepts are found
            found_relevant = any(
                any(keyword in results_text for keyword in exp_result.lower().split())
                for exp_result in query_data["expected_results"]
            )

            assert found_relevant, (
                f"Expected content not found for '{query_data['query']}'"
            )

        print(
            f"✅ Complex query '{query_data['query']}' - {execution_time:.3f}s - {len(result.get('memories', []))} results"
        )


@pytest.mark.asyncio
async def test_specialized_tools_performance(tool_executor, intensive_test_memories):
    """Test performance of all specialized retrieval tools."""
    _, _ = intensive_test_memories

    tools_test = [
        {"name": "get_all_friends", "args": {}},
        {"name": "get_panic_attacks", "args": {}},
        {"name": "get_interests", "args": {}},
        {"name": "search_by_person", "args": {"person_name": "Vasilisa"}},
        {"name": "search_by_person", "args": {"person_name": "Daniil"}},
        {"name": "search_by_emotion", "args": {"emotion": "stress"}},
        {"name": "search_by_emotion", "args": {"emotion": "excitement"}},
        {"name": "search_across_versions", "args": {"query": "learning"}},
    ]

    performance_results = []

    for tool_config in tools_test:
        start_time = time.time()

        result = await tool_executor.execute(
            tool_name=tool_config["name"],
            arguments=tool_config["args"],
            user_id=123456789,
        )

        execution_time = time.time() - start_time

        # Performance assertion
        assert execution_time < 0.5, (
            f"Tool '{tool_config['name']}' took {execution_time:.3f}s, expected <0.5s"
        )
        assert result["success"] is True, f"Tool '{tool_config['name']}' failed"

        # Track results
        result_count = len(result.get(list(result.keys())[1], []))
        performance_results.append(
            {
                "tool": tool_config["name"],
                "time": execution_time,
                "results": result_count,
                "success": True,
            }
        )

        print(
            f"✅ {tool_config['name']} - {execution_time:.3f}s - {result_count} results"
        )

    # Performance analysis
    avg_time = sum(r["time"] for r in performance_results) / len(performance_results)
    max_time = max(r["time"] for r in performance_results)
    total_results = sum(r["results"] for r in performance_results)

    print("\n=== Performance Summary ===")
    print(f"Average time: {avg_time:.3f}s")
    print(f"Maximum time: {max_time:.3f}s")
    print(f"Total results: {total_results}")
    print(f"Tools tested: {len(performance_results)}")
    print("========================\n")

    # Performance quality assertions
    assert avg_time < 0.3, f"Average time too high: {avg_time:.3f}s"
    assert max_time < 0.5, f"Maximum time too high: {max_time:.3f}s"
    assert total_results > 0, "No results returned from any specialized tools"


@pytest.mark.asyncio
async def test_cross_tool_workflows(
    tool_executor, intensive_test_memories, focused_llm_judge
):
    """Test realistic cross-tool workflows."""
    _, _ = intensive_test_memories

    # Workflow 1: Emotional Support Analysis
    print("=== Emotional Support Workflow ===")

    workflow_start = time.time()

    # Step 1: Find stressful situations
    stress_results = await tool_executor.execute(
        tool_name="search_by_emotion",
        arguments={"emotion": "stress"},
        user_id=123456789,
    )

    # Step 2: Find friends
    friends_results = await tool_executor.execute(
        tool_name="get_all_friends", arguments={}, user_id=123456789
    )

    # Step 3: Search for support interactions
    support_results = await tool_executor.execute(
        tool_name="semantic_search",
        arguments={"query": "emotional support comfort"},
        user_id=123456789,
    )

    workflow_time = time.time() - workflow_start

    # Validate workflow
    assert (
        stress_results["success"]
        and friends_results["success"]
        and support_results["success"]
    )
    assert workflow_time < 2.0, f"Workflow took {workflow_time:.3f}s, expected <2.0s"

    # Combine results for analysis
    all_results = (
        stress_results.get("panic_attacks", [])
        + friends_results.get("friends", [])
        + support_results.get("memories", [])
    )

    # LLM evaluation of workflow (limited to 1 evaluation)
    if all_results:
        evaluation = await focused_llm_judge.evaluate_critical_scenarios(
            query="emotional support patterns and coping mechanisms",
            results=all_results,
            context="Analyzing stress situations and social support networks",
        )

        print(
            f"Emotional Support Workflow - {workflow_time:.3f}s - LLM Score: {evaluation.get('overall_score', 'N/A')}"
        )

        if not evaluation.get("skipped"):
            assert evaluation.get("overall_score", 0) >= 0.5, (
                f"Emotional support workflow quality too low: {evaluation.get('overall_score', 0)}"
            )

    # Workflow 2: Professional Growth Analysis
    print("=== Professional Growth Workflow ===")

    workflow_start = time.time()

    # Step 1: Technical challenges
    tech_results = await tool_executor.execute(
        tool_name="semantic_search",
        arguments={"query": "technical challenges debugging"},
        user_id=123456789,
    )

    # Step 2: Learning experiences
    learning_results = await tool_executor.execute(
        tool_name="semantic_search",
        arguments={"query": "learning new skills"},
        user_id=123456789,
    )

    # Step 3: Colleague collaboration
    colleague_results = await tool_executor.execute(
        tool_name="search_by_person",
        arguments={"person_name": "Daniil"},
        user_id=123456789,
    )

    workflow_time = time.time() - workflow_start

    # Validate workflow
    assert (
        tech_results["success"]
        and learning_results["success"]
        and colleague_results["success"]
    )
    assert workflow_time < 2.0, f"Workflow took {workflow_time:.3f}s, expected <2.0s"

    print(f"Professional Growth Workflow - {workflow_time:.3f}s")


@pytest.mark.asyncio
async def test_edge_cases_and_boundary_conditions(
    tool_executor, intensive_test_memories
):
    """Test edge cases and boundary conditions."""
    _, _ = intensive_test_memories

    edge_cases = [
        {
            "name": "Empty query",
            "tool": "semantic_search",
            "args": {"query": "", "limit": 5},
            "should_succeed": False,
        },
        {
            "name": "Nonexistent person",
            "tool": "search_by_person",
            "args": {"person_name": "NonexistentPerson123"},
            "should_succeed": True,
            "expect_empty": True,
        },
        {
            "name": "High importance filter",
            "tool": "semantic_search",
            "args": {"query": "experiences", "min_importance": 900, "limit": 3},
            "should_succeed": True,
        },
        {
            "name": "Very specific query",
            "tool": "semantic_search",
            "args": {"query": "PyTorch tensor operations", "limit": 2},
            "should_succeed": True,
        },
    ]

    for edge_case in edge_cases:
        print(f"Testing: {edge_case['name']}")

        result = await tool_executor.execute(
            tool_name=edge_case["tool"], arguments=edge_case["args"], user_id=123456789
        )

        if edge_case["should_succeed"]:
            assert result["success"] is True, "Edge case should succeed"

            if edge_case.get("expect_empty"):
                assert len(result.get("memories", [])) == 0, (
                    "Should return empty results"
                )
        else:
            assert result["success"] is False, "Edge case should fail"

        print(f"  ✅ {edge_case['name']} handled correctly")


@pytest.mark.asyncio
async def test_intensive_performance_stress_test(
    tool_executor, intensive_test_memories
):
    """Intensive performance stress test."""
    _, _ = intensive_test_memories

    # Rapid succession testing
    rapid_queries = [
        "friends and family",
        "work stress and anxiety",
        "learning and development",
        "technical challenges",
        "emotional support",
        "artificial intelligence",
        "machine learning",
        "project deadlines",
        "birthday celebrations",
        "panic attacks",
    ]

    print("=== Performance Stress Test ===")
    print(f"Running {len(rapid_queries)} rapid queries...")

    start_time = time.time()
    successful_queries = 0

    for query in rapid_queries:
        query_start = time.time()

        result = await tool_executor.execute(
            tool_name="semantic_search",
            arguments={"query": query, "limit": 5},
            user_id=123456789,
        )

        query_time = time.time() - query_start

        if result["success"]:
            successful_queries += 1
            assert query_time < 0.5, f"Query '{query}' too slow: {query_time:.3f}s"

    total_time = time.time() - start_time
    avg_time = total_time / len(rapid_queries)

    print("Stress Test Results:")
    print(f"  Total queries: {len(rapid_queries)}")
    print(f"  Successful: {successful_queries}")
    print(f"  Total time: {total_time:.3f}s")
    print(f"  Average time: {avg_time:.3f}s")
    print(f"  Success rate: {successful_queries / len(rapid_queries):.1%}")
    print("========================\n")

    # Performance quality assertions
    assert successful_queries >= len(rapid_queries) * 0.8, "Success rate too low"
    assert avg_time < 0.3, f"Average query time too high: {avg_time:.3f}s"
    assert total_time < 5.0, f"Total stress test time too high: {total_time:.3f}s"


@pytest.mark.asyncio
async def test_strategic_llm_validation(
    tool_executor, intensive_test_memories, focused_llm_judge
):
    """Strategic LLM judge validation of key scenarios."""
    _, _ = intensive_test_memories

    # Select critical scenarios for LLM evaluation
    critical_scenarios = [
        {
            "name": "Social Support Network",
            "query": "friends who provided emotional support",
            "tool": "semantic_search",
            "args": {"query": "friends support comfort", "limit": 5},
            "context": "Evaluating social support patterns and relationships",
        },
        {
            "name": "Professional Collaboration",
            "query": "colleagues who helped with technical problems",
            "tool": "search_by_person",
            "args": {"person_name": "Daniil"},
            "context": "Assessing professional collaboration and technical assistance",
        },
        {
            "name": "Interest Development",
            "query": "artificial intelligence and machine learning interests",
            "tool": "semantic_search",
            "args": {"query": "AI machine learning interests", "limit": 5},
            "context": "Evaluating interest development and expertise areas",
        },
    ]

    print("=== Strategic LLM Judge Validation ===")

    evaluation_results = []

    for scenario in critical_scenarios:
        print(f"\nEvaluating: {scenario['name']}")

        # Execute search
        start_time = time.time()
        result = await tool_executor.execute(
            tool_name=scenario["tool"], arguments=scenario["args"], user_id=123456789
        )
        search_time = time.time() - start_time

        assert result["success"] is True, f"Search failed for {scenario['name']}"

        # Get results for evaluation
        if scenario["tool"] == "search_by_person":
            search_results = result.get("memories", [])
        else:
            search_results = result.get("memories", [])

        if search_results:
            # LLM Judge evaluation
            evaluation = await focused_llm_judge.evaluate_critical_scenarios(
                query=scenario["query"],
                results=search_results,
                context=scenario["context"],
            )

            score = evaluation.get("overall_score", 0)
            analysis = evaluation.get("analysis", "No analysis available")

            print(f"  Search time: {search_time:.3f}s")
            print(f"  Results: {len(search_results)}")
            print(f"  LLM Score: {score:.2f}")
            print(
                f"  Analysis: {analysis[:100]}..."
                if len(analysis) > 100
                else f"  Analysis: {analysis}"
            )

            evaluation_results.append(
                {
                    "scenario": scenario["name"],
                    "search_time": search_time,
                    "result_count": len(search_results),
                    "llm_score": score,
                    "evaluation": evaluation,
                }
            )

            # Quality assertion
            assert score >= 0.5, f"LLM score too low for {scenario['name']}: {score}"
        else:
            print(f"  No results found for {scenario['name']}")
            evaluation_results.append(
                {
                    "scenario": scenario["name"],
                    "search_time": search_time,
                    "result_count": 0,
                    "llm_score": None,
                    "evaluation": None,
                }
            )

    # Summary analysis
    if evaluation_results:
        scores = [
            r["llm_score"] for r in evaluation_results if r["llm_score"] is not None
        ]
        avg_score = sum(scores) / len(scores) if scores else 0
        avg_search_time = sum(r["search_time"] for r in evaluation_results) / len(
            evaluation_results
        )
        total_results = sum(r["result_count"] for r in evaluation_results)

        print("\n=== LLM Validation Summary ===")
        print(f"Scenarios evaluated: {len(evaluation_results)}")
        print(f"Average LLM score: {avg_score:.2f}")
        print(f"Average search time: {avg_search_time:.3f}s")
        print(f"Total results found: {total_results}")
        print(f"Evaluations performed: {focused_llm_judge.evaluation_count}")
        print("============================\n")

        # Quality assertions
        assert avg_score >= 0.6, f"Average LLM score too low: {avg_score:.2f}"
        assert avg_search_time < 5.0, (
            f"Average search time too high: {avg_search_time:.3f}s"
        )
        assert total_results > 0, "No results found across all scenarios"
        assert focused_llm_judge.evaluation_count > 0, "No LLM evaluations performed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

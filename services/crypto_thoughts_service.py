"""
Real Cryptocurrency Analysis Service with Crypto Therapist LLM Integration

This service provides real cryptocurrency market analysis using CoinGecko and Cointelegraph APIs,
processes the data through a crypto therapist LLM with kawaii personality, and generates
twice-daily crypto thoughts for enhanced status system integration.
"""

import json
import logging
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession

from services.redis_service import RedisService
from services.status_service import StatusService

logger = logging.getLogger(__name__)


@dataclass
class CryptoMarketData:
    """Cryptocurrency market data from CoinGecko API."""

    id: str
    symbol: str
    name: str
    current_price: float
    market_cap: int
    market_cap_rank: int
    total_volume: int
    high_24h: float
    low_24h: float
    price_change_24h: float
    price_change_percentage_24h: float
    market_cap_change_24h: float
    market_cap_change_percentage_24h: float
    circulating_supply: float
    total_supply: Optional[float]
    max_supply: Optional[float]
    last_updated: str


@dataclass
class CryptoNewsItem:
    """Cryptocurrency news item from Cointelegraph RSS."""

    title: str
    pub_date: str
    link: str
    description: str
    categories: List[str]


@dataclass
class CryptoThought:
    """Generated crypto thought with therapist analysis."""

    timestamp: str
    market_analysis: str
    irrational_behavior: str
    uncomfortable_truth: str
    market_data_summary: Dict[str, Any]
    news_summary: List[str]
    confidence_score: float
    therapeutic_tone: str
    processing_time_seconds: float
    tokens_used: int


class CryptoThoughtsService:
    """Real cryptocurrency analysis and crypto therapist service."""

    def __init__(
        self,
        session: AsyncSession,
        redis_service: RedisService,
        status_service: StatusService,
    ):
        """Initialize crypto thoughts service.

        Args:
            session: Database session
            redis_service: Redis service for caching
            status_service: Status service for integration
        """
        self.session = session
        self.redis = redis_service
        self.status = status_service

        # API endpoints
        self.coingecko_api_url = "https://api.coingecko.com/api/v3"
        self.cointelegraph_rss_url = "https://cointelegraph.com/rss"

        # Configuration
        self.cache_ttl = 3600  # 1 hour
        self.thoughts_cache_key = "crypto:thoughts:latest"
        self.market_data_cache_key = "crypto:market:latest"
        self.news_cache_key = "crypto:news:latest"

        # Crypto therapist prompts
        self.crypto_therapist_prompt = """You're mama a tired crypto therapist. And she always telling news you something about crypto. Lets read all abra-cadabra letters about that bethomens-criptoins in their metawersis or what the name? oh {market_data_and_news}

NOOOOW after we read all that, lets write 3 paragraphs:
1) Explain as child to parent or another big дядься и тетя what's ACTUALLY happening in the numbers (ignore headlines)
2) What irrational behavior this is triggering
3) One uncomfortable truth about why retail loses money.

Be childlish but shy and educational, like mama explaining complicated money stuff to her confused kiddo. Use simple words, be gentle but wise. Add some cute expressions like "oh honey" or "sweetie" but keep it educational."""

    async def generate_crypto_thoughts(
        self, force_refresh: bool = False
    ) -> CryptoThought:
        """Generate complete crypto thoughts with therapist analysis.

        Args:
            force_refresh: Force fresh analysis instead of using cache

        Returns:
            CryptoThought: Complete therapist analysis
        """
        start_time = time.time()

        # Check cache first
        if not force_refresh:
            cached_thought = await self._get_cached_thought()
            if cached_thought:
                logger.info("Using cached crypto thoughts")
                return cached_thought

        logger.info("Generating fresh crypto thoughts...")

        try:
            # Collect data from APIs
            market_data = await self._fetch_market_data()
            news_data = await self._fetch_crypto_news()

            # Generate therapist analysis
            therapist_analysis = await self._generate_therapist_analysis(
                market_data, news_data
            )

            # Create crypto thought
            crypto_thought = CryptoThought(
                timestamp=datetime.now(timezone.utc).isoformat(),
                market_analysis=therapist_analysis.get("market_analysis", ""),
                irrational_behavior=therapist_analysis.get("irrational_behavior", ""),
                uncomfortable_truth=therapist_analysis.get("uncomfortable_truth", ""),
                market_data_summary=self._summarize_market_data(market_data),
                news_summary=[news.title for news in news_data[:5]],
                confidence_score=therapist_analysis.get("confidence_score", 0.8),
                therapeutic_tone="kawaii_mama_therapist",
                processing_time_seconds=time.time() - start_time,
                tokens_used=therapist_analysis.get("tokens_used", 0),
            )

            # Cache the result
            await self._cache_crypto_thought(crypto_thought)

            # Update status for integration
            await self._update_crypto_status(crypto_thought)

            logger.info(
                f"Generated crypto thoughts in {crypto_thought.processing_time_seconds:.2f}s"
            )
            return crypto_thought

        except Exception as e:
            logger.error(f"Failed to generate crypto thoughts: {e}")
            # Return fallback thought
            return await self._generate_fallback_thought(start_time)

    async def _fetch_market_data(
        self, force_refresh: bool = False
    ) -> List[CryptoMarketData]:
        """Fetch cryptocurrency market data from CoinGecko API.

        Returns:
            List[CryptoMarketData]: Market data for top cryptocurrencies
        """
        try:
            # Check cache first
            cached_data = await self.redis.get(self.market_data_cache_key)
            if cached_data and not force_refresh:
                market_data = json.loads(cached_data)
                return [CryptoMarketData(**item) for item in market_data]

            # Fetch from CoinGecko API
            url = f"{self.coingecko_api_url}/coins/markets"
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": "100",
                "page": "1",
                "sparkline": "false",
                "price_change_percentage": "24h",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()

            # Convert to data objects
            market_data = []
            for item in data:
                market_data.append(
                    CryptoMarketData(
                        id=item["id"],
                        symbol=item["symbol"],
                        name=item["name"],
                        current_price=item["current_price"],
                        market_cap=item["market_cap"],
                        market_cap_rank=item["market_cap_rank"],
                        total_volume=item["total_volume"],
                        high_24h=item["high_24h"],
                        low_24h=item["low_24h"],
                        price_change_24h=item.get("price_change_24h", 0.0),
                        price_change_percentage_24h=item.get(
                            "price_change_percentage_24h", 0.0
                        ),
                        market_cap_change_24h=item.get("market_cap_change_24h", 0.0),
                        market_cap_change_percentage_24h=item.get(
                            "market_cap_change_percentage_24h", 0.0
                        ),
                        circulating_supply=item["circulating_supply"],
                        total_supply=item.get("total_supply"),
                        max_supply=item.get("max_supply"),
                        last_updated=item.get(
                            "last_updated", datetime.now(timezone.utc).isoformat()
                        ),
                    )
                )

            # Cache for 30 minutes
            await self.redis.setex(
                self.market_data_cache_key,
                1800,
                json.dumps([asdict(item) for item in market_data]),
            )

            logger.info(f"Fetched market data for {len(market_data)} cryptocurrencies")
            return market_data

        except Exception as e:
            logger.error(f"Failed to fetch market data: {e}")
            return []

    async def _fetch_crypto_news(
        self, force_refresh: bool = False
    ) -> List[CryptoNewsItem]:
        """Fetch cryptocurrency news from Cointelegraph RSS.

        Returns:
            List[CryptoNewsItem]: Latest crypto news items
        """
        try:
            # Check cache first
            cached_news = await self.redis.get(self.news_cache_key)
            if cached_news and not force_refresh:
                news_data = json.loads(cached_news)
                return [CryptoNewsItem(**item) for item in news_data]

            # Fetch RSS feed
            async with aiohttp.ClientSession() as session:
                async with session.get(self.cointelegraph_rss_url) as response:
                    response.raise_for_status()
                    rss_content = await response.text()

            # Parse XML
            root = ET.fromstring(rss_content)
            news_items = []

            # Parse RSS content

            for item in root.findall(".//item")[:10]:  # Get latest 10 items
                title = item.find("title").text
                pub_date = item.find("pubDate").text
                link = item.find("link").text
                description = item.find("description").text

                # Extract categories
                categories = []
                for category in item.findall("category"):
                    if category.text:
                        categories.append(category.text)

                news_items.append(
                    CryptoNewsItem(
                        title=title,
                        pub_date=pub_date,
                        link=link,
                        description=description,
                        categories=categories,
                    )
                )

            # Cache for 1 hour
            await self.redis.setex(
                self.news_cache_key,
                3600,
                json.dumps([asdict(item) for item in news_items]),
            )

            logger.info(f"Fetched {len(news_items)} crypto news items")
            return news_items

        except Exception as e:
            logger.error(f"Failed to fetch crypto news: {e}")
            return []

    async def _generate_therapist_analysis(
        self, market_data: List[CryptoMarketData], news_data: List[CryptoNewsItem]
    ) -> Dict[str, Any]:
        """Generate crypto therapist analysis using LLM.

        Args:
            market_data: Cryptocurrency market data
            news_data: Cryptocurrency news items

        Returns:
            Dict: Therapist analysis results
        """
        try:
            # Prepare data for LLM
            market_summary = self._prepare_market_summary(market_data)
            news_summary = self._prepare_news_summary(news_data)

            # Create prompt
            prompt_data = f"""
MARKET DATA:
{market_summary}

LATEST NEWS:
{news_summary}
"""

            formatted_prompt = self.crypto_therapist_prompt.format(
                market_data_and_news=prompt_data
            )

            # Try to get OpenAI API key from environment
            import os

            api_key = os.getenv("OPENAI_API_KEY")

            if not api_key:
                logger.warning("OpenAI API key not found, using fallback analysis")
                return await self._generate_fallback_analysis(market_data, news_data)

            # Call OpenAI API
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }

                data = {
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a kawaii crypto therapist mama explaining complex crypto markets to your child. Be gentle, educational, and use cute expressions while providing real insights.",
                        },
                        {"role": "user", "content": formatted_prompt},
                    ],
                    "max_tokens": 800,
                    "temperature": 0.7,
                }

                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30.0,
                ) as response:
                    if response.status != 200:
                        logger.error(f"OpenAI API error: {response.status}")
                        return await self._generate_fallback_analysis(
                            market_data, news_data
                        )

                    result = await response.json()

                    content = result["choices"][0]["message"]["content"]
                    tokens_used = result["usage"]["total_tokens"]

                    # Parse the 3 paragraphs
                    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

                    return {
                        "market_analysis": paragraphs[0]
                        if len(paragraphs) > 0
                        else "Market is doing its usual crypto dance, sweetie.",
                        "irrational_behavior": paragraphs[1]
                        if len(paragraphs) > 1
                        else "People are being emotional about numbers again, honey.",
                        "uncomfortable_truth": paragraphs[2]
                        if len(paragraphs) > 2
                        else "Remember kiddo, easy money rarely exists.",
                        "confidence_score": 0.85,
                        "tokens_used": tokens_used,
                    }

        except Exception as e:
            logger.error(f"Failed to generate therapist analysis: {e}")
            return await self._generate_fallback_analysis(market_data, news_data)

    async def _generate_fallback_analysis(
        self, market_data: List[CryptoMarketData], news_data: List[CryptoNewsItem]
    ) -> Dict[str, Any]:
        """Generate fallback analysis when LLM is not available.

        Args:
            market_data: Market data (may be empty)
            news_data: News data (may be empty)

        Returns:
            Dict: Fallback analysis
        """
        # Simple analysis based on available data
        if market_data:
            top_gainer = max(
                market_data, key=lambda x: x.price_change_percentage_24h or 0
            )
            top_loser = min(
                market_data, key=lambda x: x.price_change_percentage_24h or 0
            )

            market_analysis = f"Oh honey, Bitcoin is at ${market_data[0].current_price:,.0f} and {top_gainer.name} is having a party with {top_gainer.price_change_percentage_24h:+.1f}% today! But {top_loser.name} is feeling sad with {top_loser.price_change_percentage_24h:+.1f}% poor baby."
        else:
            market_analysis = "Sweetie, the crypto market data is hiding right now, but it's probably doing its usual roller coaster thing!"

        irrational_behavior = "Oh my sweet child, everyone's either yelling 'to the moon!' or 'it's crashing!' - same as every day. People get so excited about numbers going up and down, it's like watching kids on a swing!"

        uncomfortable_truth = "Listen honey, most people lose money because they buy when everyone's excited and sell when they're scared. It's like wanting to join the game when it's almost over, sweetie."

        return {
            "market_analysis": market_analysis,
            "irrational_behavior": irrational_behavior,
            "uncomfortable_truth": uncomfortable_truth,
            "confidence_score": 0.6,
            "tokens_used": 0,
        }

    def _prepare_market_summary(self, market_data: List[CryptoMarketData]) -> str:
        """Prepare market data summary for LLM.

        Args:
            market_data: Market data list

        Returns:
            str: Formatted market summary
        """
        if not market_data:
            return "No market data available"

        summary = "TOP 10 CRYPTOCURRENCIES:\n"

        for i, crypto in enumerate(market_data[:10], 1):
            change_emoji = (
                "📈" if (crypto.price_change_percentage_24h or 0) > 0 else "📉"
            )
            summary += f"{i}. {crypto.name}: ${crypto.current_price:,.2f} ({crypto.price_change_percentage_24h:+.2f}%) {change_emoji}\n"

        # Add market statistics
        total_market_cap = sum(c.market_cap for c in market_data[:20])
        total_volume = sum(c.total_volume for c in market_data[:20])
        avg_change = (
            sum(c.price_change_percentage_24h or 0 for c in market_data[:20]) / 20
        )

        summary += "\nMARKET STATS:\n"
        summary += f"Total Market Cap (Top 20): ${total_market_cap:,.0f}\n"
        summary += f"Total Volume (Top 20): ${total_volume:,.0f}\n"
        summary += f"Average 24h Change: {avg_change:+.2f}%\n"

        return summary

    def _prepare_news_summary(self, news_data: List[CryptoNewsItem]) -> str:
        """Prepare news summary for LLM.

        Args:
            news_data: News items list

        Returns:
            str: Formatted news summary
        """
        if not news_data:
            return "No news data available"

        summary = "LATEST CRYPTO NEWS:\n"

        for i, news in enumerate(news_data[:5], 1):
            summary += f"{i}. {news.title}\n"

        return summary

    def _summarize_market_data(
        self, market_data: List[CryptoMarketData]
    ) -> Dict[str, Any]:
        """Create summary of market data for storage.

        Args:
            market_data: Market data list

        Returns:
            Dict: Market data summary
        """
        if not market_data:
            return {"error": "No market data available"}

        return {
            "total_cryptocurrencies": len(market_data),
            "bitcoin_price": market_data[0].current_price if market_data else 0,
            "top_5": [
                {
                    "name": crypto.name,
                    "price": crypto.current_price,
                    "change_24h": crypto.price_change_percentage_24h,
                }
                for crypto in market_data[:5]
            ],
            "total_market_cap_top_20": sum(c.market_cap for c in market_data[:20]),
            "average_change_24h": sum(
                c.price_change_percentage_24h or 0 for c in market_data[:20]
            )
            / 20,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _cache_crypto_thought(self, crypto_thought: CryptoThought) -> None:
        """Cache crypto thought in Redis.

        Args:
            crypto_thought: The crypto thought to cache
        """
        try:
            thought_data = asdict(crypto_thought)
            await self.redis.setex(
                self.thoughts_cache_key, self.cache_ttl, json.dumps(thought_data)
            )
        except Exception as e:
            logger.error(f"Failed to cache crypto thought: {e}")

    async def _update_crypto_status(self, crypto_thought: CryptoThought) -> None:
        """Update crypto status for status service integration.

        Args:
            crypto_thought: The crypto thought to create status from
        """
        try:
            crypto_status = {
                "timestamp": crypto_thought.timestamp,
                "status": "operational",
                "market_analysis_available": bool(crypto_thought.market_analysis),
                "processing_time_seconds": crypto_thought.processing_time_seconds,
                "tokens_used": crypto_thought.tokens_used,
                "confidence_score": crypto_thought.confidence_score,
                "therapeutic_tone": crypto_thought.therapeutic_tone,
                "news_items_count": len(crypto_thought.news_summary),
                "bitcoin_price": crypto_thought.market_data_summary.get(
                    "bitcoin_price", 0
                ),
                "last_run": crypto_thought.timestamp,
                "market_analysis_preview": crypto_thought.market_analysis[:100] + "..."
                if len(crypto_thought.market_analysis) > 100
                else crypto_thought.market_analysis,
            }

            await self.redis.setex(
                "crypto:status:latest", self.cache_ttl, json.dumps(crypto_status)
            )
        except Exception as e:
            logger.error(f"Failed to update crypto status: {e}")

    async def _get_cached_thought(self) -> Optional[CryptoThought]:
        """Get cached crypto thought.

        Returns:
            Optional[CryptoThought]: Cached thought if available
        """
        try:
            cached_data = await self.redis.get(self.thoughts_cache_key)
            if cached_data:
                thought_data = json.loads(cached_data)
                return CryptoThought(**thought_data)
        except Exception as e:
            logger.error(f"Failed to get cached thought: {e}")

        return None

    async def _generate_fallback_thought(self, start_time: float) -> CryptoThought:
        """Generate fallback crypto thought when APIs fail.

        Args:
            start_time: Process start time

        Returns:
            CryptoThought: Fallback thought
        """
        return CryptoThought(
            timestamp=datetime.now(timezone.utc).isoformat(),
            market_analysis="Oh honey, the crypto market is sleeping right now, but that's okay! Even markets need naps, sweetie.",
            irrational_behavior="People are probably still making emotional decisions about numbers they don't understand, bless their hearts.",
            uncomfortable_truth="Remember sweetie, if someone promises guaranteed returns in crypto, they're either lying or misunderstood how math works.",
            market_data_summary={"error": "APIs unavailable"},
            news_summary=["No news available"],
            confidence_score=0.3,
            therapeutic_tone="fallback_mama_therapist",
            processing_time_seconds=time.time() - start_time,
            tokens_used=0,
        )

    async def get_crypto_thoughts_status(self) -> Dict[str, Any]:
        """Get current status of crypto thoughts system.

        Returns:
            Dict: System status information
        """
        try:
            # Get latest thought
            latest_thought = await self._get_cached_thought()

            # Get cached market data status
            market_data_cached = await self.redis.exists(self.market_data_cache_key)
            news_data_cached = await self.redis.exists(self.news_cache_key)

            return {
                "system_status": "operational",
                "latest_thought_available": latest_thought is not None,
                "last_thought_timestamp": latest_thought.timestamp
                if latest_thought
                else None,
                "market_data_cached": bool(market_data_cached),
                "news_data_cached": bool(news_data_cached),
                "processing_time_seconds": latest_thought.processing_time_seconds
                if latest_thought
                else None,
                "tokens_used": latest_thought.tokens_used if latest_thought else 0,
                "confidence_score": latest_thought.confidence_score
                if latest_thought
                else 0.0,
                "therapeutic_tone": latest_thought.therapeutic_tone
                if latest_thought
                else "none",
            }

        except Exception as e:
            logger.error(f"Failed to get crypto thoughts status: {e}")
            return {"system_status": "error", "error": str(e)}

    async def run_crypto_thoughts_cron(self) -> None:
        """Run crypto thoughts generation as scheduled cron job."""
        logger.info("Running crypto thoughts cron job...")

        try:
            # Generate fresh thoughts
            crypto_thought = await self.generate_crypto_thoughts(force_refresh=True)

            # Log results
            logger.info(
                f"Crypto thoughts cron completed in {crypto_thought.processing_time_seconds:.2f}s, "
                f"confidence: {crypto_thought.confidence_score:.2f}, "
                f"tokens: {crypto_thought.tokens_used}"
            )

            # Store cron execution metadata
            cron_metadata = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "thoughts_generated": 1,
                "processing_time_seconds": crypto_thought.processing_time_seconds,
                "tokens_used": crypto_thought.tokens_used,
                "confidence_score": crypto_thought.confidence_score,
                "market_data_available": bool(
                    crypto_thought.market_data_summary.get("bitcoin_price")
                ),
                "news_items_count": len(crypto_thought.news_summary),
            }

            await self.redis.setex(
                "crypto:cron:last_run",
                43200,  # 12 hours (twice daily schedule)
                json.dumps(cron_metadata),
            )

        except Exception as e:
            logger.error(f"Crypto thoughts cron job failed: {e}")

            # Store failure metadata
            failure_metadata = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "failed",
                "error": str(e),
            }

            await self.redis.setex(
                "crypto:cron:last_run", 43200, json.dumps(failure_metadata)
            )

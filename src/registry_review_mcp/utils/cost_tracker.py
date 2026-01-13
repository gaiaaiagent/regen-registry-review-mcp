"""Cost tracking for LLM API usage.

Tracks API calls, tokens, and estimated costs for monitoring and optimization.
"""

import fcntl
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Pricing (as of November 2025)
# Source: https://docs.claude.com/en/docs/about-claude/pricing
# Note: Cache pricing uses 5-minute tier (1.25x input for writes, 0.1x input for reads)
# For 1-hour cache writes, multiply input by 2x instead of 1.25x
PRICING = {
    # Claude Sonnet 4.5 (Latest, released September 2025)
    "claude-sonnet-4-5-20250929": {
        "input": 3.00 / 1_000_000,         # $3 per MTok
        "output": 15.00 / 1_000_000,       # $15 per MTok
        "cache_write": 3.75 / 1_000_000,   # $3.75 per MTok (5-min cache)
        "cache_read": 0.30 / 1_000_000,    # $0.30 per MTok (10% of input)
    },
    # Claude Sonnet 4 (Previous generation)
    "claude-sonnet-4-20250514": {
        "input": 3.00 / 1_000_000,
        "output": 15.00 / 1_000_000,
        "cache_write": 3.75 / 1_000_000,
        "cache_read": 0.30 / 1_000_000,
    },
    # Claude Haiku 4.5 (Latest, released October 2025)
    "claude-haiku-4-5-20251015": {
        "input": 1.00 / 1_000_000,         # $1 per MTok
        "output": 5.00 / 1_000_000,        # $5 per MTok
        "cache_write": 1.25 / 1_000_000,   # $1.25 per MTok (5-min cache)
        "cache_read": 0.10 / 1_000_000,    # $0.10 per MTok (10% of input)
    },
    # Claude Haiku 3.5 (Legacy)
    "claude-haiku-3-5-20241022": {
        "input": 0.80 / 1_000_000,         # $0.80 per MTok
        "output": 4.00 / 1_000_000,        # $4 per MTok
        "cache_write": 1.00 / 1_000_000,   # $1 per MTok (5-min cache)
        "cache_read": 0.08 / 1_000_000,    # $0.08 per MTok (10% of input)
    },
}


class APICall(BaseModel):
    """Record of a single API call."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model: str
    extractor: str  # "date", "tenure", "project_id"
    document_name: str
    input_tokens: int
    output_tokens: int
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    cost_usd: float
    duration_seconds: float
    cached: bool = False


class SessionCostSummary(BaseModel):
    """Cost summary for a session."""

    session_id: str
    total_api_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_cache_creation_tokens: int
    total_cache_read_tokens: int
    total_cost_usd: float
    total_duration_seconds: float
    cache_hit_rate: float
    api_calls: list[APICall] = Field(default_factory=list)


class CostTracker:
    """Track API costs for LLM extraction."""

    def __init__(self, session_id: str, storage_path: Path | None = None):
        """Initialize cost tracker.

        Args:
            session_id: Session identifier
            storage_path: Optional path to store cost data (defaults to session directory)
        """
        self.session_id = session_id
        self.storage_path = storage_path or Path(f"data/sessions/{session_id}/cost_tracking.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        self.api_calls: list[APICall] = []
        self._load_existing()

    def _load_existing(self) -> None:
        """Load existing cost data if available."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path) as f:
                    # Acquire shared lock for reading (multiple readers allowed)
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                    try:
                        data = json.load(f)
                        summary = SessionCostSummary(**data)
                        self.api_calls = summary.api_calls
                        logger.info(f"Loaded {len(self.api_calls)} existing API calls from cost tracker")
                    finally:
                        # Release lock
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except Exception as e:
                logger.warning(f"Failed to load existing cost data: {e}")

    def track_api_call(
        self,
        model: str,
        extractor: str,
        document_name: str,
        input_tokens: int,
        output_tokens: int,
        duration_seconds: float,
        cached: bool = False,
        cache_creation_tokens: int = 0,
        cache_read_tokens: int = 0,
    ) -> float:
        """Track an API call and calculate cost.

        Args:
            model: Model name (e.g., "claude-sonnet-4-5-20250929")
            extractor: Extractor type ("date", "tenure", "project_id")
            document_name: Name of document being processed
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            duration_seconds: API call duration
            cached: Whether this was a cache hit
            cache_creation_tokens: Tokens written to cache
            cache_read_tokens: Tokens read from cache

        Returns:
            Cost in USD for this API call
        """
        # Get pricing for model
        if model not in PRICING:
            logger.warning(f"No pricing data for model {model}, using default Sonnet pricing")
            pricing = PRICING["claude-sonnet-4-5-20250929"]
        else:
            pricing = PRICING[model]

        # Calculate cost
        cost = 0.0
        cost += input_tokens * pricing["input"]
        cost += output_tokens * pricing["output"]
        cost += cache_creation_tokens * pricing["cache_write"]
        cost += cache_read_tokens * pricing["cache_read"]

        # Record API call
        api_call = APICall(
            model=model,
            extractor=extractor,
            document_name=document_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_creation_tokens=cache_creation_tokens,
            cache_read_tokens=cache_read_tokens,
            cost_usd=cost,
            duration_seconds=duration_seconds,
            cached=cached,
        )

        self.api_calls.append(api_call)
        self._save()

        logger.info(
            f"API call tracked: {extractor} on {document_name} - "
            f"{input_tokens}+{output_tokens} tokens, ${cost:.4f}, {duration_seconds:.2f}s"
        )

        return cost

    def get_summary(self) -> SessionCostSummary:
        """Get cost summary for the session.

        Returns:
            SessionCostSummary with aggregated metrics
        """
        if not self.api_calls:
            return SessionCostSummary(
                session_id=self.session_id,
                total_api_calls=0,
                total_input_tokens=0,
                total_output_tokens=0,
                total_cache_creation_tokens=0,
                total_cache_read_tokens=0,
                total_cost_usd=0.0,
                total_duration_seconds=0.0,
                cache_hit_rate=0.0,
            )

        total_calls = len(self.api_calls)
        cached_calls = sum(1 for call in self.api_calls if call.cached)

        return SessionCostSummary(
            session_id=self.session_id,
            total_api_calls=total_calls,
            total_input_tokens=sum(call.input_tokens for call in self.api_calls),
            total_output_tokens=sum(call.output_tokens for call in self.api_calls),
            total_cache_creation_tokens=sum(call.cache_creation_tokens for call in self.api_calls),
            total_cache_read_tokens=sum(call.cache_read_tokens for call in self.api_calls),
            total_cost_usd=sum(call.cost_usd for call in self.api_calls),
            total_duration_seconds=sum(call.duration_seconds for call in self.api_calls),
            cache_hit_rate=cached_calls / total_calls if total_calls > 0 else 0.0,
            api_calls=self.api_calls,
        )

    def _save(self) -> None:
        """Save cost data to file with exclusive lock."""
        try:
            summary = self.get_summary()
            with open(self.storage_path, "w") as f:
                # Acquire exclusive lock for writing (blocks other readers/writers)
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(summary.model_dump(mode="json"), f, indent=2, default=str)
                finally:
                    # Release lock
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            logger.error(f"Failed to save cost data: {e}")

    def print_summary(self) -> None:
        """Print formatted cost summary to console."""
        summary = self.get_summary()

        print(f"\n{'='*60}")
        print(f"COST SUMMARY - Session: {self.session_id}")
        print(f"{'='*60}")
        print(f"Total API Calls:     {summary.total_api_calls}")
        print(f"Cache Hit Rate:      {summary.cache_hit_rate:.1%}")
        print(f"\nTokens:")
        print(f"  Input:             {summary.total_input_tokens:,}")
        print(f"  Output:            {summary.total_output_tokens:,}")
        print(f"  Cache Creation:    {summary.total_cache_creation_tokens:,}")
        print(f"  Cache Read:        {summary.total_cache_read_tokens:,}")
        print(f"\nCost:")
        print(f"  Total:             ${summary.total_cost_usd:.4f}")
        print(f"  Per Call:          ${summary.total_cost_usd/summary.total_api_calls if summary.total_api_calls > 0 else 0:.4f}")
        print(f"\nDuration:")
        print(f"  Total:             {summary.total_duration_seconds:.2f}s")
        print(f"  Average:           {summary.total_duration_seconds/summary.total_api_calls if summary.total_api_calls > 0 else 0:.2f}s")
        print(f"{'='*60}\n")

        # Breakdown by extractor
        if summary.api_calls:
            print(f"Breakdown by Extractor:")
            extractors = {}
            for call in summary.api_calls:
                if call.extractor not in extractors:
                    extractors[call.extractor] = {"calls": 0, "cost": 0.0, "tokens": 0}
                extractors[call.extractor]["calls"] += 1
                extractors[call.extractor]["cost"] += call.cost_usd
                extractors[call.extractor]["tokens"] += call.input_tokens + call.output_tokens

            for extractor, stats in extractors.items():
                print(f"  {extractor:15s}: {stats['calls']:2d} calls, ${stats['cost']:.4f}, {stats['tokens']:,} tokens")
            print(f"{'='*60}\n")

"""
The Router - Core routing logic for BlackRoad Operator.

This is the brain that decides which provider handles each request.
The agent doesn't need to be smart. It needs to know WHO TO CALL.
"""

import re
from typing import Optional
from enum import Enum

from .models.requests import IntentType
from .providers.base import registry, BaseProvider


class RouteStrategy(str, Enum):
    """Routing strategy options."""
    FASTEST = "fastest"  # Prefer local/edge
    CHEAPEST = "cheapest"  # Minimize cost
    BEST = "best"  # Best quality (usually Claude)
    AUTO = "auto"  # Automatic based on query


# Intent detection patterns
INTENT_PATTERNS = {
    IntentType.PHYSICS: [
        r"physic",
        r"quantum",
        r"energy",
        r"force",
        r"mass",
        r"velocity",
        r"acceleration",
        r"wavelength",
        r"frequency",
        r"relativity",
        r"electron",
        r"proton",
        r"neutron",
        r"atom",
        r"molecule",
        r"thermodynamic",
        r"electromagnetic",
        r"gravity",
        r"orbital",
        r"binding energy",
        r"kinetic",
        r"potential",
        r"lorentz",
        r"coulomb",
        r"planck",
        r"heisenberg",
        r"schrodinger",
        r"calculate.*(?:eV|joule|newton|meter|kelvin)",
    ],
    IntentType.DATA: [
        r"customer",
        r"contact",
        r"account",
        r"lead",
        r"opportunity",
        r"salesforce",
        r"crm",
        r"lookup",
        r"find.*(?:customer|contact|account)",
        r"get.*(?:customer|contact|account)",
        r"create.*(?:customer|contact|account)",
        r"update.*(?:customer|contact|account)",
        r"soql",
    ],
    IntentType.INFERENCE: [
        r"classify",
        r"detect",
        r"recognize",
        r"vision",
        r"image",
        r"video",
        r"real.?time",
        r"edge",
        r"fast.*inference",
        r"local.*model",
    ],
    IntentType.LANGUAGE: [
        r"explain",
        r"write",
        r"summarize",
        r"translate",
        r"analyze",
        r"code",
        r"help.*with",
        r"what is",
        r"how do",
        r"why",
        r"tell me",
        r"describe",
    ],
}

# Provider priority for each intent
INTENT_PROVIDER_MAP = {
    IntentType.PHYSICS: ["physics", "claude", "gpt"],
    IntentType.DATA: ["salesforce", "claude"],
    IntentType.INFERENCE: ["hailo", "claude"],
    IntentType.LANGUAGE: ["claude", "gpt"],
    IntentType.UNKNOWN: ["claude", "gpt"],
}


def detect_intent(query: str) -> IntentType:
    """
    Detect the intent of a query using pattern matching.

    Returns the most likely intent type.
    """
    query_lower = query.lower()
    intent_scores: dict[IntentType, int] = {intent: 0 for intent in IntentType}

    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                intent_scores[intent] += 1

    # Get highest scoring intent
    max_score = max(intent_scores.values())
    if max_score == 0:
        return IntentType.UNKNOWN

    for intent, score in intent_scores.items():
        if score == max_score:
            return intent

    return IntentType.UNKNOWN


def select_provider(
    intent: IntentType,
    strategy: RouteStrategy = RouteStrategy.AUTO,
    preferred: Optional[str] = None,
    require_local: bool = False,
) -> Optional[BaseProvider]:
    """
    Select the best provider for a given intent.

    Args:
        intent: The detected intent type
        strategy: Routing strategy to use
        preferred: Preferred provider name (if any)
        require_local: If True, only consider local/edge providers

    Returns:
        The selected provider, or None if no suitable provider found
    """
    # If user specified a preferred provider, try it first
    if preferred:
        provider = registry.get(preferred)
        if provider:
            return provider

    # Get provider priority list for this intent
    provider_names = INTENT_PROVIDER_MAP.get(intent, INTENT_PROVIDER_MAP[IntentType.UNKNOWN])

    # Apply strategy modifications
    if strategy == RouteStrategy.FASTEST:
        # Prioritize local/edge providers
        provider_names = sorted(
            provider_names,
            key=lambda n: 0 if registry.get(n) and registry.get(n).provider_type == "edge" else 1
        )
    elif strategy == RouteStrategy.CHEAPEST:
        # Prioritize compute (free) over API providers
        provider_names = sorted(
            provider_names,
            key=lambda n: 0 if registry.get(n) and registry.get(n).provider_type == "compute" else 1
        )

    # Filter for local only if required
    if require_local:
        provider_names = [
            n for n in provider_names
            if registry.get(n) and registry.get(n).provider_type in ("compute", "edge")
        ]

    # Return first available provider
    for name in provider_names:
        provider = registry.get(name)
        if provider:
            return provider

    return None


def get_alternative_providers(
    selected: str,
    intent: IntentType
) -> list[str]:
    """Get list of alternative providers that could handle this intent."""
    provider_names = INTENT_PROVIDER_MAP.get(intent, [])
    return [n for n in provider_names if n != selected and registry.get(n)]


class Router:
    """
    The Router class - orchestrates the routing decision.

    This is the heart of BlackRoad. It doesn't need to be smart.
    It needs to know WHO TO CALL.
    """

    def __init__(self, default_strategy: RouteStrategy = RouteStrategy.AUTO):
        self.default_strategy = default_strategy

    def route(
        self,
        query: str,
        strategy: Optional[RouteStrategy] = None,
        preferred_provider: Optional[str] = None,
        require_local: bool = False,
    ) -> tuple[BaseProvider, IntentType, list[str]]:
        """
        Route a query to the appropriate provider.

        Args:
            query: The user's query
            strategy: Routing strategy (defaults to instance default)
            preferred_provider: User's preferred provider
            require_local: Require local/edge processing

        Returns:
            Tuple of (selected_provider, detected_intent, alternative_providers)

        Raises:
            ValueError: If no suitable provider is found
        """
        # Detect intent
        intent = detect_intent(query)

        # Select provider
        strategy = strategy or self.default_strategy
        provider = select_provider(
            intent=intent,
            strategy=strategy,
            preferred=preferred_provider,
            require_local=require_local,
        )

        if not provider:
            raise ValueError(f"No provider available for intent: {intent}")

        # Get alternatives
        alternatives = get_alternative_providers(provider.name, intent)

        return provider, intent, alternatives


# Global router instance
router = Router()

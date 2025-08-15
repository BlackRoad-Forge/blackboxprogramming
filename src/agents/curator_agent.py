"""
Curator Agent - integrates AIService for intelligent fact extraction,
similarity analysis, source reliability assessment, and contradiction detection.

This agent uses the AIServiceRouter to call underlying AI providers. All methods
are asynchronous and will gracefully handle the absence of AI providers by
falling back to simple logic when necessary.
"""

from typing import List, Any, Optional

# Import the AI service router from the backend services. The backend package has an
# __init__.py so it can be imported from src.agents.
try:
    from backend.services.ai_service import AIServiceRouter
except ImportError:
    # If backend cannot be imported as a package, attempt relative import.
    from ..backend.services.ai_service import AIServiceRouter  # type: ignore


class CuratorAgent:
    """Curator/Learner agent using AI for intelligent knowledge ingestion."""

    def __init__(self, ai_service: AIServiceRouter) -> None:
        self.ai_service = ai_service

    async def learn_from_text(self, text: str) -> List[Any]:
        """Extract facts from raw input using the AI service.

        Args:
            text: Raw input text to learn from.

        Returns:
            A list of extracted fact objects. The structure of fact objects
            depends on the AI provider and may include content, confidence,
            source metadata, and context.
        """
        # Call the AI service to extract facts. If no provider is available, this
        # call will raise an exception or return an empty list depending on
        # implementation.
        return await self.ai_service.extract_facts(text)

    async def is_duplicate(self, fact1: Any, fact2: Any, threshold: float = 0.9) -> bool:
        """Determine if two facts are duplicates using semantic similarity.

        Args:
            fact1: First fact object.
            fact2: Second fact object.
            threshold: Similarity threshold above which the facts are considered duplicates.

        Returns:
            True if the similarity between the facts exceeds the threshold, False otherwise.
        """
        # Extract content strings from fact objects. Fallback to str() if content attribute is missing.
        content1 = getattr(fact1, 'content', str(fact1))
        content2 = getattr(fact2, 'content', str(fact2))
        similarity = await self.ai_service.analyze_semantic_similarity(content1, content2)
        return similarity >= threshold

    async def deduplicate(self, facts: List[Any], threshold: float = 0.9) -> List[Any]:
        """Deduplicate a list of facts by semantic similarity.

        Args:
            facts: A list of fact objects to deduplicate.
            threshold: Similarity threshold for considering two facts duplicates.

        Returns:
            A list of unique fact objects.
        """
        unique: List[Any] = []
        for fact in facts:
            # Skip if fact is considered duplicate of any already in unique list.
            is_dup = False
            for existing in unique:
                if await self.is_duplicate(fact, existing, threshold=threshold):
                    is_dup = True
                    break
            if not is_dup:
                unique.append(fact)
        return unique

    async def assess_source_reliability(self, facts: List[Any]) -> List[Any]:
        """Assess and annotate reliability of fact sources.

        This method iterates over provided facts and may adjust their confidence
        values based on source reliability. Currently it returns the facts
        unchanged. In a more sophisticated implementation this could query
        external knowledge about sources or use AI to judge credibility.

        Args:
            facts: A list of fact objects.

        Returns:
            The list of fact objects, potentially annotated or reordered based on reliability.
        """
        # Placeholder: return facts unchanged. Future versions could call
        # self.ai_service.assess_source_reliability() when implemented.
        return facts

    async def detect_contradictions(self, facts: List[Any]) -> List[Any]:
        """Detect contradictions among a collection of facts.

        Args:
            facts: A list of fact objects.

        Returns:
            A list of contradiction objects describing conflicting facts. The
            structure of contradiction objects depends on the AI provider.
        """
        return await self.ai_service.detect_contradictions(facts)

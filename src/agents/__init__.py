"""
Agent package initialization.

This module exposes all available agent classes in the ``agents`` package.
It aggregates both the original agents (curator, guardian, lucidia and
roadie) and the newly added roles such as research, testing, documentation,
devops, UX, performance, compliance and training coordinators.
"""

from .research_agent import ResearchAgent
from .testing_agent import TestingAgent
from .documentation_agent import DocumentationAgent
from .devops_agent import DevOpsAgent
from .ux_agent import UXAgent
from .performance_agent import PerformanceAgent
from .compliance_agent import ComplianceAgent
from .training_agent import TrainingAgent

# Import existing agents if they exist in the package.  Use optional imports
# to avoid failing if some agents are not yet implemented.
try:
    from .curator_agent import CuratorAgent  # type: ignore
except ImportError:
    CuratorAgent = None  # type: ignore

try:
    from .guardian_agent import GuardianAgent  # type: ignore
except ImportError:
    GuardianAgent = None  # type: ignore

try:
    from .lucidia_agent import LucidiaAgent  # type: ignore
except ImportError:
    LucidiaAgent = None  # type: ignore

try:
    from .roadie_agent import RoadieAgent  # type: ignore
except ImportError:
    RoadieAgent = None  # type: ignore

__all__ = [
    "ResearchAgent",
    "TestingAgent",
    "DocumentationAgent",
    "DevOpsAgent",
    "UXAgent",
    "PerformanceAgent",
    "ComplianceAgent",
    "TrainingAgent",
    # Existing agents
    "CuratorAgent",
    "GuardianAgent",
    "LucidiaAgent",
    "RoadieAgent",
]

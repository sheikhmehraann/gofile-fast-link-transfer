"""Base classes and data models for link resolvers."""

from dataclasses import dataclass, field
from typing import Optional, Dict
from abc import ABC, abstractmethod


@dataclass
class ResolvedURL:
    """Dataclass holding resolved direct download information."""
    original_url: str
    direct_url: str
    filename: Optional[str] = None
    file_size: Optional[int] = None
    headers: Dict[str, str] = field(default_factory=dict)
    cookies: Dict[str, str] = field(default_factory=dict)
    supports_ranges: bool = False


class BaseResolver(ABC):
    """Abstract Base Class for Link Resolvers."""

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Check if this resolver supports the given URL."""
        pass

    @abstractmethod
    def resolve(self, url: str) -> ResolvedURL:
        """Resolve the input URL into a direct downloadable stream URL."""
        pass

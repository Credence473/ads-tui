"""
Shared data models for ADS TUI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Paper:
    """Representation of one ADS search result."""

    bibcode: str

    title: str

    authors: list[str] = field(default_factory=list)

    year: int | None = None

    journal: str | None = None

    doi: str | None = None

    abstract: str | None = None

    keywords: list[str] = field(default_factory=list)

    citation_count: int = 0

    _property: list[str] = field(default_factory=list)

    esources: list[str] = field(default_factory=list)

    pdf_url: str | None = None

    ads_url: str | None = None

    bibtex: str | None = None

    arxiv_id: str | None = None

    local_pdf: Path | None = None

    @property
    def author_string(self) -> str:
        if not self.authors:
            return ""

        if len(self.authors) == 1:
            return self.authors[0]

        if len(self.authors) == 2:
            return f"{self.authors[0]} & {self.authors[1]}"

        return f"{self.authors[0]} et al."

    @property
    def display_title(self) -> str:
        if len(self.title) <= 90:
            return self.title

        return self.title[:87] + "..."

    @property
    def display_line(self) -> str:
        year = str(self.year) if self.year else "----"

        return f"{year:<4}  " f"{self.author_string:<28.28}  " f"{self.display_title}"

    @property
    def ads_link(self) -> str:
        return self.ads_url or (f"https://ui.adsabs.harvard.edu/abs/{self.bibcode}")

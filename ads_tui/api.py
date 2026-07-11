"""
Async ADS API client.
"""

from __future__ import annotations

from typing import Any

import httpx

from .models import Paper

BASE_URL = "https://api.adsabs.harvard.edu/v1"


class ADSClient:
    """Thin wrapper around the ADS REST API."""

    def __init__(
        self,
        token: str,
        *,
        timeout: float = 30.0,
    ):
        self.client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Bearer {token}",
            },
            timeout=timeout,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.close()

    # ------------------------------------------------------------
    # Search
    # ------------------------------------------------------------

    async def search(
        self,
        query: str,
        rows: int = 10,
    ) -> list[Paper]:
        """
        Search ADS.
        """

        params = {
            "q": query,
            "rows": rows,
            "fl": ",".join(
                [
                    "bibcode",
                    "title",
                    "author",
                    "year",
                    "pub",
                    "doi",
                    "abstract",
                    "keyword",
                    "citation_count",
                    "property",
                    "esources",
                    "identifier",
                ]
            ),
        }

        r = await self.client.get(
            "/search/query",
            params=params,
        )
        r.raise_for_status()

        docs = r.json()["response"]["docs"]

        return [self._paper_from_doc(doc) for doc in docs]

    # ------------------------------------------------------------
    # BibTeX export
    # ------------------------------------------------------------

    async def export_bibtex(
        self,
        bibcodes: list[str],
    ) -> str:
        """
        Export one or more papers as BibTeX.
        """

        r = await self.client.post(
            "/export/bibtex",
            json={"bibcode": bibcodes},
        )

        r.raise_for_status()

        return r.json()["export"]

    # ------------------------------------------------------------
    # Abstract lookup
    # ------------------------------------------------------------

    async def get_abstract(
        self,
        bibcode: str,
    ) -> str | None:
        """
        Fetch abstract for a single paper.
        """

        papers = await self.search(f"bibcode:{bibcode}", rows=1)

        if not papers:
            return None

        return papers[0].abstract

    # ------------------------------------------------------------
    # PDF URL discovery
    # ------------------------------------------------------------

    async def pdf_url(
        self,
        bibcode: str,
    ) -> str | None:
        """
        Try to locate a downloadable PDF.

        Preference:

            arXiv
            ADS
            publisher
        """

        papers = await self.search(
            f"bibcode:{bibcode}",
            rows=1,
        )

        if not papers:
            return None

        paper = papers[0]

        identifiers = paper.esources or []

        # arXiv
        for item in identifiers:
            if isinstance(item, str) and item.lower() == "pub_pdf":
                return (
                    "https://ui.adsabs.harvard.edu/link_gateway/" f"{bibcode}/PUB_PDF"
                )
            elif isinstance(item, str) and item.lower() == "eprint_pdf":
                return (
                    "https://ui.adsabs.harvard.edu/link_gateway/"
                    f"{bibcode}/EPRINT_PDF"
                )
            else:
                continue
        return None

    # ------------------------------------------------------------
    # Internal conversion
    # ------------------------------------------------------------

    @staticmethod
    def _paper_from_doc(doc: dict[str, Any]) -> Paper:

        title = ""

        if doc.get("title"):
            title = doc["title"][0]

        doi = None

        if doc.get("doi"):
            doi = doc["doi"][0]

        return Paper(
            bibcode=doc["bibcode"],
            title=title,
            authors=doc.get("author", []),
            year=doc.get("year"),
            journal=doc.get("pub"),
            doi=doi,
            abstract=doc.get("abstract"),
            keywords=doc.get("keyword", []),
            citation_count=doc.get("citation_count", 0),
            _property=doc.get("property", []),
            esources=doc.get("esources", []),
        )

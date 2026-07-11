"""
Actions performed on selected ADS papers.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import httpx
import pyperclip

from .api import ADSClient
from .cache import Cache
from .config import Config
from .models import Paper


class ActionError(RuntimeError):
    pass


class PaperActions:
    """
    Operations on selected papers.
    """

    def __init__(
        self,
        api: ADSClient,
        cache: Cache,
        config: Config,
    ):
        self.api = api
        self.cache = cache
        self.config = config

    # ---------------------------------------------------------
    # BibTeX
    # ---------------------------------------------------------

    async def get_bibtex(
        self,
        papers: list[Paper],
    ) -> str:

        entries = []

        for paper in papers:

            cached = self.cache.get_bibtex(paper.bibcode)

            if cached:
                entries.append(cached)
                continue

            bibtex = await self.api.export_bibtex([paper.bibcode])

            self.cache.save_bibtex(
                paper.bibcode,
                bibtex,
            )

            entries.append(bibtex)

        return "\n\n".join(entries)

    async def copy_bibtex(
        self,
        papers: list[Paper],
    ) -> None:

        bibtex = await self.get_bibtex(papers)

        pyperclip.copy(bibtex)

    async def save_bibtex(
        self,
        papers: list[Paper],
        path: Path | None = None,
    ) -> Path:

        path = path or self.config.default_bib

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        bibtex = await self.get_bibtex(papers)

        path.write_text(
            bibtex + "\n",
            encoding="utf-8",
        )

        return path

    async def append_bibtex(
        self,
        papers: list[Paper],
        path: Path | None = None,
    ) -> Path:

        path = path or self.config.default_bib

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        bibtex = await self.get_bibtex(papers)

        with path.open(
            "a",
            encoding="utf-8",
        ) as f:
            f.write("\n\n" + bibtex + "\n")

        return path

    # ---------------------------------------------------------
    # DOI
    # ---------------------------------------------------------

    def copy_doi(
        self,
        papers: list[Paper],
    ) -> None:

        dois = [p.doi for p in papers if p.doi]

        pyperclip.copy("\n".join(dois))

    # ---------------------------------------------------------
    # PDF download
    # ---------------------------------------------------------

    async def download_pdf(
        self,
        papers: list[Paper],
    ) -> list[Path]:

        destination = self.config.download_dir

        destination.mkdir(
            parents=True,
            exist_ok=True,
        )

        files = []

        for paper in papers:

            url = await self.api.pdf_url(paper.bibcode)

            if not url:
                continue

            filename = self._safe_filename(paper) + ".pdf"

            path = destination / filename

            await self._download(
                url,
                path,
            )

            paper.local_pdf = path

            files.append(path)

        return files

    async def _download(
        self,
        url: str,
        path: Path,
    ) -> None:

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=60,
        ) as client:

            response = await client.get(url)

            response.raise_for_status()

            path.write_bytes(response.content)

    # ---------------------------------------------------------
    # Open external applications
    # ---------------------------------------------------------

    def open_ads(
        self,
        paper: Paper,
    ) -> None:

        subprocess.Popen(
            [
                "xdg-open",
                paper.ads_link,
            ]
        )

    def open_pdf(
        self,
        paper: Paper,
    ) -> None:

        if not paper.local_pdf:
            raise ActionError("PDF has not been downloaded")

        subprocess.Popen(
            [
                "xdg-open",
                str(paper.local_pdf),
            ]
        )

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _safe_filename(
        paper: Paper,
    ) -> str:

        author = paper.author_string.replace("et al.", "").strip()

        year = str(paper.year) if paper.year else "unknown"

        title = paper.title

        name = f"{year}_{author}_{title}"

        name = re.sub(
            r"[^\w\-]+",
            "_",
            name,
        )

        return name[:150]

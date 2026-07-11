"""
fzf based interactive paper selector.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from .models import Paper


class FZFError(RuntimeError):
    pass


class FZFSelector:
    """
    Interface between ads-tui and fzf.
    """

    def __init__(
        self,
        *,
        height: str = "80%",
    ):
        self.height = height

    # ---------------------------------------------------------
    # Public interface
    # ---------------------------------------------------------

    def select(
        self,
        papers: list[Paper],
        *,
        multi: bool = False,
    ) -> list[Paper]:

        if not papers:
            return []

        lookup = {paper.bibcode: paper for paper in papers}

        lines = "\n".join(f"{paper.bibcode}\t{paper.display_line}" for paper in papers)

        result = self._run_fzf(
            lines,
            multi=multi,
            papers=papers,
        )

        if not result:
            return []

        selected = []

        for line in result.splitlines():

            bibcode = line.split("\t")[0]

            if bibcode in lookup:
                selected.append(lookup[bibcode])

        return selected

    # ---------------------------------------------------------
    # fzf execution
    # ---------------------------------------------------------

    def _run_fzf(
        self,
        input_text: str,
        *,
        multi: bool,
        papers: list[Paper],
    ) -> str:

        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
        ) as f:

            preview_file = Path(f.name)

            for paper in papers:
                f.write(self._preview_text(paper) + "\n")

        command = [
            "fzf",
            "--ansi",
            "--height",
            self.height,
            "--layout",
            "reverse",
            "--delimiter",
            "\t",
            "--with-nth",
            "2..",
            "--preview",
            ("grep -A100 " "'{1}' " f"{preview_file}"),
            "--preview-window",
            "right:50%",
        ]

        if multi:
            command.append("--multi")

        try:

            proc = subprocess.run(
                command,
                input=input_text,
                text=True,
                capture_output=True,
            )

        except FileNotFoundError:
            raise FZFError("fzf is not installed")

        finally:
            preview_file.unlink(missing_ok=True)

        return proc.stdout.strip()

    # ---------------------------------------------------------
    # Preview formatting
    # ---------------------------------------------------------

    @staticmethod
    def _preview_text(
        paper: Paper,
    ) -> str:

        abstract = paper.abstract or "No abstract available."

        keywords = ", ".join(paper.keywords)

        return "\n".join(
            [
                paper.bibcode,
                "",
                f"Title: {paper.title}",
                "",
                f"Authors: {paper.author_string}",
                "",
                f"Journal: {paper.journal}",
                f"Year: {paper.year}",
                "",
                f"DOI: {paper.doi}",
                "",
                f"Citations: {paper.citation_count}",
                "",
                f"Keywords: {keywords}",
                "",
                "Abstract:",
                abstract,
                "",
            ]
        )

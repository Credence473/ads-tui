"""
SQLite cache for ads-tui.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from .config import CACHE_DB
from .models import Paper


class Cache:
    def __init__(
        self,
        db_path: Path = CACHE_DB,
        *,
        max_age_days: int = 30,
    ):
        self.db_path = db_path
        self.max_age = max_age_days * 86400

        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

        self._create_tables()

    def close(self) -> None:
        self.conn.close()

    # ---------------------------------------------------------
    # Schema
    # ---------------------------------------------------------

    def _create_tables(self) -> None:
        cur = self.conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS searches (
                query TEXT PRIMARY KEY,
                results INTEGER NOT NULL,
                timestamp INTEGER NOT NULL,
                results_json TEXT NOT NULL
            )
            """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                bibcode TEXT PRIMARY KEY,
                timestamp INTEGER NOT NULL,
                paper_json TEXT NOT NULL
            )
            """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS bibtex (
                bibcode TEXT PRIMARY KEY,
                timestamp INTEGER NOT NULL,
                bibtex TEXT NOT NULL
            )
            """)

        self.conn.commit()

    # ---------------------------------------------------------
    # Expiration
    # ---------------------------------------------------------

    def _expired(self, timestamp: int) -> bool:
        return (time.time() - timestamp) > self.max_age

    def vacuum(self) -> None:
        """
        Remove expired entries.
        """

        cutoff = int(time.time() - self.max_age)

        cur = self.conn.cursor()

        cur.execute(
            "DELETE FROM searches WHERE timestamp < ?",
            (cutoff,),
        )

        cur.execute(
            "DELETE FROM papers WHERE timestamp < ?",
            (cutoff,),
        )

        cur.execute(
            "DELETE FROM bibtex WHERE timestamp < ?",
            (cutoff,),
        )

        self.conn.commit()

    # ---------------------------------------------------------
    # Search cache
    # ---------------------------------------------------------

    def get_search(
        self,
        query: str,
        results: int,
    ) -> list[Paper] | None:

        row = self.conn.execute(
            """
            SELECT timestamp, results_json
            FROM searches
            WHERE query = ?
            AND results = ?
            """,
            (query, results),
        ).fetchone()

        if row is None:
            return None

        if self._expired(row["timestamp"]):
            return None

        data = json.loads(row["results_json"])

        return [self._paper_from_dict(p) for p in data]

    def save_search(
        self,
        query: str,
        results: int,
        papers: list[Paper],
    ) -> None:

        payload = json.dumps([self._paper_to_dict(p) for p in papers])

        self.conn.execute(
            """
            INSERT OR REPLACE INTO searches
            VALUES (?, ?, ?, ?)
            """,
            (
                query,
                results,
                int(time.time()),
                payload,
            ),
        )

        self.conn.commit()

    # ---------------------------------------------------------
    # Paper cache
    # ---------------------------------------------------------

    def get_paper(
        self,
        bibcode: str,
    ) -> Paper | None:

        row = self.conn.execute(
            """
            SELECT timestamp, paper_json
            FROM papers
            WHERE bibcode = ?
            """,
            (bibcode,),
        ).fetchone()

        if row is None:
            return None

        if self._expired(row["timestamp"]):
            return None

        return self._paper_from_dict(json.loads(row["paper_json"]))

    def save_paper(
        self,
        paper: Paper,
    ) -> None:

        payload = json.dumps(self._paper_to_dict(paper))

        self.conn.execute(
            """
            INSERT OR REPLACE INTO papers
            VALUES (?, ?, ?)
            """,
            (
                paper.bibcode,
                int(time.time()),
                payload,
            ),
        )

        self.conn.commit()

    # ---------------------------------------------------------
    # BibTeX cache
    # ---------------------------------------------------------

    def get_bibtex(
        self,
        bibcode: str,
    ) -> str | None:

        row = self.conn.execute(
            """
            SELECT timestamp, bibtex
            FROM bibtex
            WHERE bibcode = ?
            """,
            (bibcode,),
        ).fetchone()

        if row is None:
            return None

        if self._expired(row["timestamp"]):
            return None

        return row["bibtex"]

    def save_bibtex(
        self,
        bibcode: str,
        bibtex: str,
    ) -> None:

        self.conn.execute(
            """
            INSERT OR REPLACE INTO bibtex
            VALUES (?, ?, ?)
            """,
            (
                bibcode,
                int(time.time()),
                bibtex,
            ),
        )

        self.conn.commit()

    # ---------------------------------------------------------
    # Serialization helpers
    # ---------------------------------------------------------

    @staticmethod
    def _paper_to_dict(
        paper: Paper,
    ) -> dict:

        return {
            "bibcode": paper.bibcode,
            "title": paper.title,
            "authors": paper.authors,
            "year": paper.year,
            "journal": paper.journal,
            "doi": paper.doi,
            "abstract": paper.abstract,
            "keywords": paper.keywords,
            "citation_count": paper.citation_count,
            "property": paper._property,
            "esources": paper.esources,
            "pdf_url": paper.pdf_url,
            "ads_url": paper.ads_url,
            "bibtex": paper.bibtex,
            "arxiv_id": paper.arxiv_id,
        }

    @staticmethod
    def _paper_from_dict(
        data: dict,
    ) -> Paper:

        return Paper(
            bibcode=data["bibcode"],
            title=data["title"],
            authors=data.get("authors", []),
            year=data.get("year"),
            journal=data.get("journal"),
            doi=data.get("doi"),
            abstract=data.get("abstract"),
            keywords=data.get("keywords", []),
            citation_count=data.get(
                "citation_count",
                0,
            ),
            _property=data.get("property", []),
            esources=data.get("esources", []),
            pdf_url=data.get("pdf_url"),
            ads_url=data.get("ads_url"),
            bibtex=data.get("bibtex"),
            arxiv_id=data.get("arxiv_id"),
        )

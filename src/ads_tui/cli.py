"""
Command line interface for ads-tui.
"""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.prompt import Prompt

from .actions import PaperActions
from .api import ADSClient
from .cache import Cache
from .config import load_config, require_token
from .fzf import FZFSelector
from .models import Paper

app = typer.Typer(
    name="ads-tui",
    help="""
    Search ADS papers from the terminal.
    The query can be a simple string or a comma-separated list of field:value pairs. For example: 'author:Smith,year:2020'.
    The following shorthands are also available for common fields:
    'a' for author,
    'fa' for first_author,
    'abs' for abstract,
    'y' for year,
    'ft' for full text, and
    'pub' for publication.
    Additionally, the keyword 'astro' can be used to filter results to the astronomy collection. Example: 'astro,author:Smith,year:2020'.
    """,
)

console = Console()


@app.command()
def search(
    query: str,
    results: int | None = typer.Option(
        None,
        "--results",
        "-n",
        help="Number of results",
    ),
    multi: bool = typer.Option(
        False,
        "--multi",
        "-m",
        help="Allow selecting multiple papers",
    ),
):
    """
    Search ADS papers from the terminal.
    The query can be a simple string or a comma-separated list of field:value pairs. For example: 'author:Smith,year:2020'.
    The following shorthands are also available for common fields:
    'a' for author,
    'fa' for first_author,
    'abs' for abstract,
    'y' for year,
    'ft' for full text, and
    'pub' for publication.
    Additionally, the keyword 'astro' can be used to filter results to the astronomy collection. Example: 'astro,author:Smith,year:2020'.
    """

    asyncio.run(
        _search(
            query,
            results,
            multi,
        )
    )


def parse_query(query: str) -> str:
    shorthands = {
        "a": "author",
        "fa": "first_author",
        "abs": "abstract",
        "y": "year",
        "ft": "full",
        "pub": "bibstem",
    }

    fields = query.split(",")
    parsed_query = ""
    for field in fields:
        if ":" in field:
            key, value = field.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key in shorthands:
                parsed_query += f"{shorthands[key]}:{value} "
            else:
                parsed_query += f"{key}:{value} "
        elif field.strip() == "astro":
            parsed_query += "collection:astronomy "
        else:
            parsed_query += f"{field} "
    return parsed_query.strip()


async def _search(
    query: str,
    results: int | None,
    multi: bool,
):

    config = load_config()

    require_token(config)

    cache = Cache(max_age_days=config.cache_days)
    _original_query = query.strip()
    query = parse_query(query)
    if query != _original_query:
        console.print(f"[bold]Parsed Query:[/bold] {query}")

    async with ADSClient(config.token) as api:

        # --------------------------------------------------
        # Search
        # --------------------------------------------------

        papers = cache.get_search(query, results or config.results)

        if papers:

            console.print("[green]Using cached results[/green]")

        else:

            console.print("[cyan]Searching ADS...[/cyan]")

            papers = await api.search(
                query,
                rows=(results or config.results),
            )

            cache.save_search(
                query,
                results or config.results,
                papers,
            )

        if not papers:

            console.print("[red]No papers found[/red]")

            return

        # --------------------------------------------------
        # Select
        # --------------------------------------------------

        selector = FZFSelector()

        selected = selector.select(
            papers,
            multi=multi,
        )

        if not selected:
            return

        # --------------------------------------------------
        # Actions
        # --------------------------------------------------

        actions = PaperActions(
            api,
            cache,
            config,
        )

        await action_menu(
            selected,
            actions,
        )

    cache.close()


async def action_menu(
    papers: list[Paper],
    actions: PaperActions,
):

    while True:

        console.print()

        console.print("[bold]Selected:[/bold]")

        for paper in papers:
            console.print(f"  {paper.display_line}")

        console.print()

        choice = Prompt.ask(
            """
Choose action:
    Multiple mode: 
    (b) BibTeX copy
    (s) Save BibTeX
    (a) Append BibTeX
    (d) Copy DOI

    Single mode: (first paper in multi-selection)
    (p) Open PDF link
    (u) Open ADS

    (q) Quit
""",
            choices=[
                "b",
                "s",
                "a",
                "p",
                "d",
                "u",
                "q",
            ],
        )

        if choice == "b":

            await actions.copy_bibtex(papers)

            console.print("[green]BibTeX copied[/green]")

        elif choice == "s":

            path = await actions.save_bibtex(papers)

            console.print(f"Saved: {path}")

        elif choice == "a":

            path = await actions.append_bibtex(papers)

            console.print(f"Appended: {path}")

        elif choice == "p":

            console.print("[yellow]Opening PDF in browser[/yellow]")

            await actions.open_pdf_link(papers[0])

        elif choice == "d":

            actions.copy_doi(papers)

            console.print("[green]DOI copied[/green]")

        elif choice == "u":

            actions.open_ads(papers[0])

        elif choice == "q":

            break


if __name__ == "__main__":
    app()

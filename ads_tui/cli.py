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
    help="Search ADS papers from the terminal.",
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
    Search ADS and perform actions.
    """

    asyncio.run(
        _search(
            query,
            results,
            multi,
        )
    )


async def _search(
    query: str,
    results: int | None,
    multi: bool,
):

    config = load_config()

    require_token(config)

    cache = Cache(max_age_days=config.cache_days)

    async with ADSClient(config.token) as api:

        # --------------------------------------------------
        # Search
        # --------------------------------------------------

        papers = cache.get_search(query)

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

    (b) BibTeX copy
    (s) Save BibTeX
    (a) Append BibTeX
    (p) Download PDF
    (d) Copy DOI
    (o) Open ADS
    (q) Quit
""",
            choices=[
                "b",
                "s",
                "a",
                "p",
                "d",
                "o",
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

            files = await actions.download_pdf(papers)

            for f in files:
                console.print(f"Downloaded: {f}")

        elif choice == "d":

            actions.copy_doi(papers)

            console.print("[green]DOI copied[/green]")

        elif choice == "o":

            actions.open_ads(papers[0])

        elif choice == "q":

            break


if __name__ == "__main__":
    app()

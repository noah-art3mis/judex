import json
from pathlib import Path
from typing import List, Optional

import typer
from rich import print

from judex.core import JudexScraper
from judex.strategies import SpiderStrategyFactory

# Create Typer app
app = typer.Typer(
    name="judex",
    help="Judex - Batedor de processos",
    add_completion=False,
)


@app.command()
def batedores():
    """Listar os batedores disponíveis"""
    strategies = SpiderStrategyFactory.list_strategies()
    print("Batedores disponíveis:")
    for strategy in strategies:
        print(f"  - {strategy}")


@app.command()
def scrape(
    classe: str = typer.Option(
        ...,
        "--classe",
        "-c",
        help="A classe do processo para raspar (ex: ADI, ADPF, ACI, etc.)",
    ),
    processo: List[int] = typer.Option(
        ...,
        "--processo",
        "-p",
        help="Os números do processo para raspar (pode especificar múltiplos)",
    ),
    salvar_como: List[str] = typer.Option(
        ...,
        "--salvar-como",
        "-s",
        help="Tipo de persistência para usar (json, csv, jsonl, sql) - pode especificar múltiplos",
    ),
    scraper_kind: str = typer.Option(
        "stf",
        "--scraper",
        help="O tipo de raspador a usar (padrão: stf)",
    ),
    output_path: Path = typer.Option(
        Path("judex_output"),
        "--output-path",
        help="O caminho para o diretório de saída (padrão: judex_output)",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Habilitar logging verboso"
    ),
    custom_name: Optional[str] = typer.Option(
        None,
        "--custom-name",
        help="Nome personalizado para arquivos de saída (padrão: classe + processo)",
    ),
    skip_existing: bool = typer.Option(
        True,
        "--skip-existing/--no-skip-existing",
        help="Se deve pular processo existentes (padrão: true)",
    ),
    retry_failed: bool = typer.Option(
        True,
        "--retry-failed/--no-retry-failed",
        help="Se deve tentar novamente processo que falharam (padrão: true)",
    ),
    max_age: int = typer.Option(
        24,
        "--max-age",
        help="Idade máxima do processo para raspar em horas (padrão: 24)",
    ),
):
    """Raspar casos jurídicos do STF"""
    try:
        # Convert process numbers to JSON string format expected by JudexScraper
        processos_json = json.dumps(processo)

        # Create and run the scraper
        scraper = JudexScraper(
            classe=classe,
            processos=processos_json,
            scraper_kind=scraper_kind,
            output_path=str(output_path),
            salvar_como=salvar_como,  # Already a list
            skip_existing=skip_existing,
            retry_failed=retry_failed,
            max_age_hours=max_age,
            db_path=None,
            custom_name=custom_name,
            verbose=verbose,
        )

        # Display startup information with rich formatting
        print(
            f"[bold green]🚀 Iniciando raspador para classe '{classe}' com processo {processo}[/bold green]"
        )
        print(f"[blue]📁 Diretório de saída: {output_path}[/blue]")
        print(f"[blue]💾 Tipo de saída: {salvar_como}[/blue]")

        scraper.scrape()

        print(f"[blue]📁 Diretório de saída: {output_path}[/blue]")
        print(f"[blue]💾 Tipo de saída: {salvar_como}[/blue]")
        print("[bold green]✅ Raspagem concluída com sucesso![/bold green]")

    except Exception as e:
        print(f"[bold red]❌ Erro: {e}[/bold red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

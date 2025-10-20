import json
import os
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
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Reduzir verbosidade (log apenas INFO)"
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
    log_level: Optional[str] = typer.Option(
        None,
        "--log-level",
        help="Scrapy LOG_LEVEL (CRITICAL|ERROR|WARNING|INFO|DEBUG)",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache/--cache",
        help="Desabilitar cache HTTP (sobrepõe configurações quando ativado)",
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
            verbose=not quiet,
        )

        # Apply CLI-controlled Scrapy settings
        if log_level:
            scraper.settings.set("LOG_LEVEL", str(log_level).upper())
        else:
            if quiet:
                scraper.settings.set("LOG_LEVEL", "INFO")
            else:
                scraper.settings.set("LOG_LEVEL", "DEBUG")

        if no_cache:
            scraper.settings.set("HTTPCACHE_ENABLED", False)

        # Display startup information with rich formatting
        print(
            f"[bold green]🚀 Iniciando raspador para classe '{classe}' com processo {processo}[/bold green]"
        )
        print(f"[blue]📁 Diretório de saída: {output_path}[/blue]")
        print(f"[blue]💾 Tipo de saída: {salvar_como}[/blue]")

        scraper.scrape()

        # Log saved file paths after scraping is complete
        _log_saved_files(output_path, classe, custom_name, processo, salvar_como)

    except Exception as e:
        print(f"[bold red]❌ Erro: {e}[/bold red]")
        raise typer.Exit(1)


def _log_saved_files(
    output_path: Path,
    classe: str,
    custom_name: Optional[str],
    processo: List[int],
    salvar_como: List[str],
) -> None:
    """Log the paths to saved files after scraping is complete"""
    from judex.output_registry import OutputFormatRegistry

    print("\n[bold green]✅ Raspagem concluída! Arquivos salvos em:[/bold green]")

    for format_name in salvar_como:
        config = OutputFormatRegistry.get_pipeline_config(
            format_name=format_name,
            output_path=str(output_path),
            classe=classe,
            custom_name=custom_name,
            process_numbers=processo,
            overwrite=True,
        )

        if config and "file_path" in config:
            file_path = config["file_path"]
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"[green]  📄 {file_path} ({file_size:,} bytes)[/green]")
            else:
                print(f"[yellow]  ⚠️  {file_path} (arquivo não encontrado)[/yellow]")
        elif format_name == "sql":
            # Special case for SQL - database file path
            db_path = os.path.join(output_path, "judex.db")
            if os.path.exists(db_path):
                file_size = os.path.getsize(db_path) / (1024 * 1024)  # Convert bytes to MB
                print(f"[green]  🗄️  {db_path} ({file_size:.2f} MB)[/green]")
            else:
                print(f"[yellow]  ⚠️  {db_path} (arquivo não encontrado)[/yellow]")


if __name__ == "__main__":
    app()

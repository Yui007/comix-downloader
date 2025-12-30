"""
Rich console display utilities for beautiful CLI output.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich import box

from ..core.models import MangaInfo, Chapter, DownloadConfig, OutputFormat

console = Console()


class Display:
    """Rich display utilities for CLI."""
    
    @staticmethod
    def show_banner():
        """Display application banner."""
        banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║       ██████╗ ██████╗ ███╗   ███╗██╗██╗  ██╗                 ║
║      ██╔════╝██╔═══██╗████╗ ████║██║╚██╗██╔╝                 ║
║      ██║     ██║   ██║██╔████╔██║██║ ╚███╔╝                  ║
║      ██║     ██║   ██║██║╚██╔╝██║██║ ██╔██╗                  ║
║      ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║██╔╝ ██╗                 ║
║       ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═╝                 ║
║                                                               ║
║          ██████╗  ██████╗ ██╗    ██╗███╗   ██╗               ║
║          ██╔══██╗██╔═══██╗██║    ██║████╗  ██║               ║
║          ██║  ██║██║   ██║██║ █╗ ██║██╔██╗ ██║               ║
║          ██║  ██║██║   ██║██║███╗██║██║╚██╗██║               ║
║          ██████╔╝╚██████╔╝╚███╔███╔╝██║ ╚████║               ║
║          ╚═════╝  ╚═════╝  ╚══╝╚══╝ ╚═╝  ╚═══╝               ║
║                                                               ║
║             🎨 Beautiful Manga Downloader CLI                 ║
╚═══════════════════════════════════════════════════════════════╝
"""
        console.print(Text(banner, style="bold cyan"))
    
    @staticmethod
    def show_manga_info(manga: MangaInfo):
        """Display manga information in a beautiful panel."""
        info_table = Table(show_header=False, box=None, padding=(0, 1))
        info_table.add_column("Field", style="cyan bold")
        info_table.add_column("Value", style="white")
        
        info_table.add_row("📚 Title", manga.title or "Unknown")
        
        if manga.alt_titles:
            alt = ", ".join(manga.alt_titles[:3])
            if len(manga.alt_titles) > 3:
                alt += f" (+{len(manga.alt_titles) - 3} more)"
            info_table.add_row("📝 Alt Titles", alt)
        
        info_table.add_row("📖 Type", (manga.manga_type or "Unknown").title())
        info_table.add_row("📊 Status", (manga.status or "Unknown").title())
        
        if manga.year:
            info_table.add_row("📅 Year", str(manga.year))
        
        if manga.latest_chapter:
            info_table.add_row("📑 Latest Chapter", str(manga.latest_chapter))
        
        if manga.rated_avg:
            stars = "⭐" * int(manga.rated_avg)
            info_table.add_row("⭐ Rating", f"{manga.rated_avg:.1f}/5 {stars}")
        
        if manga.follows_total:
            info_table.add_row("👥 Followers", f"{manga.follows_total:,}")
        
        if manga.is_nsfw:
            info_table.add_row("🔞 NSFW", "Yes")
        
        # Description (truncated)
        if manga.description:
            desc = manga.description[:300]
            if len(manga.description) > 300:
                desc += "..."
            info_table.add_row("📝 Description", desc)
        
        panel = Panel(
            info_table,
            title="[bold magenta]Manga Information[/]",
            border_style="magenta",
            box=box.ROUNDED
        )
        console.print(panel)
    
    @staticmethod
    def show_chapters_table(chapters: list[Chapter], display_limit: int = 20):
        """Display chapters in a table format.
        
        Args:
            chapters: List of chapters to display
            display_limit: Max chapters to show (0 = show all)
        """
        table = Table(
            title="📚 Available Chapters",
            box=box.ROUNDED,
            border_style="blue"
        )
        
        table.add_column("#", style="dim", width=4)
        table.add_column("Number", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Group", style="green")
        table.add_column("Pages", style="yellow", justify="right")
        
        # Apply limit (0 = show all)
        if display_limit > 0:
            display_chapters = chapters[:display_limit]
        else:
            display_chapters = chapters
        
        for idx, ch in enumerate(display_chapters, 1):
            table.add_row(
                str(idx),
                str(ch.number),
                ch.title or "-",
                ch.group_name or "-",
                str(ch.pages_count) if ch.pages_count else "-"
            )
        
        console.print(table)
        
        if display_limit > 0 and len(chapters) > display_limit:
            console.print(
                f"[dim]... and {len(chapters) - display_limit} more chapters. "
                f"Total: {len(chapters)} chapters[/]"
            )
    
    @staticmethod
    def show_settings(config: DownloadConfig):
        """Display current settings."""
        table = Table(
            title="⚙️  Current Settings",
            box=box.ROUNDED,
            border_style="yellow"
        )
        
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("📁 Output Format", config.output_format.value.upper())
        table.add_row("🖼️  Keep Images", "✅ Yes" if config.keep_images else "❌ No")
        table.add_row("📝 Enable Logs", "✅ Yes" if config.enable_logs else "❌ No")
        table.add_row("📂 Download Path", config.download_path)
        table.add_row("🔄 Max Chapter Workers", str(config.max_chapter_workers))
        table.add_row("🔄 Max Image Workers", str(config.max_image_workers))
        table.add_row("🔁 Retry Count", str(config.retry_count))
        table.add_row("⏱️  Retry Delay", f"{config.retry_delay}s")
        
        console.print(table)
    
    @staticmethod
    def show_download_summary(successful: int, failed: int, manga_title: str):
        """Display download summary."""
        total = successful + failed
        
        if failed == 0:
            style = "bold green"
            emoji = "🎉"
            message = "All chapters downloaded successfully!"
        elif successful == 0:
            style = "bold red"
            emoji = "❌"
            message = "All downloads failed!"
        else:
            style = "bold yellow"
            emoji = "⚠️"
            message = "Download completed with some failures"
        
        summary = f"""
{emoji} {message}

📚 Manga: {manga_title}
✅ Successful: {successful}/{total}
❌ Failed: {failed}/{total}
"""
        
        panel = Panel(
            summary.strip(),
            title="[bold]Download Summary[/]",
            border_style=style.replace("bold ", ""),
            box=box.ROUNDED
        )
        console.print(panel)
    
    @staticmethod
    def error(message: str):
        """Display error message."""
        console.print(f"[bold red]❌ Error:[/] {message}")
    
    @staticmethod
    def success(message: str):
        """Display success message."""
        console.print(f"[bold green]✅[/] {message}")
    
    @staticmethod
    def info(message: str):
        """Display info message."""
        console.print(f"[bold blue]ℹ️[/]  {message}")
    
    @staticmethod
    def warning(message: str):
        """Display warning message."""
        console.print(f"[bold yellow]⚠️[/]  {message}")

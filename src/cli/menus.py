"""
Interactive menu components using Rich prompts.
"""

from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich import box

from ..core.models import Chapter, DownloadConfig, OutputFormat
from ..utils.config import ConfigManager

console = Console()


class MainMenu:
    """Main application menu."""
    
    MENU_OPTIONS = {
        "1": ("📥 Download Manga by URL", "download"),
        "2": ("⚙️  Settings", "settings"),
        "3": ("🚪 Exit", "exit")
    }
    
    @classmethod
    def show(cls) -> str:
        """Show main menu and return selected action."""
        menu_text = "\n".join(
            f"  [cyan bold]{key}[/] │ {name}"
            for key, (name, _) in cls.MENU_OPTIONS.items()
        )
        
        panel = Panel(
            menu_text,
            title="[bold magenta]Main Menu[/]",
            border_style="magenta",
            box=box.ROUNDED
        )
        console.print(panel)
        
        while True:
            choice = Prompt.ask(
                "\n[bold cyan]Select an option[/]",
                choices=list(cls.MENU_OPTIONS.keys()),
                default="1"
            )
            
            if choice in cls.MENU_OPTIONS:
                return cls.MENU_OPTIONS[choice][1]
    
    @staticmethod
    def get_manga_url() -> str:
        """Prompt for manga URL."""
        return Prompt.ask(
            "\n[bold cyan]Enter manga URL[/]",
            default=""
        ).strip()


class ChapterSelector:
    """Chapter selection menu with scanlator grouping."""
    
    @staticmethod
    def select_chapters(chapters: list[Chapter]) -> list[Chapter]:
        """
        Prompt user to select chapters with scanlator preference.
        
        Supports:
        - Single: "5"
        - Range: "1-10"
        - All: "all"
        - Multiple: "1,3,5-10"
        """
        console.print("\n[bold cyan]Chapter Selection Options:[/]")
        console.print("  • Enter a single number: [dim]5[/]")
        console.print("  • Enter a range: [dim]1-10[/]")
        console.print("  • Enter multiple: [dim]1,3,5-10[/]")
        console.print("  • Download all: [dim]all[/]")
        
        while True:
            selection = Prompt.ask(
                "\n[bold cyan]Select chapters[/]",
                default="all"
            ).strip().lower()
            
            if selection == "all":
                # For "all", still need to group and ask for scanlator
                grouped = ChapterSelector._group_by_number(chapters)
                scanlators = ChapterSelector._get_all_scanlators(chapters)
                
                if len(scanlators) > 1:
                    preferred = ChapterSelector._select_scanlator(scanlators)
                    filtered = ChapterSelector._filter_by_scanlator(grouped, preferred)
                else:
                    filtered = [chs[0] for chs in grouped.values()]
                
                console.print(f"[green]Selected {len(filtered)} unique chapter(s)[/]")
                if Confirm.ask(f"[yellow]Download {len(filtered)} chapters?[/]", default=True):
                    return sorted(filtered, key=lambda c: (float(c.number) if str(c.number).replace('.','').isdigit() else 0))
                continue
            
            try:
                # Parse the selection to get chapter numbers requested
                selected_raw = ChapterSelector._parse_selection(selection, chapters)
                
                if selected_raw:
                    # Group selected chapters by number
                    grouped = ChapterSelector._group_by_number(selected_raw)
                    
                    # Get unique scanlators from selected chapters
                    scanlators = ChapterSelector._get_all_scanlators(selected_raw)
                    
                    if len(scanlators) > 1:
                        console.print(f"\n[yellow]Found {len(grouped)} unique chapters with multiple scanlator versions[/]")
                        preferred = ChapterSelector._select_scanlator(scanlators)
                        filtered = ChapterSelector._filter_by_scanlator(grouped, preferred)
                    else:
                        filtered = [chs[0] for chs in grouped.values()]
                    
                    console.print(
                        f"[green]Selected {len(filtered)} chapter(s): "
                        f"{', '.join(str(c.number) for c in filtered[:5])}"
                        f"{'...' if len(filtered) > 5 else ''}[/]"
                    )
                    if Confirm.ask("[cyan]Proceed with download?[/]", default=True):
                        return sorted(filtered, key=lambda c: (float(c.number) if str(c.number).replace('.','').isdigit() else 0))
                else:
                    console.print("[red]No valid chapters selected. Try again.[/]")
            except ValueError as e:
                console.print(f"[red]Invalid selection: {e}[/]")
    
    @staticmethod
    def _group_by_number(chapters: list[Chapter]) -> dict[str, list[Chapter]]:
        """Group chapters by their chapter number."""
        grouped: dict[str, list[Chapter]] = {}
        for ch in chapters:
            num = str(ch.number)
            if num not in grouped:
                grouped[num] = []
            grouped[num].append(ch)
        return grouped
    
    @staticmethod
    def _get_all_scanlators(chapters: list[Chapter]) -> list[str]:
        """Extract all unique scanlator names from chapters."""
        scanlators = set()
        for ch in chapters:
            if ch.group_name:
                scanlators.add(ch.group_name)
        # Sort alphabetically, add "Any (first available)" option
        return sorted(list(scanlators))
    
    @staticmethod
    def _select_scanlator(scanlators: list[str]) -> str | None:
        """Prompt user to select preferred scanlator."""
        from rich.table import Table
        
        console.print("\n[bold magenta]🎨 Multiple Scanlators Available[/]")
        
        table = Table(box=box.ROUNDED, border_style="cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column("Scanlator Group", style="white")
        
        table.add_row("0", "[dim]Any (first available)[/]")
        for idx, name in enumerate(scanlators, 1):
            table.add_row(str(idx), name)
        
        console.print(table)
        
        choices = ["0"] + [str(i) for i in range(1, len(scanlators) + 1)]
        choice = Prompt.ask(
            "\n[bold cyan]Select preferred scanlator[/]",
            choices=choices,
            default="0"
        )
        
        if choice == "0":
            return None  # Any/first available
        else:
            return scanlators[int(choice) - 1]
    
    @staticmethod
    def _filter_by_scanlator(
        grouped: dict[str, list[Chapter]], 
        preferred: str | None
    ) -> list[Chapter]:
        """Filter to one chapter per number based on scanlator preference."""
        result = []
        
        for num, chs in grouped.items():
            if preferred:
                # Look for preferred scanlator first
                for ch in chs:
                    if ch.group_name == preferred:
                        result.append(ch)
                        break
                else:
                    # Fallback to first available if preferred not found
                    result.append(chs[0])
            else:
                # No preference - pick first (usually has most votes)
                result.append(chs[0])
        
        return result
    
    @staticmethod
    def _parse_selection(selection: str, chapters: list[Chapter]) -> list[Chapter]:
        """Parse chapter selection string."""
        # Create a mapping from chapter number to ALL chapters with that number
        chapter_by_num: dict[str, list[Chapter]] = {}
        for ch in chapters:
            num = str(ch.number)
            if num not in chapter_by_num:
                chapter_by_num[num] = []
            chapter_by_num[num].append(ch)
        
        # Index-based mapping (1-indexed)
        index_map = {str(i): ch for i, ch in enumerate(chapters, 1)}
        
        selected = []
        parts = selection.replace(" ", "").split(",")
        
        for part in parts:
            if "-" in part:
                # Range selection
                start_str, end_str = part.split("-", 1)
                
                try:
                    start = float(start_str)
                    end = float(end_str)
                    
                    # Select ALL chapters whose number falls in the range
                    for ch in chapters:
                        try:
                            ch_num = float(ch.number)
                            if start <= ch_num <= end:
                                selected.append(ch)
                        except (ValueError, TypeError):
                            pass
                except ValueError:
                    raise ValueError(f"Invalid range: {part}")
            else:
                # Single selection - by chapter number
                if part in chapter_by_num:
                    # Add ALL versions of this chapter number
                    selected.extend(chapter_by_num[part])
                elif part in index_map:
                    selected.append(index_map[part])
                else:
                    # Try to match flexibly
                    for ch in chapters:
                        if str(ch.number) == part:
                            selected.append(ch)
        
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for ch in selected:
            if ch.chapter_id not in seen:
                seen.add(ch.chapter_id)
                unique.append(ch)
        
        return unique


class SettingsMenu:
    """Settings configuration menu."""
    
    @staticmethod
    def show(config_manager: ConfigManager) -> bool:
        """
        Show settings menu and handle changes.
        
        Returns:
            True to return to main menu
        """
        while True:
            config = config_manager.get_download_config()
            
            display_limit = config_manager.get("chapters_display_limit", 20)
            display_text = "Show All" if display_limit == 0 else str(display_limit)
            
            options = [
                f"  [cyan bold]1[/] │ Output Format: [white]{config.output_format.value.upper()}[/]",
                f"  [cyan bold]2[/] │ Keep Images After Conversion: [white]{'✅ Yes' if config.keep_images else '❌ No'}[/]",
                f"  [cyan bold]3[/] │ Enable Logs: [white]{'✅ Yes' if config.enable_logs else '❌ No'}[/]",
                f"  [cyan bold]4[/] │ Download Path: [white]{config.download_path}[/]",
                f"  [cyan bold]5[/] │ Max Chapter Workers: [white]{config.max_chapter_workers}[/]",
                f"  [cyan bold]6[/] │ Max Image Workers: [white]{config.max_image_workers}[/]",
                f"  [cyan bold]7[/] │ Chapters Display Limit: [white]{display_text}[/]",
                f"  [cyan bold]8[/] │ Reset to Defaults",
                f"  [cyan bold]0[/] │ Back to Main Menu",
            ]
            
            panel = Panel(
                "\n".join(options),
                border_style="yellow",
                box=box.ROUNDED
            )
            console.print(panel)
            
            choice = Prompt.ask(
                "\n[bold cyan]Select option to change[/]",
                choices=["0", "1", "2", "3", "4", "5", "6", "7", "8"],
                default="0"
            )
            
            if choice == "0":
                return True
            
            elif choice == "1":
                # Output format
                format_choice = Prompt.ask(
                    "[cyan]Select format[/]",
                    choices=["images", "pdf", "cbz"],
                    default=config.output_format.value
                )
                config_manager.set("output_format", format_choice)
                console.print(f"[green]Output format set to: {format_choice.upper()}[/]")
            
            elif choice == "2":
                # Keep images
                keep = Confirm.ask(
                    "[cyan]Keep images after PDF/CBZ conversion?[/]",
                    default=config.keep_images
                )
                config_manager.set("keep_images", keep)
                console.print(f"[green]Keep images: {'Yes' if keep else 'No'}[/]")
            
            elif choice == "3":
                # Enable logs
                enable = Confirm.ask(
                    "[cyan]Enable logging?[/]",
                    default=config.enable_logs
                )
                config_manager.set("enable_logs", enable)
                console.print(f"[green]Logging: {'Enabled' if enable else 'Disabled'}[/]")
            
            elif choice == "4":
                # Download path
                path = Prompt.ask(
                    "[cyan]Enter download path[/]",
                    default=config.download_path
                )
                config_manager.set("download_path", path)
                console.print(f"[green]Download path set to: {path}[/]")
            
            elif choice == "5":
                # Max chapter workers
                workers = IntPrompt.ask(
                    "[cyan]Max concurrent chapter downloads (1-10)[/]",
                    default=config.max_chapter_workers
                )
                workers = max(1, min(10, workers))
                config_manager.set("max_chapter_workers", workers)
                console.print(f"[green]Max chapter workers: {workers}[/]")
            
            elif choice == "6":
                # Max image workers
                workers = IntPrompt.ask(
                    "[cyan]Max concurrent image downloads (1-20)[/]",
                    default=config.max_image_workers
                )
                workers = max(1, min(20, workers))
                config_manager.set("max_image_workers", workers)
                console.print(f"[green]Max image workers: {workers}[/]")
            
            elif choice == "7":
                # Chapters display limit
                console.print("[dim]Enter 0 to show all chapters[/]")
                limit = IntPrompt.ask(
                    "[cyan]Chapters to display in table (0=all, 10-100)[/]",
                    default=config_manager.get("chapters_display_limit", 20)
                )
                limit = max(0, min(500, limit))
                config_manager.set("chapters_display_limit", limit)
                display_text = "Show All" if limit == 0 else str(limit)
                console.print(f"[green]Chapters display limit: {display_text}[/]")
            
            elif choice == "8":
                # Reset to defaults
                if Confirm.ask("[yellow]Reset all settings to defaults?[/]", default=False):
                    config_manager.reset_to_defaults()
                    console.print("[green]Settings reset to defaults![/]")

from typing import List, Dict
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from goals_cli.core.models import CheckIn, Goal, GoalCategory

console = Console()

def calculate_mom_growth(checkins: List[CheckIn]) -> Dict[str, dict]:
    """
    Calculates Month-over-Month growth for global and per-category progress.
    Returns structured data for visualization.
    """
    if not checkins:
        return {}
    
    # Sort by date just in case
    sorted_checkins = sorted(checkins, key=lambda c: c.date)
    
    history = []
    
    for c in sorted_checkins:
        if not c.snapshot:
            continue
            
        period_stats = {
            "date": c.date,
            "period": c.date.strftime("%Y-%m"),
            "total_goals": len(c.snapshot),
            "avg_progress": 0,
            "categories": {}
        }
        
        total_p = 0
        cat_sums = {}
        cat_counts = {}
        
        for g_data in c.snapshot:
            # Reconstruct minimal dict or use directly
            # g_data is a dict from model_dump
            p = g_data.get("progress_percentage", 0)
            cat = g_data.get("category", "outros")
            
            total_p += p
            
            cat_sums[cat] = cat_sums.get(cat, 0) + p
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
            
        if period_stats["total_goals"] > 0:
            period_stats["avg_progress"] = round(total_p / period_stats["total_goals"], 1)
            
        for cat, s in cat_sums.items():
            count = cat_counts[cat]
            period_stats["categories"][cat] = round(s / count, 1)
            
        history.append(period_stats)
        
    return history

def render_analytics_dashboard(checkins: List[CheckIn]):
    if not checkins:
        console.print("[yellow]Sem dados históricos suficientes para análise.[/yellow]")
        return

    history = calculate_mom_growth(checkins)
    if not history:
        console.print("[yellow]Sem snapshots de dados para análise.[/yellow]")
        return
        
    # Get last 2 periods for comparison
    current = history[-1]
    previous = history[-2] if len(history) > 1 else None
    
    # 1. Header with Velocity
    velocity = 0
    if previous:
        velocity = current["avg_progress"] - previous["avg_progress"]
        
    vel_color = "green" if velocity >= 0 else "red"
    vel_sign = "+" if velocity > 0 else ""
    
    console.print(Panel(
        f"[bold]Progresso Global:[/bold] {current['avg_progress']}% "
        f"[{vel_color}]({vel_sign}{velocity:.1f}% MoM)[/{vel_color}]",
        title="📊 Analytics & MoM",
        border_style="magenta"
    ))

    # 2. Text-based Chart (Simple Bar)
    render_ascii_chart(history)
    
    # 3. Category Breakdown Table
    table = Table(title="Detalhamento por Categoria", box=box.SIMPLE)
    table.add_column("Categoria")
    table.add_column("Progresso Atual")
    table.add_column("MoM Growth", justify="right")
    
    cats = set(current["categories"].keys())
    if previous:
        cats.update(previous["categories"].keys())
        
    for cat in cats:
        curr_val = current["categories"].get(cat, 0)
        prev_val = previous["categories"].get(cat, 0) if previous else 0
        diff = curr_val - prev_val
        
        diff_style = "green" if diff > 0 else ("red" if diff < 0 else "dim")
        diff_str = f"[{diff_style}]{'+' if diff > 0 else ''}{diff:.1f}%[/{diff_style}]"
        
        # Translate category if possible or display raw
        # Assuming cat is value from enum (e.g., 'financeira')
        display_cat = cat.capitalize()
        
        table.add_row(display_cat, f"{curr_val}%", diff_str)
        
    console.print(table)
    
    # 4. Motivation / Streak
    streak = calculate_streak(checkins)
    
    streak_color = "green" if streak >= 3 else ("yellow" if streak >= 1 else "dim")
    console.print(f"\n🔥 [bold]Check-in Streak:[/bold] [{streak_color}]{streak} meses consecutivos focados![/{streak_color}]\n")

def calculate_streak(checkins: List[CheckIn]) -> int:
    """
    Calculates the streak of consecutive monthly check-ins.
    """
    if not checkins:
        return 0
        
    # Sort descending
    dates = sorted([c.date for c in checkins], reverse=True)
    
    streak = 0
    if not dates:
        return 0
        
    # Check if the most recent check-in is relevant (this month or last month)
    # If the user hasn't checked in this month yet, but did last month, the streak is alive (but pending this month)
    # If the last check-in was 2 months ago, streak is broken (0).
    
    now = datetime.now()
    current_month_val = now.year * 12 + now.month
    last_checkin_val = dates[0].year * 12 + dates[0].month
    
    diff_now = current_month_val - last_checkin_val
    
    if diff_now > 1:
        # Streak broken
        return 0
        
    streak = 1
    current_val = last_checkin_val
    
    for i in range(1, len(dates)):
        date = dates[i]
        val = date.year * 12 + date.month
        
        diff = current_val - val
        
        if diff == 1:
            streak += 1
            current_val = val
        elif diff == 0:
            continue
        else:
            break
            
    return streak


def render_ascii_chart(history: List[dict]):
    """
    Renders a simple vertical bar chart using unicode blocks.
    """
    console.print("\n[bold]Evolução Global (Últimos 12 meses)[/bold]")
    
    # Limit to last 12
    data = history[-12:]
    
    if not data:
        return

    max_val = 100 # Goals are 0-100%
    height = 10
    
    # Draw bars
    # We need to normalize avg_progress to height
    # Uses blocks:  ▂▃▄▅▆▇█
    blocks = "  ▂▃▄▅▆▇█"
    
    # visual:
    # 100% |      █
    #  50% |   █  █
    #      +----------
    
    # For simplicitly in terminal, horizontal bars might be easier to read with dates?
    # Let's try horizontal first as it allows dates on Y axis nicely? 
    # Actually user asked "along the years/months", vertical bars (time on X) is more intuitive for "Progress over time".
    
    # Let's do a simple one-line sparkline-ish or small vertical bars if possible.
    # Or just horizontal bars:
    # 2024-01: ██████░░░░ 60%
    # 2024-02: ███████░░░ 70%
    
    for item in data:
        val = item["avg_progress"]
        bar_len = int(val / 2) # 50 chars max for 100%
        bar = "█" * bar_len
        # Gradient color?
        color = "green" if val > 80 else ("yellow" if val > 50 else "blue")
        
        console.print(f"{item['period']}: [{color}]{bar}[/{color}] {val}%")
    
    console.print("")

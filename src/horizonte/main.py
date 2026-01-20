import typer
from rich import print
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.markdown import Markdown
from datetime import datetime, timedelta
from pathlib import Path
import calendar
from rich.table import Table
from rich import box
from rich.text import Text
from rich.layout import Layout

from horizonte.locales.pt_br import Strings
from horizonte.core.models import Goal, Horizon, SmartCriteria, Config, GoalCategory, GoalStatus, Milestone
from horizonte.core.storage import GoalsRepository, ConfigRepository, CheckinRepository
from horizonte.core.ai import suggest_smart_criteria, suggest_category, refine_smart_field, suggest_milestones

app = typer.Typer(help=Strings.APP_TITLE)

console = Console()

CATEGORY_COLORS = {
    GoalCategory.FINANCIAL: "green",
    GoalCategory.LIFE: "magenta",
    GoalCategory.HEALTH: "red",
    GoalCategory.PROFESSIONAL: "blue",
    GoalCategory.OTHERS: "cyan"
}

def check_due_checkins():
    config_repo = ConfigRepository()
    config = config_repo.load()
    
    # Check if we have checkins
    repo = CheckinRepository()
    files = repo.list_all()
    
    now = datetime.now()
    month_str = now.strftime("%Y-%m")
    
    # If no files, or last file is not from this month
    is_done = False
    if files:
        last_file = files[0] # sorted desc
        if month_str in last_file.name:
            is_done = True
            
    if not is_done:
        msg = None
        title = None
        
        # Check if today is the last day of the month
        last_day = calendar.monthrange(now.year, now.month)[1]
        
        if now.day == last_day:
             title = "⚠️ Último dia do Mês!"
             msg = Strings.MSG_CHECKIN_LAST_DAY
        elif now.day > 20: # Gentle reminder logic late in the month
             # Or if we want stricter logic: check if we are overdue for PREVIOUS month?
             # Current logic is simplest: Have I done checkin for CURRENT month?
             # If not, and it's late in month, remind.
             pass
             
        # Check if we are overdue for PREVIOUS month?
        # If today is Jan 5th, and last checkin was Nov...
        # Let's keep it simple: "Check-in Pendente" banner on launch if not done for current month
        pass

        # New Logic: Always show a small reminder if not done? 
        # Or only if overdue? 
        # Let's show big warning if Last Day.
        # Let's show warning if we are in first week of new month and missed previous? 
        # (That implies iterating checkin history gap? Too complex for now)
        
        # Let's stick to user request: "Notification"
        # If it is Last Day, Notify.
        # If we explicitly haven't done it by day 1 of next month, it's overdue.
        
        if title and msg:
            console.print(Panel(f"[bold red]📅 {msg}[/bold red]\n\n[italic]Execute 'horizonte checkin' para realizar o fechamento do mês.[/italic]", style="red", title=title))
            try_system_notification(title, msg)

def try_system_notification(title: str, message: str):
    """
    Attempts to send a system notification (macOS specific for now).
    """
    import platform
    import subprocess
    
    if platform.system() == "Darwin":
        try:
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script], check=False)
        except Exception:
            pass


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    Road to 35: Acompanhe suas resoluções pessoais.
    """
    if ctx.invoked_subcommand is None:
        # Verify if init is needed
        if not (Path.home() / ".road-to-35" / "goals.json").exists():
             console.print(f"[yellow]{Strings.ERR_NO_GOALS}[/yellow]")
        else:
            check_due_checkins()
            # Show progress summary
            progress() 
            
            # Interactive Main Menu
            while True:
                console.print("\n[bold]O que deseja fazer?[/bold]")
                console.print("  [1] Fazer Check-in")
                console.print("  [2] Listar Objetivos")
                console.print("  [3] Novo Objetivo")
                console.print("  [4] Detalhes de Objetivo")
                console.print("  [5] Editar Objetivo")
                console.print("  [6] Breakdown de Objetivo")
                console.print("  [7] Histórico")
                console.print("  [0] Sair")
                
                choice = Prompt.ask("Opção", choices=["1", "2", "3", "4", "5", "6", "7", "0"], default="1")
                
                if choice == "1":
                    checkin(force=False)
                elif choice == "2":
                    list_goals()
                elif choice == "3":
                    add()
                elif choice == "4":
                    try:
                        show()
                    except typer.Exit:
                        pass
                elif choice == "5":
                    try:
                        adjust()
                    except typer.Exit:
                        pass
                elif choice == "6":
                    try:
                        breakdown()
                    except typer.Exit:
                        pass
                elif choice == "7":
                    history()
                elif choice == "0":
                    break
                    
                console.print("\n" + "─"*50 + "\n") 
    else:
        # Run check on any command? Maybe too intrusive. 
        # Requirement says "on launch". 
        pass

def edit_smart_criteria_interactive(current_smart: SmartCriteria, context: dict) -> SmartCriteria:
    field_map = {
         "1": ("Specific", "specific"),
         "2": ("Measurable", "measurable"),
         "3": ("Achievable", "achievable"),
         "4": ("Relevant", "relevant"),
         "5": ("Time-bound", "time_bound")
    }

    while True:
         console.print("\n[bold]Editar Critérios SMART:[/bold]")
         for k, (label, attr) in field_map.items():
             val = getattr(current_smart, attr)
             preview = (val[:75] + '...') if len(val) > 75 else val
             console.print(f"  [{k}] [blue]{label}[/blue]: {preview}")
         console.print("  [0] Concluir Edição")
         
         choice = Prompt.ask("Selecione o campo para editar", choices=["1", "2", "3", "4", "5", "0"], default="0")
         
         if choice == "0":
             return current_smart
             
         label, attr = field_map[choice]
         current_val = getattr(current_smart, attr)
         
         console.print(Panel(f"[bold]{label}[/bold]\n\n{current_val}", title="Valor Atual"))
         console.print("[dim]Digite o novo valor, ou use [bold]/ia [instrução][/bold] para pedir alterações à IA.[/dim]")
         
         new_val = Prompt.ask("Novo valor", default=current_val)
         
         if new_val.strip().lower() == "refinar" or new_val.strip().lower().startswith("/ia"):
             instruction = None
             if new_val.strip().lower().startswith("/ia"):
                 parts = new_val.strip().split(" ", 1)
                 if len(parts) > 1:
                     instruction = parts[1]
             
             refined = refine_smart_field(label, current_val, context, user_instruction=instruction)
             if refined:
                 console.print(Panel(f"[bold]Sugestão IA:[/bold]\n\n{refined}", style="green"))
                 if Confirm.ask("Usar este texto?"):
                     setattr(current_smart, attr, refined)
         else:
             setattr(current_smart, attr, new_val)


def get_smart_criteria_interactive() -> SmartCriteria:
    console.print(f"\n[bold]{Strings.MSG_LETS_CREATE_GOAL}[/bold]")
    
    specific = Prompt.ask(f"[blue]{Strings.SMART_SPECIFIC}[/blue]")
    measurable = Prompt.ask(f"[blue]{Strings.SMART_MEASURABLE}[/blue]")
    achievable = Prompt.ask(f"[blue]{Strings.SMART_ACHIEVABLE}[/blue]")
    relevant = Prompt.ask(f"[blue]{Strings.SMART_RELEVANT}[/blue]")
    time_bound = Prompt.ask(f"[blue]{Strings.SMART_TIME_BOUND}[/blue]")
    
    return SmartCriteria(
        specific=specific,
        measurable=measurable,
        achievable=achievable,
        relevant=relevant,
        time_bound=time_bound
    )

def create_goal_interactive(horizon: Horizon = None) -> Goal:
    # 1. Ask Title and Description First to enable AI context
    title = Prompt.ask(Strings.PROMPT_GOAL_TITLE)
    description = Prompt.ask(Strings.PROMPT_GOAL_DESC)
    
    # 2. Category Selection (AI Assisted)
    category_val = None
    avail_cats = [c.value for c in GoalCategory]
    
    # Try AI Suggestion
    suggested_cat = suggest_category(title, description, avail_cats)
    
    if suggested_cat and suggested_cat in avail_cats:
        console.print(f"[dim]Categoria sugerida pela IA: {suggested_cat}[/dim]")
        if Confirm.ask(f"Confirmar categoria '{suggested_cat}'?", default=True):
             category_val = suggested_cat
    
    if not category_val:
        console.print("[bold]Selecione a Categoria:[/bold]")
        cat_menu = {str(i+1): c for i, c in enumerate(avail_cats)}
        for k, v in cat_menu.items():
            console.print(f"  [{k}] {v}")
            
        cat_choice = Prompt.ask("Opção", choices=list(cat_menu.keys()), default="1")
        category_val = cat_menu[cat_choice]
        
    category = GoalCategory(category_val)

    if not horizon:
        # Prompt for horizon
        display_map = {
            Horizon.SHORT_TERM: Strings.HORIZON_SHORT,
            Horizon.MID_TERM: Strings.HORIZON_MID,
            Horizon.LONG_TERM: Strings.HORIZON_LONG
        }
        
        horizon_menu = {
            "1": Horizon.SHORT_TERM,
            "2": Horizon.MID_TERM,
            "3": Horizon.LONG_TERM
        }
        
        console.print("[bold]Horizonte de Tempo:[/bold]")
        for k, h in horizon_menu.items():
            console.print(f"  [{k}] {display_map[h]}")
            
        h_choice = Prompt.ask(Strings.PROMPT_SELECT_HORIZON, choices=list(horizon_menu.keys()), default="1")
        horizon = horizon_menu[h_choice]

    
    smart = None
    use_ai = Confirm.ask("Gostaria que a IA (OpenRouter) sugerisse os critérios SMART?", default=False)
    
    if use_ai:
        smart_suggestion = suggest_smart_criteria(title, description, category.value, horizon.value)
        if smart_suggestion:
            console.print(Panel(
                f"[bold]Sugestão da IA:[/bold]\n\n"
                f"• [blue]Specific:[/blue] {smart_suggestion.specific}\n"
                f"• [blue]Measurable:[/blue] {smart_suggestion.measurable}\n"
                f"• [blue]Achievable:[/blue] {smart_suggestion.achievable}\n"
                f"• [blue]Relevant:[/blue] {smart_suggestion.relevant}\n"
                f"• [blue]Time-bound:[/blue] {smart_suggestion.time_bound}",
                title="IA Analysis", border_style="green"
            ))
            
            console.print("[bold]Ação:[/bold]")
            console.print("  [1] Aceitar")
            console.print("  [2] Editar/Refinar")
            console.print("  [3] Descartar")
            
            action_map = {"1": "aceitar", "2": "editar", "3": "descartar"}
            action_choice = Prompt.ask("Opção", choices=["1", "2", "3"], default="1")
            action = action_map[action_choice]
            
            if action == "aceitar":
                smart = smart_suggestion
            elif action == "editar":
                 context = {"title": title, "description": description}
                 smart = edit_smart_criteria_interactive(smart_suggestion, context)
    
    if not smart:
        smart = get_smart_criteria_interactive()
    
    return Goal(
        title=title,
        description=description,
        category=category,
        horizon=horizon,
        smart_criteria=smart
    )

@app.command(help=Strings.CMD_INIT_DESC)
def init(reset: bool = typer.Option(False, "--reset", help="Limpar objetivos existentes")):
    print(f"[bold green]{Strings.WELCOME_MESSAGE}[/bold green]")
    
    # Ensure directory exists
    from horizonte.core.storage import ensure_app_dir, GOALS_FILE
    ensure_app_dir()
    
    goals_repo = GoalsRepository()
    if GOALS_FILE.exists():
        existing_goals = goals_repo.load()
        if existing_goals:
            if reset or Confirm.ask("Já existem objetivos salvos. Deseja limpar e começar do zero?"):
                 GOALS_FILE.unlink()
                 print("[yellow]Objetivos anteriores removidos.[/yellow]")
            else:
                 print("[dim]Mantendo objetivos existentes e adicionando novos.[/dim]")
                 # List existing goals simply
                 console.print("\n[bold]Objetivos Atuais:[/bold]")
                 for g in existing_goals:
                     console.print(f" • [{g.category.value}] {g.title} ({g.horizon})")
                 console.print("\n")

    if not Confirm.ask(Strings.MSG_CONFIRM_INIT):
        raise typer.Abort()
    
    config_repo = ConfigRepository()
    config = config_repo.load()
    
    if not config.user_name:
        name = Prompt.ask(Strings.PROMPT_NAME)
        config.user_name = name
        config_repo.save(config)
    
    # User-driven Loop
    while True:
        console.print("\n[bold]Novo Objetivo[/bold]")
        
        display_map = {
            Horizon.SHORT_TERM: Strings.HORIZON_SHORT,
            Horizon.MID_TERM: Strings.HORIZON_MID,
            Horizon.LONG_TERM: Strings.HORIZON_LONG
        }
        
        menu_options = {
            "1": (Horizon.SHORT_TERM, display_map[Horizon.SHORT_TERM]),
            "2": (Horizon.MID_TERM, display_map[Horizon.MID_TERM]),
            "3": (Horizon.LONG_TERM, display_map[Horizon.LONG_TERM]),
            "0": (None, "Finalizar configuração")
        }
        
        console.print("Escolha o Horizonte:")
        for key, (val, label) in menu_options.items():
            console.print(f"  [cyan]{key}[/cyan]. {label}")

        choice = Prompt.ask("Opção", choices=list(menu_options.keys()), default="0")
        
        selected_horizon, _ = menu_options[choice]
        
        if selected_horizon is None:
            break
            
        horizon = selected_horizon
        
        console.print(Panel(f"[bold]{display_map[horizon]}[/bold]", expand=False))
        
        goal = create_goal_interactive(horizon=horizon)
        goals_repo.add(goal)
        print(f"[green]✓ {Strings.MSG_GOAL_ADDED}[/green]\n")

    print(f"[bold green]{Strings.MSG_INIT_SUCCESS}[/bold green]")
    print(f"[dim]Objetivos salvos em: {GOALS_FILE}[/dim]")

@app.command(help=Strings.CMD_ADD_DESC)
def add():
    goal = create_goal_interactive()
    GoalsRepository().add(goal)
    print(f"[bold green]{Strings.MSG_GOAL_ADDED}[/bold green]")

@app.command(name="list", help=Strings.CMD_LIST_DESC)
def list_goals():
    goals = GoalsRepository().load()
    if not goals:
        print(f"[yellow]{Strings.ERR_NO_GOALS}[/yellow]")
        return

    # Create Rich Table
    table = Table(title=Strings.CMD_LIST_DESC, box=box.ROUNDED)
    
    table.add_column("S", justify="center", style="bold")
    table.add_column("Categoria", justify="left")
    table.add_column("Horizonte", justify="left")
    table.add_column("Título", justify="left", style="bold")
    
    # Sort keys for grouping visual (optional, but we'll specific sort)
    # Let's simple sort by horizon then category
    
    horizon_order = {Horizon.SHORT_TERM: 1, Horizon.MID_TERM: 2, Horizon.LONG_TERM: 3}
    
    sorted_goals = sorted(goals, key=lambda x: (horizon_order[x.horizon], x.category))
    
    horizon_names = {
        Horizon.SHORT_TERM: Strings.HORIZON_SHORT.split('(')[0].strip(), # Simplifies display
        Horizon.MID_TERM: Strings.HORIZON_MID.split('(')[0].strip(),
        Horizon.LONG_TERM: Strings.HORIZON_LONG.split('(')[0].strip()
    }

    current_horizon = None
    
    for g in sorted_goals:
        # Add section separator if horizon changes
        if g.horizon != current_horizon:
            if current_horizon is not None:
                table.add_section()
            current_horizon = g.horizon
            
        status_icon = "✓" if g.status == "completed" else ("✕" if g.status == "abandoned" else "•")
        status_style = "dim" if g.status == "abandoned" else ("green" if g.status == "completed" else "yellow")
        
        cat_color = CATEGORY_COLORS.get(g.category, "white")
        
        table.add_row(
            f"[{status_style}]{status_icon}[/{status_style}]",
            f"[{cat_color}]{g.category.value}[/{cat_color}]",
            horizon_names[g.horizon],
            g.title if g.status != "abandoned" else f"[dim strikes]{g.title}[/dim strikes]"
        )
        
    console.print(table)

def select_goal_interactive() -> Goal:
    repo = GoalsRepository()
    goals = repo.load()
    if not goals:
        print(f"[yellow]{Strings.ERR_NO_GOALS}[/yellow]")
        raise typer.Exit()
    
    # List all goals with index
    console.print("\n")
    for i, g in enumerate(goals):
        console.print(f"[{i+1}] {g.title} ([cyan]{g.category.value}[/cyan], {g.horizon})")
    
    idx_str = Prompt.ask(Strings.MSG_SELECT_GOAL)
    try:
        idx = int(idx_str) - 1
        if 0 <= idx < len(goals):
            return goals[idx]
        else:
            print(f"[red]{Strings.ERR_INVALID_INDEX}[/red]")
            raise typer.Exit()
    except ValueError:
        print(f"[red]{Strings.ERR_INVALID_INDEX}[/red]")
        raise typer.Exit()

@app.command(help="Mostra detalhes de um objetivo")
def show():
    goal = select_goal_interactive()
    
    cat_color = CATEGORY_COLORS.get(goal.category, "white")
    
    # Header
    grid = Table.grid(expand=True)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="right")
    
    status_style = "green" if goal.status == "completed" else ("red" if goal.status == "abandoned" else "yellow")
    status_text = f"[{status_style}]{goal.status.value.upper()}[/{status_style}]"
    
    grid.add_row(
        f"[bold {cat_color} reverse] {goal.category.value.upper()} [/bold {cat_color} reverse]",
        status_text
    )
    
    console.print(Panel(grid, style=f"bold {cat_color}", title=f"[bold]{goal.title}[/bold]", subtitle=goal.horizon.value))
    
    console.print(f"\n[italic]{goal.description}[/italic]\n")
    
    # SMART Table
    smart_table = Table(show_header=False, box=box.SIMPLE, show_edge=False)
    smart_table.add_column("Type", style="bold blue", width=12)
    smart_table.add_column("Value")
    
    smart_table.add_row("Specific", goal.smart_criteria.specific)
    smart_table.add_row("Measurable", goal.smart_criteria.measurable)
    smart_table.add_row("Achievable", goal.smart_criteria.achievable)
    smart_table.add_row("Relevant", goal.smart_criteria.relevant)
    smart_table.add_row("Time-bound", goal.smart_criteria.time_bound)
    
    console.print(Panel(smart_table, title="SMART Criteria", border_style="blue"))
    
    if goal.status_reason:
        reason_color = "green" if goal.status == "completed" else "red"
        console.print(Panel(f"[{reason_color}]{goal.status_reason}[/{reason_color}]", title="Motivo do Status", border_style=reason_color))

    # History Visualization
    repo = CheckinRepository()
    checkins = repo.load_all_snapshots()
    
    history_data = []
    for c in checkins:
        if not c.snapshot: continue
        # Find this goal in snapshot
        # Snapshot is list of dicts
        goal_snap = next((g for g in c.snapshot if g.get('id') == goal.id), None)
        if goal_snap:
            history_data.append({
                "date": c.date,
                "progress": goal_snap.get('progress_percentage', 0),
                "status": goal_snap.get('status', 'active')
            })
            
    if history_data:
        console.print("\n[bold]Evolução do Progresso:[/bold]")
        # Sort by date asc
        history_data.sort(key=lambda x: x['date'])
        
        # Simple visualization
        for h in history_data:
            date_str = h['date'].strftime("%Y-%m-%d")
            prog = h['progress']
            bar_len = int(prog / 5) # Scale 100% -> 20 chars
            bar = "█" * bar_len
            
            p_color = "green" if prog == 100 else ("cyan" if prog > 0 else "dim")
            
            console.print(f"  {date_str} │ [{p_color}]{bar:<20}[/{p_color}] {prog}%")
    else:
        console.print("\n[dim]Sem histórico de check-ins para este objetivo.[/dim]")

@app.command(help="Marca um objetivo como concluído")
def complete():
    goal = select_goal_interactive()
    
    if Confirm.ask(f"Marcar '{goal.title}' como concluído?"):
        reason = Prompt.ask(Strings.PROMPT_COMPLETION_REASON)
        
        goal.status = "completed"
        goal.status_reason = reason
        goal.updated_at = datetime.now()
        
        GoalsRepository().update(goal)
        print(f"[bold green]{Strings.MSG_GOAL_COMPLETED}[/bold green]")

@app.command(help="Marca um objetivo como abandonado")
def abandon():
    goal = select_goal_interactive()
    
    if Confirm.ask(f"Marcar '{goal.title}' como abandonado?"):
        reason = Prompt.ask(Strings.PROMPT_ABANDON_REASON)
        
        goal.status = "abandoned"
        goal.status_reason = reason
        goal.updated_at = datetime.now()
        
        GoalsRepository().update(goal)
        print(f"[bold yellow]{Strings.MSG_GOAL_ABANDONED}[/bold yellow]")

@app.command(help="Edita um objetivo existente")
def adjust():
    goal = select_goal_interactive()
    
    console.print(f"[bold]Editando: {goal.title}[/bold]")
    
    # Menu for editing
    while True:
        console.print("\n[bold]O que deseja editar?[/bold]")
        console.print("  [1] Título")
        console.print("  [2] Descrição")
        console.print("  [3] Categoria")
        console.print("  [4] Horizonte")
        console.print("  [5] Critérios SMART")
        console.print("  [0] Salvar e Sair")
        
        choice = Prompt.ask("Opção", choices=["1", "2", "3", "4", "5", "0"], default="0")
        
        if choice == "0":
            break
            
        elif choice == "1":
            goal.title = Prompt.ask("Título", default=goal.title)
            
        elif choice == "2":
            goal.description = Prompt.ask("Descrição", default=goal.description)
            
        elif choice == "3":
             avail_cats = [c.value for c in GoalCategory]
             cat_menu = {str(i+1): c for i, c in enumerate(avail_cats)}
             console.print("[bold]Selecione a Categoria:[/bold]")
             for k, v in cat_menu.items():
                console.print(f"  [{k}] {v}")
             
             # Try to find current index as default
             current_idx = "1"
             if goal.category.value in avail_cats:
                 current_idx = str(avail_cats.index(goal.category.value) + 1)
                 
             cat_choice = Prompt.ask("Opção", choices=list(cat_menu.keys()), default=current_idx)
             goal.category = GoalCategory(cat_menu[cat_choice])
             
        elif choice == "4":
             display_map = {
                Horizon.SHORT_TERM: Strings.HORIZON_SHORT,
                Horizon.MID_TERM: Strings.HORIZON_MID,
                Horizon.LONG_TERM: Strings.HORIZON_LONG
            }
             horizon_menu = {
                "1": Horizon.SHORT_TERM,
                "2": Horizon.MID_TERM,
                "3": Horizon.LONG_TERM
             }
             console.print("[bold]Horizonte de Tempo:[/bold]")
             for k, h in horizon_menu.items():
                console.print(f"  [{k}] {display_map[h]}")
                
             # Try to find current index
             current_idx = "1" 
             # ... simple mapping logic back is harder without reverse map, default to 1
             
             h_choice = Prompt.ask(Strings.PROMPT_SELECT_HORIZON, choices=list(horizon_menu.keys()), default="1")
             goal.horizon = horizon_menu[h_choice]
             
        elif choice == "5":
             context = {"title": goal.title, "description": goal.description}
             goal.smart_criteria = edit_smart_criteria_interactive(goal.smart_criteria, context)
                 
    goal.updated_at = datetime.now()
    GoalsRepository().update(goal)
    print(f"[bold green]{Strings.MSG_GOAL_UPDATED}[/bold green]")


@app.command(help="Quebra um objetivo em milestones (marcos)")
def breakdown():
    goal = select_goal_interactive()
    
    console.print(f"[bold]Breakdown de Milestones: {goal.title}[/bold]")
    
    if goal.milestones:
        console.print("\n[bold]Milestones Atuais:[/bold]")
        for i, m in enumerate(goal.milestones):
            status = "[green]✓[/green]" if m.is_completed else "[dim]•[/dim]"
            console.print(f"  {status} {m.title}")
            
    if Confirm.ask("Gerar sugestões de milestones com IA?", default=True):
        smart_summary = f"{goal.smart_criteria.specific} {goal.smart_criteria.measurable} {goal.smart_criteria.time_bound}"
        suggestions = suggest_milestones(goal.title, goal.description, smart_summary)
        
        if suggestions:
            console.print("\n[bold]Sugestões da IA:[/bold]")
            for i, s in enumerate(suggestions):
                console.print(f"  [{i+1}] {s}")
                
            if Confirm.ask("Adicionar estas sugestões?", default=True):
                for s in suggestions:
                    goal.milestones.append(Milestone(title=s))
                
                goal.updated_at = datetime.now()
                GoalsRepository().update(goal)
                console.print(f"[green]Milestones adicionados![/green]")
    
    # Manual add loop could be here too, but let's start with AI


@app.command(help=Strings.CMD_CHECKIN_DESC)
def checkin(force: bool = typer.Option(False, "--force", "-f", help="Forçar check-in mesmo sem estar vencido")):
    from horizonte.core.ai import generate_checkin_interaction
    
    goals_repo = GoalsRepository()
    goals = goals_repo.load()
    active_goals = [g for g in goals if g.status == GoalStatus.ACTIVE]
    
    if not active_goals:
        print("[yellow]Sem objetivos ativos para check-in.[/yellow]")
        return

    # Check date logic (simplified: force or confirm)
    if not force:
        print(f"[bold]{Strings.CHECKIN_INTRO}[/bold]")
        if not Confirm.ask(Strings.PROMPT_FORCE_CHECKIN, default=True):
             print(f"[yellow]{Strings.MSG_CHECKIN_SKIPPED}[/yellow]")
             return
             
    # AI Intro
    now = datetime.now()
    month_str = now.strftime("%B %Y")
    intro_msg = generate_checkin_interaction(active_goals, month_str)
    
    console.print(Panel(Markdown(intro_msg), title=f"Check-in: {month_str}", style="bold magenta"))
    
    # ask mode
    console.print("\n[bold]Modo de Check-in:[/bold]")
    console.print("  [1] Interativo (Passo a passo por objetivo)")
    console.print("  [2] Conversacional IA (Texto livre, a IA processa)")
    
    mode_choice = Prompt.ask("Opção", choices=["1", "2"], default="1")
    
    checkin_data = [] # To store (goal, comment, old_progress, new_progress)
    processed_goal_ids = set()

    if mode_choice == "2":
        console.print(Panel(
            "[bold]Modo Conversacional[/bold]\n"
            "Escreva livremente sobre seu progresso no mês.\n"
            "Ex: [italic]'Avancei bem na corrida, fiz 50km. No financeiro guardei 500 reais de 1000. O resto foi normal.'[/italic]",
            style="cyan"
        ))
        
        user_text = Prompt.ask("Seu relato")
        
        from horizonte.core.ai import process_intelligent_checkin
        updates = process_intelligent_checkin(user_text, active_goals)
        
        if updates:
            console.print("\n[bold]A IA identificou as seguintes atualizações:[/bold]")
            
            # Create a map for easy lookup
            updates_map = {u['goal_id']: u for u in updates}
            
            for g in active_goals:
                if g.id in updates_map:
                    upd = updates_map[g.id]
                    processed_goal_ids.add(g.id)
                    
                    console.print(f"\n[bold cyan]Objetivo: {g.title}[/bold cyan]")
                    console.print(f"  Progresso Sugerido: {g.progress_percentage}% -> [bold green]{upd['new_percent']}%[/bold green]")
                    console.print(f"  Comentário Sugerido: [italic]{upd['comment']}[/italic]")
                    
                    if Confirm.ask("Confirmar e aplicar?", default=True):
                        checkin_data.append({
                            "goal": g,
                            "old_percent": g.progress_percentage,
                            "new_percent": upd['new_percent'],
                            "comment": upd['comment']
                        })
                        
                        # Update object immediately for accurate snapshot
                        g.progress_percentage = upd['new_percent']
                        g.updated_at = now
                        goals_repo.update(g)
                    else:
                        processed_goal_ids.remove(g.id) # Treat as not processed to fallback to manual
            
        else:
            console.print("[yellow]A IA não identificou atualizações claras. Vamos para o modo manual.[/yellow]")
            
    # Process remaining goals (or all if mode 1)
    remaining_goals = [g for g in active_goals if g.id not in processed_goal_ids]
    
    if remaining_goals:
        if mode_choice == "2" and processed_goal_ids:
             console.print("\n[bold]Vamos verificar os objetivos restantes manualmentes:[/bold]")
             
        for g in remaining_goals:
            console.print(f"\n[bold cyan]Objetivo: {g.title} ({g.progress_percentage}%)[/bold cyan]")
            console.print(f"[dim]SMART: {g.smart_criteria.measurable}[/dim]")
            
            # 1. Update Percentage
            while True:
                try:
                    new_prog_str = Prompt.ask("Novo % de conclusão (0-100)", default=str(g.progress_percentage))
                    new_prog = int(new_prog_str)
                    if 0 <= new_prog <= 100:
                        break
                    console.print("[red]Por favor, entre um valor entre 0 e 100.[/red]")
                except ValueError:
                     console.print("[red]Valor inválido.[/red]")
            
            # 2. Comment
            comment = Prompt.ask("Comentário sobre o progresso")
            
            checkin_data.append({
                "goal": g,
                "old_percent": g.progress_percentage,
                "new_percent": new_prog,
                "comment": comment
            })
            
            # Update Goal Object
            g.progress_percentage = new_prog
            g.updated_at = now
            goals_repo.update(g)
    
    # Save Check-in File
    md_content = f"# Check-in {month_str}\n\n"
    md_content += f"**Data:** {now.strftime('%Y-%m-%d %H:%M')}\n\n"
    md_content += intro_msg + "\n\n"
    md_content += "## Atualizações de Objetivos\n\n"
    
    if mode_choice == "2":
         md_content += "**Nota:** Check-in iniciado via Conversacional IA.\n"
         md_content += f"> *\"{user_text}\"*\n\n"
    
    for item in checkin_data:
        g = item['goal']
        diff = item['new_percent'] - item['old_percent']
        diff_str = f"+{diff}%" if diff >= 0 else f"{diff}%"
        
        md_content += f"### {g.title} ({g.category.value})\n"
        md_content += f"- **Progresso:** {item['old_percent']}% -> {item['new_percent']}% ({diff_str})\n"
        md_content += f"- **Comentário:** {item['comment']}\n\n"
        
    # General Reflection
    md_content += "## Reflexão Geral\n"
    general_feeling = Prompt.ask("\n[bold]Para fechar: Como você resume esse mês em uma frase?[/bold]")
    md_content += f"{general_feeling}\n\n"

    # AI Analysis & Summary
    from horizonte.core.ai import analyze_checkin_period
    
    ai_summary = analyze_checkin_period(checkin_data, general_feeling, month_str)
    
    if ai_summary:
        while True:
            console.print(Panel(Markdown(ai_summary), title="Resumo da IA", border_style="cyan"))
            
            console.print("[dim]Deseja usar este resumo? [S]im, [E]ditar manualmente, ou use [bold]/ia [instrução][/bold] para pedir ajustes.[/dim]")
            choice = Prompt.ask("Ação", default="S")
            
            if choice.lower() == "s":
                break
            elif choice.lower() == "e":
                ai_summary = Prompt.ask("Edite o resumo", default=ai_summary)
            elif choice.lower().startswith("/ia") or choice.strip() == "/ia":
                instruction = None
                if choice.lower().startswith("/ia"):
                     parts = choice.strip().split(" ", 1)
                     if len(parts) > 1:
                         instruction = parts[1]
                
                new_summary = analyze_checkin_period(checkin_data, general_feeling, month_str, user_instruction=instruction)
                if new_summary:
                    ai_summary = new_summary
            else:
                # Treat as manual edit or ignore? Let's assume S check handles most, but let's be safe
                pass

        md_content += "## Análise do Coach IA\n"
        md_content += f"{ai_summary}\n"

    from horizonte.core.models import CheckIn, CheckInType
    
    checkin_obj = CheckIn(
        type=CheckInType.MONTHLY,
        goals_covered=[g.id for g in active_goals],
        file_path="",
        snapshot=[g.model_dump(mode='json') for g in active_goals] 
    )
    
    repo = CheckinRepository()
    saved_path = repo.save(checkin_obj, md_content)
    
    print(f"\n[bold green]Check-in concluído e salvo em:[/bold green] {saved_path}")
    
    # Show Summary Table
    summary_table = Table(title="Resumo do Progresso", box=box.SIMPLE)
    summary_table.add_column("Objetivo")
    summary_table.add_column("Progresso", justify="right")
    summary_table.add_column("Delta", justify="right")
    
    for item in checkin_data:
        diff = item['new_percent'] - item['old_percent']
        diff_style = "green" if diff > 0 else "dim"
        summary_table.add_row(
            item['goal'].title, 
            f"{item['new_percent']}%", 
            f"[{diff_style}]{'+' if diff > 0 else ''}{diff}%[/{diff_style}]"
        )
    
    console.print(summary_table)

@app.command(help=Strings.CMD_HISTORY_DESC)
def history():
    repo = CheckinRepository()
    files = repo.list_all()
    
    if not files:
        print("[yellow]Nenhum histórico encontrado.[/yellow]")
        return
        
    console.print(Panel(f"[bold]{Strings.HEADER_HISTORY}[/bold]", style="cyan"))
    
    for f in files:
        # Assuming filename YYYY-MM-DD-type.md
        name_parts = f.stem.split('-')
        if len(name_parts) >= 3:
            date_str = f"{name_parts[0]}-{name_parts[1]}-{name_parts[2]}"
            console.print(f" • [bold]{date_str}[/bold]: {f.name} ([dim]{f.stat().st_size} bytes[/dim])")
        else:
             console.print(f" • {f.name}")

@app.command(help=Strings.CMD_PROGRESS_DESC)
def progress():
    goals = GoalsRepository().load()
    repo = CheckinRepository()
    # Load full snapshots for analytics
    checkins = repo.load_all_snapshots()
    
    total = len(goals)
    completed = sum(1 for g in goals if g.status == "completed")
    abandoned = sum(1 for g in goals if g.status == "abandoned")
    active = sum(1 for g in goals if g.status == "active")
    
    # 1. High Level Stats
    console.print(Panel(f"[bold]{Strings.HEADER_PROGRESS}[/bold]", style="magenta"))
    
    from rich.table import Table
    table = Table(show_header=False, box=None)
    table.add_row(Strings.LABEL_TOTAL_GOALS, str(total))
    table.add_row(f"[green]{Strings.LABEL_COMPLETED}[/green]", str(completed))
    table.add_row(f"[blue]{Strings.LABEL_ACTIVE}[/blue]", str(active))
    table.add_row(f"[dim]{Strings.LABEL_ABANDONED}[/dim]", str(abandoned))
    table.add_row(Strings.LABEL_CHECKINS, str(len(checkins)))
    
    console.print(table)
    
    # 2. Detailed Analytics Dashboard
    from horizonte.core.analytics import render_analytics_dashboard
    
    if checkins:
        console.print("\n")
        render_analytics_dashboard(checkins)
    else:
        console.print("\n[dim]Realize seu primeiro check-in para ver análises detalhadas de progresso ao longo do tempo.[/dim]")

if __name__ == "__main__":
    app()

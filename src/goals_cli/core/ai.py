import os
import json
import re
from typing import Optional, Dict
from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel

from goals_cli.core.models import SmartCriteria

load_dotenv()

console = Console()

def _extract_value_from_text(text: str) -> Optional[float]:
    """
    Extracts a financial/numeric value from text using Python regex.
    Handles 'k', 'm', 'mi', 'bi' suffixes and pt-BR formatting.
    """
    if not text:
        return None
        
    clean_text = text.lower().replace("r$", "").replace("us$", "").strip()
    
    # Regex to capture number + optional suffix
    # Matches: 227k, 227.5k, 1.5m, 1000, 1,000.00
    match = re.search(r'([\d\.,]+)\s*(k|m|mi|bi|t)?', clean_text)
    if not match:
        return None
        
    num_str = match.group(1)
    suffix = match.group(2)
    
    # Normalize number string (handling pt-BR dots/commas)
    if '.' in num_str and ',' in num_str:
        num_str = num_str.replace('.', '').replace(',', '.')
    elif ',' in num_str:
        # If only comma, assume decimal
        num_str = num_str.replace(',', '.')
    
    try:
        val = float(num_str)
    except ValueError:
        return None
        
    if suffix:
        if suffix == 'k':
            val *= 1000
        elif suffix in ['m', 'mi']:
            val *= 1_000_000
        elif suffix == 'bi':
            val *= 1_000_000_000
            
    return val


def get_ai_client() -> Optional[OpenAI]:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None
    
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

def suggest_smart_criteria(title: str, description: str, category: str, horizon: str) -> Optional[SmartCriteria]:
    client = get_ai_client()
    if not client:
        # Fallback quiet or notify once? Assuming already checked.
        return None
    
    model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
    
    prompt = f"""
    Atue como um especialista em produtividade e objetivos (Life Coach).
    O usuário tem o seguinte objetivo:
    
    Título: {title}
    Descrição: {description}
    Categoria: {category}
    Horizonte: {horizon}
    
    Sua tarefa é expandir este objetivo em critérios SMART (Específico, Mensurável, Atingível, Relevante, Temporal).
    Seja conciso, direto e prático. Responda em Português (Brasil).
    
    Retorne APENAS um objeto JSON no seguinte formato, sem markdown code blocks:
    {{
        "specific": "...",
        "measurable": "...",
        "achievable": "...",
        "relevant": "...",
        "time_bound": "..."
    }}
    """
    
    try:
        with console.status("[bold green]Consultando a IA para refinar seu objetivo...[/bold green]"):
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown logic if present
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            elif content.startswith("```"):
                content = content.replace("```", "")
                
            data = json.loads(content)
            
            return SmartCriteria(
                specific=data.get("specific", ""),
                measurable=data.get("measurable", ""),
                achievable=data.get("achievable", ""),
                relevant=data.get("relevant", ""),
                time_bound=data.get("time_bound", "")
            )
            
    except Exception as e:
        console.print(f"[red]Erro ao consultar IA: {str(e)}[/red]")
        return None

def refine_smart_field(field_name: str, current_value: str, context_goal: Dict[str, str], user_instruction: str = None) -> Optional[str]:
    """
    Refine a specific SMART field using AI suggestion, optionally guided by user instruction.
    """
    client = get_ai_client()
    if not client:
        return None
    
    model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
    
    base_instruction = """
    Sua tarefa: Melhore e refine este texto para torná-lo mais forte, claro e acionável, mantendo o sentido original.
    Se o texto original for muito breve ou vago, expanda-o.
    Se já estiver bom, apenas faça pequenos ajustes de clareza.
    """
    
    if user_instruction:
        base_instruction = f"""
        Sua tarefa: Reescreva este texto seguindo a instrução específica do usuário: "{user_instruction}".
        Mantenha o contexto do objetivo, mas priorize atender ao pedido do usuário.
        """
    
    prompt = f"""
    O usuário está definindo o critério '{field_name}' para um objetivo SMART.
    
    Contexto do Objetivo:
    Título: {context_goal['title']}
    Descrição: {context_goal['description']}
    
    Valor atual '{field_name}':
    "{current_value}"
    
    {base_instruction}
    
    Responda APENAS com o texto melhorado/reescrito, sem aspas e sem explicações adicionais.
    Responda em Português (Brasil).
    """
    
    try:
        with console.status(f"[bold green]Refinando '{field_name}'...[/bold green]"):
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
            
    except Exception as e:
        console.print(f"[red]Erro ao refinar: {str(e)}[/red]")
        return None

def suggest_category(title: str, description: str, avail_categories: list) -> Optional[str]:
    """
    Suggests a category for the goal based on title and description.
    """
    client = get_ai_client()
    if not client:
        return None
        
    model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
    
    prompt = f"""
    Com base no Título e Descrição do objetivo abaixo, classifique-o EM UMA das seguintes categorias:
    {', '.join(avail_categories)}
    
    Título: {title}
    Descrição: {description}
    
    Retorne APENAS a palavra da categoria escolhida, em minúsculas, sem pontuação.
    Se nenhuma se encaixar perfeitamente, retorne 'outros'.
    """
    
    try:
        with console.status("[bold green]Sugerindo categoria...[/bold green]"):
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )
            return response.choices[0].message.content.strip().lower()
    except Exception as e:
        console.print(f"[red]Erro ao sugerir categoria: {str(e)}[/red]")
        return None

def generate_checkin_interaction(goals: list, period: str) -> str:
    """
    Generates a fun, interactive intro for the check-in session using AI.
    """
    client = get_ai_client()
    if not client:
        return f"Bem-vindo ao seu check-in de {period}! Vamos ver como você está indo."
    
    model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
    
    goals_summary = "\n".join([f"- {g.title} ({g.category.value})" for g in goals])
    
    prompt = f"""
    O usuário vai iniciar um check-in de progresso dos seus objetivos para o período: {period}.
    
    Objetivos em andamento:
    {goals_summary}
    
    Crie uma breve introdução (1-2 parágrafos) divertida, encorajadora e interativa para começar o check-in.
    Use emojis. Fale como um coach amigo e energético.
    Pergunte se ele está pronto para detonar.
    
    Responda em Português (Brasil).
    """
    
    try:
        with console.status("[bold magenta]Preparando seu check-in...[/bold magenta]"):
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Bem-vindo ao seu check-in de {period}! Vamos ver como você está indo."

def analyze_checkin_period(checkin_data: list, user_reflection: str, period: str, user_instruction: str = None) -> Optional[str]:
    """
    Analyzes the check-in data and user reflection to provide a cohesive summary.
    """
    client = get_ai_client()
    if not client:
        return None
        
    model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
    
    updates_text = ""
    for item in checkin_data:
        g = item['goal']
        diff = item['new_percent'] - item['old_percent']
        updates_text += f"- {g.title}: {item['old_percent']}% -> {item['new_percent']}% (Total: {g.progress_percentage}%). Comentário: {item['comment']}\n"
    
    base_instruction = """
    Sua tarefa: Crie um RESUMO ANALÍTICO E MOTIVACIONAL deste check-in.
    1. Destaque as maiores vitórias (maiores progressos).
    2. Mencione gentlmente onde houve estagnação, sugerindo foco.
    3. Incorpore o sentimento do usuário ("Reflexão do Usuário") na narrativa.
    4. Termine com uma frase de impacto para o próximo mês.
    Use emojis e tom de coach parceiro.
    """
    
    if user_instruction:
        base_instruction = f"""
        Sua tarefa: Refaça o resumo analítico seguindo a instrução do usuário: "{user_instruction}".
        Use os dados fornecidos, mantenha o tom motivacional, mas priorize o pedido do usuário.
        """
    
    prompt = f"""
    Dados do Check-in ({period}):
    
    {updates_text}
    
    Reflexão do Usuário: "{user_reflection}"
    
    {base_instruction}
    
    Responda em Português (Brasil).
    """
    
    try:
        with console.status("[bold magenta]Analisando seu progresso...[/bold magenta]"):
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
    except Exception as e:
        console.print(f"[red]Erro na análise: {str(e)}[/red]")
        return None

def process_intelligent_checkin(user_text: str, goals: list) -> list:
    """
    Parses user natural language text to extract progress updates for goals.
    Supports value translation (e.g. 150k/1M -> 15%).
    Returns a list of dicts: [{'goal_id': str, 'new_percent': int, 'comment': str, 'confidence': float}]
    """
    client = get_ai_client()
    if not client:
        return []
        
    model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
    
    # Context for AI
    goals_context = []
    for g in goals:
        # Pre-calculate target from title/description
        inferred_target = _extract_value_from_text(g.title)
        if inferred_target is None:
            inferred_target = _extract_value_from_text(g.description)

        goals_context.append({
            "id": g.id,
            "title": g.title,
            "description": g.description,
            "category": g.category.value if hasattr(g.category, 'value') else str(g.category),
            "horizon": g.horizon.value if hasattr(g.horizon, 'value') else str(g.horizon),
            "current_percent": g.progress_percentage,
            "smart_measurable": g.smart_criteria.measurable,
            "inferred_target_value": inferred_target
        })
        
    goals_json = json.dumps(goals_context, ensure_ascii=False)
    
    # Pre-extract numbers from user input as hints
    inferred_input_values = []
    # Find all potential matches in user text
    matches = re.finditer(r'([\d\.,]+)\s*(k|m|mi|bi|t)?', user_text.lower())
    for m in matches:
        val = _extract_value_from_text(m.group(0))
        if val is not None:
            inferred_input_values.append(val)
    
    input_hints = f"Números detectados via Python no input: {inferred_input_values}"
    
    prompt = f"""
    Você é um assistente inteligente de tracking de objetivos.
    
    CONTEXTO (Objetivos do Usuário):
    {goals_json}
    
    TEXTO DO USUÁRIO (Update de Check-in):
    "{user_text}"
    
    HINTS (Python Engine):
    {input_hints}
    
    SUA TAREFA:
    1. Analise o texto do usuário e determine quais objetivos devem ser atualizados.
       - IMPORTANTE: Se uma informação (ex: "tenho 50k agora") se aplica a múltiplos objetivos (ex: um de Curto Prazo e outro de Longo Prazo da mesma categoria), GERE UPDATES PARA TODOS ELES.
    2. Para cada objetivo identificado, extraia valores para cálculo.
       - 'target_value': Use o 'inferred_target_value' do contexto SE ele existir, a menos que o usuário esteja explicitamente mudando a meta.
       - 'current_value': Tente casar os números do texto do usuário com o valor atual deste objetivo.
       - Se o usuário disse "277k em 27", e '277k' está nos hints, use 277000.
    
    Retorne APENAS um JSON array. Formato:
    [
        {{
            "goal_id": "id_do_objetivo",
            "target_value": 227000, 
            "current_value": 277000,
            "delta_value": null,
            "explicit_percent": null,
            "comment": "Comentário curto.",
            "reasoning": "Texto explicativo"
        }}
    ]
    """
    
    try:
        with console.status("[bold cyan]Interpretando seu check-in com IA + Math Engine...[/bold cyan]"):
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs JSON. Convert all written numbers (k, M, mi) to float."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1, 
            )
            
            content = response.choices[0].message.content.strip()
            
            # Cleanup Markdown
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            elif content.startswith("```"):
                content = content.replace("```", "")
            
            raw_data = json.loads(content)
            
            # Post-processing with Python Math
            processed_data = []
            
            # Get goal objects for reference
            goals_map = {g.id: g for g in goals}
            
            for item in raw_data:
                g_id = item.get("goal_id")
                goal = goals_map.get(g_id)
                if not goal:
                    continue
                    
                new_percent = goal.progress_percentage # Default to no change
                
                # Math Logic
                if item.get("explicit_percent") is not None:
                    new_percent = float(item["explicit_percent"])
                
                elif item.get("target_value"):
                    target = float(item["target_value"])
                    current = None
                    
                    if item.get("current_value") is not None:
                        current = float(item["current_value"])
                    elif item.get("delta_value") is not None:
                        # Infer current from previous % + delta
                        # Current Abs = (Old % * Target / 100) + Delta
                        old_abs = (goal.progress_percentage / 100.0) * target
                        current = old_abs + float(item["delta_value"])
                        
                    if current is not None and target > 0:
                        new_percent = (current / target) * 100.0
                
                # Cap at 0-100
                new_percent = max(0, min(100, int(round(new_percent))))
                
                processed_data.append({
                    "goal_id": g_id,
                    "new_percent": new_percent,
                    "comment": item.get("comment", ""),
                    "reasoning": item.get("reasoning", "")
                })
                
            return processed_data
            
    except Exception as e:
        console.print(f"[red]Erro ao processar check-in inteligente: {str(e)}[/red]")
        return []

# Horizonte CLI

Uma Interface de Linha de Comando (CLI) poderosa e aprimorada por IA para acompanhar seus objetivos de vida, visão e progresso.

## Funcionalidades

- **Gerenciamento de Objetivos**: Crie, acompanhe e gerencie objetivos em diferentes categorias (Financeiro, Vida, Saúde, Profissional).
- **Horizontes Inteligentes**: Acompanhe sua visão de Curto Prazo vs Longo Prazo.
- **Integração com IA**:
    - **Critérios SMART**: A IA sugere critérios Específicos, Mensuráveis, Atingíveis, Relevantes e Temporais para seus objetivos.
    - **Check-ins Inteligentes**: Atualizações em linguagem natural (Corri 10KM esse mês) são analisadas automaticamente e aplicadas aos objetivos relevantes.
    - **Análise de Progresso**: Receba feedback motivacional e resumos analíticos do seu progresso.
- **Privacidade em Primeiro Lugar**: Todos os dados são armazenados localmente.

## Instalação

```bash
uv sync
```

## Como Usar

Execute a CLI usando `uv run`:

```bash
uv run horizonte [COMANDO]
```

### Comandos Comuns

- `uv run horizonte init`: Inicializa o banco de dados.
- `uv run horizonte add`: Adiciona um novo objetivo (interativo).
- `uv run horizonte list`: Lista todos os objetivos ativos.
- `uv run horizonte checkin`: Inicia uma sessão de check-in interativa.
- `uv run horizonte progress`: Visualiza seu progresso geral.

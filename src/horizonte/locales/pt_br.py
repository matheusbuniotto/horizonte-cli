class Strings:
    # General
    APP_TITLE = "Road to 35 - Resoluções Pessoais"
    WELCOME_MESSAGE = "Bem-vindo ao Road to 35!"
    
    # Horizons
    HORIZON_SHORT = "Curto Prazo (1 ano)"
    HORIZON_MID = "Médio Prazo (2-5 anos)"
    HORIZON_LONG = "Longo Prazo (1 década)"
    
    # Categories
    CAT_FINANCIAL = "Financeira"
    CAT_LIFE = "Vida"
    CAT_HEALTH = "Saúde"
    CAT_PROFESSIONAL = "Profissional"
    CAT_OTHERS = "Outros"
    PROMPT_SELECT_CATEGORY = "Selecione a categoria"

    
    # SMART Criteria Prompts
    SMART_SPECIFIC = "Específico: O que exatamente você quer alcançar? (Quem, o quê, onde, por quê)"
    SMART_MEASURABLE = "Mensurável: Como você saberá que alcançou este objetivo? Quanto/Quantos?"
    SMART_ACHIEVABLE = "Atingível: Isso é realista para você agora? Como você vai conseguir?"
    SMART_RELEVANT = "Relevante: Por que isso é importante para você agora? Vale a pena o esforço?"
    SMART_TIME_BOUND = "Temporal: Quando você quer alcançar isso? Existe um prazo final?"
    
    # Commands
    CMD_INIT_DESC = "Inicializa o Road to 35 e cria seus primeiros objetivos."
    CMD_ADD_DESC = "Adiciona um novo objetivo."
    CMD_LIST_DESC = "Lista seus objetivos ativos."
    CMD_CHECKIN_DESC = "Inicia um check-in de reflexão."
    
    # Errors
    ERR_NO_GOALS = "Nenhum objetivo encontrado. Use 'road-to-35 init' para começar."
    ERR_INVALID_OPTION = "Opção inválida."
    
    # Interaction
    PROMPT_NAME = "Como você gostaria de ser chamado?"
    PROMPT_GOAL_TITLE = "Dê um título curto para este objetivo"
    PROMPT_GOAL_DESC = "Descreva este objetivo brevemente"
    PROMPT_SELECT_HORIZON = "Selecione o horizonte de tempo"
    
    MSG_INIT_SUCCESS = "Configuração inicial concluída com sucesso! Boa sorte na sua jornada."
    MSG_GOAL_ADDED = "Objetivo adicionado com sucesso!"
    MSG_LETS_CREATE_GOAL = "Vamos criar um objetivo para: "
    MSG_CONFIRM_INIT = "Isso irá guiar você na criação dos seus primeiros objetivos. Continuar?"
    
    # Actions
    MSG_SELECT_GOAL = "Selecione um objetivo (digite o número)"
    MSG_GOAL_DETAILS = "Detalhes do Objetivo"
    MSG_GOAL_COMPLETED = "Parabéns! Objetivo marcado como concluído."
    MSG_GOAL_ABANDONED = "Objetivo marcado como abandonado."
    MSG_GOAL_UPDATED = "Objetivo atualizado."
    PROMPT_COMPLETION_REASON = "Reflexão final (opcional)"
    PROMPT_ABANDON_REASON = "Por que você decidiu abandonar este objetivo"
    PROMPT_NEW_VALUE = "Novo valor (Enter para manter '{current}')"
    ERR_INVALID_INDEX = "Índice inválido."

    # Check-in
    CHECKIN_TITLE = "Check-in Mensal: {month}"
    CHECKIN_INTRO = "Vamos refletir sobre o seu progresso no último mês."
    CHECKIN_Q_FEELING = "Como você se sentiu em relação aos seus objetivos este mês?"
    CHECKIN_Q_PROGRESS = "Qual foi o maior progresso que você fez?"
    CHECKIN_Q_OBSTACLES = "Quais obstáculos atrapalharam?"
    CHECKIN_Q_ADJUSTMENTS = "O que você precisa ajustar para o próximo mês?"
    MSG_CHECKIN_SAVED = "Check-in salvo com sucesso em: {path}"
    MSG_NO_DUE_CHECKIN = "Nenhum check-in pendente por enquanto."
    MSG_CHECKIN_DUE = "Você tem um check-in mensal pendente!"
    PROMPT_FORCE_CHECKIN = "Deseja forçar um check-in agora?"
    MSG_CHECKIN_SKIPPED = "Check-in adiado."
    MSG_CHECKIN_LAST_DAY = "Hoje é o último dia do mês! Hora do seu Check-in Mensal."
    
    # Progress
    CMD_HISTORY_DESC = "Mostra o histórico de check-ins."
    CMD_PROGRESS_DESC = "Visualiza o progresso geral."
    HEADER_HISTORY = "Histórico de Check-ins"
    HEADER_PROGRESS = "Progresso Geral"
    
    LABEL_TOTAL_GOALS = "Total de Objetivos"
    LABEL_COMPLETED = "Concluídos"
    LABEL_ACTIVE = "Ativos"
    LABEL_ABANDONED = "Abandonados"
    LABEL_CHECKINS = "Check-ins Realizados"

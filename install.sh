#!/bin/bash

# Simple install script for Horizonte CLI

echo "Instalando Horizonte CLI..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Erro: 'uv' não encontrado. Por favor instale o uv primeiro: https://github.com/astral-sh/uv"
    exit 1
fi

# Install from local directory if running inside dev env, or install from git if distributed.
# Assuming this script is distributed with the source, we install from CWD "."
uv tool install . --force

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Instalação concluída com sucesso!"
    echo "Agora você pode usar o comando 'horizonte' no seu terminal."
    echo "Exemplo: horizonte list"
else
    echo "❌ Falha na instalação."
fi

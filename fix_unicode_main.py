#!/usr/bin/env python3
"""
Script para remover caracteres Unicode do main.py para compatibilidade Windows
"""

import re

def fix_unicode_chars():
    """Remove caracteres Unicode do main.py"""
    
    # Mapeamento de emojis para texto
    unicode_map = {
        '🚀': '[COMANDO]',
        '✅': '[OK]',
        '📁': '[ARQUIVO]', 
        '❌': '[ERRO]',
        '🎯': '[COMANDO]',
        '📊': '[DADOS]',
        '📦': '[PACOTE]',
        '🔄': '[PROCESSANDO]',
        '⚠️': '[AVISO]',
        '📋': '[LISTA]',
        '🏥': '[FARMACEUTICO]',
        '💾': '[SALVANDO]',
        '🎉': '[SUCESSO]',
        '👥': '[USUARIOS]',
        '🔗': '[CONEXAO]',
        '🧪': '[TESTE]',
        '\U0001f4c1': '[DIRETORIO]'  # 📁 em formato Unicode longo
    }
    
    # Ler arquivo
    with open('src/main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Substituir emojis
    for emoji, replacement in unicode_map.items():
        content = content.replace(emoji, replacement)
    
    # Salvar arquivo
    with open('src/main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Caracteres Unicode removidos do main.py")

if __name__ == "__main__":
    fix_unicode_chars()

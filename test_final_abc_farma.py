#!/usr/bin/env python3
"""
Teste final da integração ABC Farma com main.py
"""

import sys
import os

# Adicionar src ao path
sys.path.append('src')

from main import _buscar_ncm_inteligente, _is_pharmaceutical_product
from services.unified_sqlite_service import get_unified_service

def test_final_abc_farma_integration():
    """Teste final da integração ABC Farma"""
    
    print("🏥 TESTE FINAL - INTEGRAÇÃO ABC FARMA")
    print("=" * 60)
    
    # Teste 1: Detecção farmacêutica
    print("\n1️⃣ TESTE DE DETECÇÃO FARMACÊUTICA:")
    print("-" * 40)
    
    produtos_teste = [
        ("Dipirona Sódica 500mg 20 comprimidos", True),
        ("Smartphone Samsung Galaxy S24 Ultra", False),
        ("Paracetamol 750mg caixa", True),
        ("Notebook Dell Inspiron", False),
        ("Amoxicilina 500mg cápsulas", True)
    ]
    
    for produto, esperado in produtos_teste:
        resultado = _is_pharmaceutical_product(produto.lower())
        status = "✅" if resultado == esperado else "❌"
        print(f"{status} {produto}: {resultado} (esperado: {esperado})")
    
    # Teste 2: Busca inteligente NCM para farmacêuticos
    print("\n2️⃣ TESTE DE BUSCA NCM INTELIGENTE:")
    print("-" * 40)
    
    service = get_unified_service()
    
    farmaceuticos = [
        "Dipirona Sódica 500mg 20 comprimidos",
        "Paracetamol 750mg 10 comprimidos",
        "Vitamina C 1g efervescente"
    ]
    
    for produto in farmaceuticos:
        try:
            ncm = _buscar_ncm_inteligente(produto, service)
            print(f"✅ {produto[:40]}...")
            print(f"   NCM: {ncm}")
            
            # Verificar se é NCM farmacêutico
            if ncm == '30049099':
                print("   🏥 Classificado corretamente como farmacêutico!")
            else:
                print(f"   ⚠️  NCM não farmacêutico: {ncm}")
        except Exception as e:
            print(f"❌ {produto}: Erro - {e}")
    
    # Teste 3: Busca direta ABC Farma
    print("\n3️⃣ TESTE DE BUSCA DIRETA ABC FARMA:")
    print("-" * 40)
    
    termos_busca = ["DIPIRONA", "PARACETAMOL", "AMOXICILINA"]
    
    for termo in termos_busca:
        try:
            results = service.search_abc_farma_by_text(termo, 2)
            print(f"✅ '{termo}': {len(results)} produtos encontrados")
            
            for i, result in enumerate(results, 1):
                print(f"   {i}. {result['descricao'][:60]}...")
                print(f"      NCM: {result['ncm']}")
        except Exception as e:
            print(f"❌ '{termo}': Erro - {e}")
    
    print(f"\n🎉 TESTE CONCLUÍDO!")
    print("=" * 60)

if __name__ == "__main__":
    test_final_abc_farma_integration()

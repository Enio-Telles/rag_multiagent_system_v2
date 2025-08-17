#!/usr/bin/env python3
"""
Verificar dados reais na base ABC Farma
"""

import sys
import os

# Adicionar src ao path
sys.path.append('src')

from services.unified_sqlite_service import get_unified_service

def check_abc_farma_data():
    """Verifica dados reais no ABC Farma"""
    
    unified_service = get_unified_service()
    
    print("🔍 VERIFICAÇÃO DOS DADOS ABC FARMA")
    print("=" * 60)
    
    # Buscar primeiros 10 produtos
    with unified_service.get_session() as session:
        from database.unified_sqlite_models import ABCFarmaProduct
        
        print("\n📋 PRIMEIROS 10 PRODUTOS:")
        print("-" * 40)
        
        products = session.query(ABCFarmaProduct).limit(10).all()
        
        for i, product in enumerate(products, 1):
            print(f"{i}. {product.descricao_completa[:80]}...")
            print(f"   Princípio Ativo: {product.principio_ativo}")
            print(f"   Laboratório: {product.laboratorio}")
            print(f"   NCM: {product.ncm_farmaceutico}")
            print()
        
        # Buscar produtos que contenham termos específicos
        print("\n🔍 BUSCA POR TERMOS ESPECÍFICOS:")
        print("-" * 40)
        
        termos = ['DIPIRONA', 'PARACETAMOL', 'AMOXICILINA', 'SODICA', 'mg']
        
        for termo in termos:
            count = session.query(ABCFarmaProduct).filter(
                ABCFarmaProduct.descricao_completa.ilike(f'%{termo}%')
            ).count()
            print(f"'{termo}': {count} produtos encontrados")
            
            if count > 0:
                examples = session.query(ABCFarmaProduct).filter(
                    ABCFarmaProduct.descricao_completa.ilike(f'%{termo}%')
                ).limit(3).all()
                
                print("  Exemplos:")
                for example in examples:
                    print(f"    - {example.descricao_completa[:70]}...")
                print()

if __name__ == "__main__":
    check_abc_farma_data()

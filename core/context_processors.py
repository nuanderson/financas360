# core/context_processors.py
from .models import Company

def active_company_processor(request):
    active_company = None
    # Verificamos se o ID da empresa ativa está na sessão
    if 'active_company_id' in request.session:
        company_id = request.session['active_company_id']
        try:
            # Buscamos o objeto da empresa no banco
            active_company = Company.objects.get(pk=company_id)
        except Company.DoesNotExist:
            # Se a empresa foi deletada, limpamos a sessão
            del request.session['active_company_id']

    # Retornamos um dicionário que será adicionado ao contexto de todos os templates
    return {'active_company': active_company}
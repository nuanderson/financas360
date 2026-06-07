# core/context_processors.py
from .models import Company
from .permissions import get_role


def active_company_processor(request):
    """
    Injeta em todos os templates:
      - active_company : objeto Company ativo na sessão
      - user_role      : papel do usuário logado (string)
      - user_profile   : objeto UserProfile (ou None)
    """
    active_company = None
    if 'active_company_id' in request.session:
        company_id = request.session['active_company_id']
        try:
            active_company = Company.objects.get(pk=company_id)
        except Company.DoesNotExist:
            del request.session['active_company_id']

    user_role    = 'gestor'   # default seguro
    user_profile = None
    if hasattr(request, 'user') and request.user.is_authenticated:
        try:
            user_profile = request.user.profile
            user_role    = user_profile.role
        except Exception:
            pass

    return {
        'active_company': active_company,
        'user_role':      user_role,
        'user_profile':   user_profile,
    }

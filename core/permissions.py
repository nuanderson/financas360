"""
core/permissions.py
====================
Utilitários de controle de acesso por papel (role-based access control).

Uso em views baseadas em funções:
    @role_required(ADMIN, GESTOR)
    def minha_view(request): ...

Uso em CBVs:
    class MinhaView(RoleRequiredMixin, UpdateView):
        allowed_roles = (ADMIN, GESTOR)
"""

from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

# ── Constantes de papel ────────────────────────────────────────────
ADMIN             = 'admin'
GESTOR            = 'gestor'
ANALISTA_RECEITAS = 'analista_receitas'
ANALISTA_DESPESAS = 'analista_despesas'
ANALISTA_PLANTOES = 'analista_plantoes'

# ── Grupos pré-definidos ───────────────────────────────────────────
MANAGERS         = (ADMIN, GESTOR)
FINANCE_ANALYSTS = (ADMIN, GESTOR, ANALISTA_RECEITAS, ANALISTA_DESPESAS)
ALL_ROLES        = (ADMIN, GESTOR, ANALISTA_RECEITAS, ANALISTA_DESPESAS, ANALISTA_PLANTOES)
NON_PLANTOES     = (ADMIN, GESTOR, ANALISTA_RECEITAS, ANALISTA_DESPESAS)


def get_role(user):
    """Retorna o papel do usuário. Default 'gestor' se não tiver perfil."""
    try:
        return user.profile.role
    except Exception:
        return GESTOR


def has_role(user, *roles):
    """Verifica se o usuário tem um dos papéis informados."""
    return get_role(user) in roles


def role_required(*roles):
    """
    Decorador para views baseadas em funções.
    Redireciona para company_list com mensagem de erro se o papel não for permitido.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('core:login')
            if not has_role(request.user, *roles):
                messages.error(request,
                    "Você não tem permissão para acessar esta página.")
                return redirect('core:company_list')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


class RoleRequiredMixin:
    """
    Mixin para Class-Based Views.

    Uso:
        class MinhaView(RoleRequiredMixin, UpdateView):
            allowed_roles = (ADMIN, GESTOR)
    """
    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        if self.allowed_roles and not has_role(request.user, *self.allowed_roles):
            messages.error(request,
                "Você não tem permissão para executar esta ação.")
            return redirect('core:company_list')
        return super().dispatch(request, *args, **kwargs)

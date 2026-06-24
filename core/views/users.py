"""
Gerenciamento de Usuários — Finanças 360
Apenas Administradores têm acesso.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from ..models import UserProfile, Company
from ..permissions import role_required, ADMIN


@login_required
@role_required(ADMIN)
def user_list(request):
    users = (User.objects
             .select_related('profile')
             .order_by('username'))
    return render(request, 'core/user_list.html', {'users': users})


@login_required
@role_required(ADMIN)
def user_create(request):
    if request.method == 'POST':
        username   = request.POST.get('username', '').strip()
        email      = request.POST.get('email', '').strip()
        password1  = request.POST.get('password1', '')
        password2  = request.POST.get('password2', '')
        role       = request.POST.get('role', 'gestor')
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()

        errors = []
        if not username:
            errors.append("Nome de usuário é obrigatório.")
        elif User.objects.filter(username=username).exists():
            errors.append("Este nome de usuário já está em uso.")
        if not password1:
            errors.append("Senha é obrigatória.")
        elif password1 != password2:
            errors.append("As senhas não conferem.")
        if role not in dict(UserProfile.ROLE_CHOICES):
            errors.append("Papel inválido.")

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
            )
            profile = user.profile
            profile.role = role
            profile.save()

            company_ids = request.POST.getlist('companies')
            if company_ids:
                valid_ids = Company.objects.filter(
                    pk__in=company_ids, users=request.user
                ).values_list('pk', flat=True)
                for company in Company.objects.filter(pk__in=valid_ids):
                    company.users.add(user)

            messages.success(request, f"Usuário '{username}' criado com sucesso!")
            return redirect('core:user_list')

    companies = Company.objects.filter(users=request.user).order_by('name')
    return render(request, 'core/user_form.html', {
        'action': 'create',
        'role_choices': UserProfile.ROLE_CHOICES,
        'companies': companies,
        'selected_company_ids': list(map(int, request.POST.getlist('companies'))) if request.POST else [],
    })


@login_required
@role_required(ADMIN)
def user_edit(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)

    if request.method == 'POST':
        email      = request.POST.get('email', '').strip()
        role       = request.POST.get('role', 'gestor')
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        password1  = request.POST.get('password1', '')
        password2  = request.POST.get('password2', '')

        errors = []
        if role not in dict(UserProfile.ROLE_CHOICES):
            errors.append("Papel inválido.")
        if password1 and password1 != password2:
            errors.append("As senhas não conferem.")

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            target_user.email      = email
            target_user.first_name = first_name
            target_user.last_name  = last_name
            if password1:
                target_user.set_password(password1)
            target_user.save()

            profile.role = role
            profile.save()

            company_ids = request.POST.getlist('companies')
            admin_companies = Company.objects.filter(users=request.user)
            for company in admin_companies:
                if str(company.pk) in company_ids:
                    company.users.add(target_user)
                else:
                    company.users.remove(target_user)

            messages.success(request, f"Usuário '{target_user.username}' atualizado!")
            return redirect('core:user_list')

    companies = Company.objects.filter(users=request.user).order_by('name')
    user_company_ids = list(
        Company.objects.filter(users=target_user).values_list('pk', flat=True)
    )
    return render(request, 'core/user_form.html', {
        'action': 'edit',
        'target_user': target_user,
        'profile': profile,
        'role_choices': UserProfile.ROLE_CHOICES,
        'companies': companies,
        'selected_company_ids': user_company_ids,
    })


@login_required
@role_required(ADMIN)
def user_delete(request, user_id):
    if request.method != 'POST':
        return redirect('core:user_list')
    target_user = get_object_or_404(User, pk=user_id)
    if target_user == request.user:
        messages.error(request, "Você não pode excluir sua própria conta.")
        return redirect('core:user_list')
    username = target_user.username
    target_user.delete()
    messages.success(request, f"Usuário '{username}' excluído com sucesso.")
    return redirect('core:user_list')


@login_required
@role_required(ADMIN)
def user_toggle_active(request, user_id):
    if request.method != 'POST':
        return redirect('core:user_list')
    target_user = get_object_or_404(User, pk=user_id)
    # Impede desativar a si mesmo
    if target_user == request.user:
        messages.error(request, "Você não pode desativar sua própria conta.")
        return redirect('core:user_list')
    target_user.is_active = not target_user.is_active
    target_user.save()
    status = "ativado" if target_user.is_active else "desativado"
    messages.success(request, f"Usuário '{target_user.username}' {status}.")
    return redirect('core:user_list')

from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q

from ..models import Company, Note, NoteTag
from ..forms import NoteForm, NoteTagForm


@login_required
def note_list(request):
    active_company_id = request.session.get('active_company_id')
    if not active_company_id:
        messages.error(request, "Selecione uma empresa para ver o Bloco de Notas.")
        return redirect('core:company_list')

    company = get_object_or_404(Company, pk=active_company_id, users=request.user)

    tag_filter = request.GET.get('tag')
    visibility_filter = request.GET.get('visibility')
    search_query = request.GET.get('q')
    show_archived = request.GET.get('archived') == 'true'

    query_global = Q(is_global=True) & (Q(created_by=request.user) | Q(is_public=True))
    query_company = Q(company=company) & (Q(created_by=request.user) | Q(is_public=True))
    notes = Note.objects.filter(query_global | query_company)

    if show_archived:
        notes = notes.filter(is_archived=True)
    else:
        notes = notes.filter(is_archived=False)

    if tag_filter:
        notes = notes.filter(tag__id=tag_filter)
    if visibility_filter == 'mine':
        notes = notes.filter(created_by=request.user)
    elif visibility_filter == 'public':
        notes = notes.filter(is_public=True)
    if search_query:
        notes = notes.filter(Q(title__icontains=search_query) | Q(content__icontains=search_query))

    notes = notes.order_by('reminder_date', '-created_at')
    tags = NoteTag.objects.filter(company=company)

    context = {
        'notes': notes,
        'tags': tags,
        'company': company,
        'show_archived': show_archived,
        'today': date.today(),          # fix: lembrete vencido destacado corretamente
        'note_count': notes.count(),
    }
    return render(request, 'core/note_list.html', context)


class NoteCreateView(LoginRequiredMixin, CreateView):
    model = Note
    form_class = NoteForm
    template_name = 'core/note_form.html'
    success_url = reverse_lazy('core:note_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        company_id = self.request.session.get('active_company_id')
        if company_id:
            kwargs['company'] = get_object_or_404(Company, pk=company_id)
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        if not form.instance.is_global:
            company_id = self.request.session.get('active_company_id')
            form.instance.company = get_object_or_404(Company, pk=company_id)
        if form.instance.is_global:
            form.instance.tag = None
            form.instance.company = None
        messages.success(self.request, "Nota criada com sucesso!")
        return super().form_valid(form)


class NoteUpdateView(LoginRequiredMixin, UpdateView):
    model = Note
    form_class = NoteForm
    template_name = 'core/note_form.html'
    success_url = reverse_lazy('core:note_list')

    def get_queryset(self):
        return Note.objects.filter(created_by=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.object.company:
            kwargs['company'] = self.object.company
        else:
            company_id = self.request.session.get('active_company_id')
            if company_id:
                try:
                    kwargs['company'] = Company.objects.get(pk=company_id)
                except Company.DoesNotExist:
                    pass
        return kwargs


class NoteDeleteView(LoginRequiredMixin, DeleteView):
    model = Note
    template_name = 'core/note_confirm_delete.html'
    success_url = reverse_lazy('core:note_list')

    def get_queryset(self):
        return Note.objects.filter(created_by=self.request.user)


@login_required
def tag_create(request):
    company_id = request.session.get('active_company_id')
    company = get_object_or_404(Company, pk=company_id)

    if request.method == 'POST':
        form = NoteTagForm(request.POST)
        if form.is_valid():
            tag = form.save(commit=False)
            tag.company = company
            tag.save()
            messages.success(request, "Marcador criado!")
            return redirect('core:note_list')
    else:
        form = NoteTagForm()

    return render(request, 'core/tag_form.html', {'form': form})


@login_required
def note_archive(request, pk):
    # Fix: deve ser POST para ter proteção CSRF
    if request.method != 'POST':
        return redirect('core:note_list')

    note = get_object_or_404(Note, pk=pk)
    if note.created_by != request.user:
        messages.error(request, "Você não tem permissão para alterar esta nota.")
        return redirect('core:note_list')

    note.is_archived = not note.is_archived
    note.save()

    status = "arquivada" if note.is_archived else "desarquivada"
    messages.success(request, f"Nota {status} com sucesso!")

    # Fix: ambos os casos vão para a lista de notas ativas
    # (se arquivou → mostra as que sobraram; se desarquivou → nota aparece lá)
    return redirect('core:note_list')

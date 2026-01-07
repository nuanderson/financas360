from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(value, arg):
    """
    Adiciona uma classe CSS a um campo de formulário no template.
    Uso: {{ form.meu_campo|add_class:"minha-classe-css" }}
    """
    return value.as_widget(attrs={'class': arg})

@register.filter
def sub(value, arg):
    """ Filtro para subtrair um valor de outro no template. """
    try:
        return value - arg
    except (ValueError, TypeError):
        return ''
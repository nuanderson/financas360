from django.apps import AppConfig


class CommercialConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'commercial'

    def ready(self):
        # Importa os sinais para garantir que sejam registrados
        import commercial.signals
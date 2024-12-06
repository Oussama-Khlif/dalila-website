from django.apps import AppConfig

class HumanRessorcesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'human_ressorces'

    def ready(self):
        import human_ressorces.signals
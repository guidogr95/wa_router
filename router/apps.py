from django.apps import AppConfig

class RouterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'router'
    label = 'router'
    
    def ready(self):
        import router.signals
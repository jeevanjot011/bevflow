from django.apps import AppConfig

class BevflowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bevflow'

    def ready(self):
        # run bootstrap in background or quickly (it is idempotent)
        try:
            from bevflow.aws.bootstrap import bootstrap_aws
            bootstrap_aws()
        except Exception as e:
            print("Bootstrap error (non-fatal):", e)

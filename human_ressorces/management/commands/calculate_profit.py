from django.core.management.base import BaseCommand
from human_ressorces.models import Profit_stat  

class Command(BaseCommand):
    help = 'Calculate and save profit daily'

    def handle(self, *args, **kwargs):
        Profit_stat.calculate_and_save_profit()  
        self.stdout.write(self.style.SUCCESS('Profit calculated and saved successfully.'))
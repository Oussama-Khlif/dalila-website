from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib import messages
from .models import VisitorIP, FinancialStats
from django.utils.timezone import now

class CheckBannedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if request.user.is_banned:
                messages.error(request, "Votre compte est suspendu! Veuillez contacter l'administrateur.")

                logout(request)
                return redirect('login')

        response = self.get_response(request)
        return response

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

class UniqueVisitorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        client_ip = get_client_ip(request)

        visitor, created = VisitorIP.objects.get_or_create(ip_address=client_ip)

        if not created:
            visitor.visit_time = now()
            visitor.save()

        financial_stats, created = FinancialStats.objects.get_or_create(id=1)
        financial_stats.unique_visitors.add(visitor)
        financial_stats.save()

        return response

class SuperAdminIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated and request.user.is_superuser:
            client_ip = get_client_ip(request)
            print(client_ip)
            visitor_ips = VisitorIP.objects.all()

            for visitor in visitor_ips:
                if visitor.ip_address == client_ip:
                    visitor.is_me = True
                visitor.save()

        return response
from django.urls import path
from .views import LoginView, CookieTokenRefreshView, LogoutView, PasswordResetRequestView, PasswordResetConfirmView, MeView

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/refresh/', CookieTokenRefreshView.as_view(), name='refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/password-reset/request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('auth/password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('me/', MeView.as_view(), name='me'),
]

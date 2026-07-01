from django.urls import path
from . import views

urlpatterns = [

    path('', views.home, name='home'),

    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_user, name='logout'),

    path('crop/', views.crop, name='crop'),

    path('disease/', views.disease_detection, name='disease'),

    path('history/', views.history, name='history'),

    path(
        'delete/<int:id>/',
        views.delete_prediction,
        name='delete_prediction'
    ),

    path(
        'report/',
        views.download_report,
        name='download_report'
    ),

    path(
        'dashboard/',
        views.dashboard,
        name='dashboard'
    ),

    path(
        'export-excel/',
        views.export_excel,
        name='export_excel'
    ),
    path(
    'feedback/',
    views.feedback,
    name='feedback'
),
path(
    'chatbot/',
    views.chatbot,
    name='chatbot'
),

]
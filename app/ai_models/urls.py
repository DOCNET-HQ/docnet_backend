from django.urls import path
from . import views

app_name = 'ai_models'

urlpatterns = [
    path('', views.AIModelListView.as_view(), name='model-list'),
    path('<uuid:id>/', views.AIModelDetailView.as_view(), name='model-detail'),
]

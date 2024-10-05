from django.urls import path
from .views import *

urlpatterns = [
    path('api-key/', api_key_view, name='api-key'),
    path('login/', user_login, name='login'),
    path('',FineTunningListView.as_view(),name='dashboard'),
    path('fine-tunning/',FineTunningListView.as_view(),name='models-list'),
    path('fine-tunning/create/',FineTuneExampleListView.as_view(),name='create-modal'),
    path('fine-tunning/create-job/',fine_tune,name='create-job'),
    path('fine-tunning/<str:job_id>/', FineTunnigDetailView.as_view(), name='fine-tune-model-detail'),
    path('select/<str:job_id>/', select_model, name='select-model'),
]

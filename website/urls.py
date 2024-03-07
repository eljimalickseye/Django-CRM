from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('record/<int:pk>', views.customer_record, name='record'),
    path('delete_record/<int:pk>', views.delete_record, name='delete_record'),
    path('add_record/', views.add_record, name='add_record'),
    path('update_record/<int:pk>', views.update_record, name='update_record'),
    path('update_details/', views.update_details, name='update_details'),
    path('', views.RecordListView, name='record-list'),
    path('export/', views.export_to_csv, name='export_to_csv'),
    path('export_actif/', views.export_actif, name='export_actif'),
    path('export_to_gnoc/', views.export_to_gnoc, name='export_to_gnoc'),
    path('export_tmp/', views.export_tmp, name='export_tmp'),
    path('export_to_desk/', views.export_to_desk, name='export_to_desk'),
    path('insert/', views.insert, name='insert'),
]

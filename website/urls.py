from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('home/', views.home, name='home'),
    path('status/', views.status, name='status'),
    path('adfile/', views.adfile, name='adfile'),
    path('temporaire_drh/', views.temporaire_drh, name='temporaire_drh'),

    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),

    # path('record/<int:pk>', views.customer_record, name='record'),
    # path('delete_record/<int:pk>', views.delete_record, name='delete_record'),
    # path('add_record/', views.add_record, name='add_record'),
    # path('update_record/<int:pk>', views.update_record, name='update_record'),
    # path('update_details/', views.update_details, name='update_details'),
    path('home/', views.RecordListView, name='record-list'),

    path('export/', views.export_to_csv, name='export_to_csv'),
    path('export_actif/', views.export_actif, name='export_actif'),
    path('export_to_gnoc/', views.export_to_gnoc, name='export_to_gnoc'),
    path('export_tmp/', views.export_tmp, name='export_tmp'),
    path('export_to_desk/', views.export_to_desk, name='export_to_desk'),

    path('export_status_desabled/', views.export_status_desabled, name='export_status_desabled'),
    path('export_status_gnoc/', views.export_status_gnoc, name='export_status_gnoc'),
    path('export_tmp_status/', views.export_tmp_status, name='export_tmp_status'),
    path('export_status_desc/', views.export_status_desc, name='export_status_desc'),
    path('export_status_actif/', views.export_status_actif, name='export_status_actif'),

    path('insert/', views.insert, name='insert'),
    path('insert_status/', views.insert_status, name='insert_status'),
    path('insert_admp/', views.insert_admp, name='insert_admp'),
    path('insert_tmp_drh/', views.insert_tmp_drh, name='insert_tmp_drh'),

    path('update_status/', views.update_status, name='update_status'),
    path('update_status_tmp/', views.update_status_tmp, name='update_status_tmp'),

    
    path('supprimer_toutes_donnees/', views.supprimer_toutes_donnees, name='supprimer_toutes_donnees'),
    path('supprimer_record_data/', views.supprimer_record_data, name='supprimer_record_data'),
    path('supprimer_tmp_data/', views.supprimer_tmp_data, name='supprimer_tmp_data'),
    path('supprimer_status_data/', views.supprimer_status_data, name='supprimer_status_data'),
    path('supprimer_ad_data/', views.supprimer_ad_data, name='supprimer_ad_data'),
]

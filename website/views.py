from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import SignUpForm,UploadTmpDRHForm
from .models import Record, ADStatus, AdMPReport, TemporaireDRH
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import os
import tempfile
import xlrd
from django.http import HttpResponse
import csv
from django.db import connection
import mysql.connector
import pandas as pd
from .forms import UploadCSVForm,UploadStatusForm,UploadADForm
from dateutil.relativedelta import relativedelta
import re
from django.utils import timezone
from dateutil import parser
from datetime import date

def home(request):
    now = datetime.now().date()

    # Calculer la date d'il y a trois mois
    # Approximation de trois mois à 30 jours chacun
    three_months_ago = now - timedelta(days=3*30)

    # Récupérer tous les enregistrements
    records = Record.objects.all()

    # Pagination
    paginator = Paginator(records, 100)  # 10 enregistrements par page
    page_number = request.GET.get('page')
    try:
        records = paginator.page(page_number)
    except PageNotAnInteger:
        # Si le numéro de page n'est pas un entier, afficher la première page
        records = paginator.page(1)
    except EmptyPage:
        # Si la page est vide, afficher la dernière page
        records = paginator.page(paginator.num_pages)

    # Mettre en forme les enregistrements pour les inclure dans le contexte
    all_records = []
    record_to_delete = []  # Liste pour stocker les enregistrements à supprimer
    for record in records:
        all_records.append({
            'username': record.username,
            'id': record.id,
            'last_connected': record.last_connected.strftime('%Y-%m-%d'),
            'commentaire': record.commentaire,
            'traitement': record.traitement
        })
        # Vérifier si l'enregistrement doit être supprimé
        if record.last_connected < three_months_ago:
            record_to_delete.append(record.id)

    context = {
        'three_months_ago': three_months_ago,
        'all_records': all_records,
        'record_to_delete': record_to_delete,
    }

    # Vérifier s'il y a une tentative de connexion
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        # Authentifier
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Vous êtes connecté avec succès.")
            return redirect('home')
        else:
            messages.error(
                request, "Erreur lors de la connexion. Veuillez réessayer.")
            return redirect('home')

    # Rendre la page d'accueil avec le contexte et les enregistrements paginés
    return render(request, 'home.html', {**context, 'records': records})

# Connection a la base de donnees
def connect_to_database():
    connection = mysql.connector.connect(
                    host="",
                    user="",
                    password="",
                    database=""
                )
    return connection


def welcome(request):
    return render(request, 'welcome.html')


def status(request):
    # Récupérer tous les enregistrements
    status_records = ADStatus.objects.all()

    # Pagination
    paginator = Paginator(status_records, 100)  # 10 enregistrements par page
    page_number = request.GET.get('page')
    try:
        status_records = paginator.page(page_number)
    except PageNotAnInteger:
        # Si le numéro de page n'est pas un entier, afficher la première page
        status_records = paginator.page(1)
    except EmptyPage:
        # Si la page est vide, afficher la dernière page
        status_records = paginator.page(paginator.num_pages)

    # Mettre en forme les enregistrements pour les inclure dans le contexte
    all_status_records = []
    status_record_to_delete = []  # Liste pour stocker les enregistrements à supprimer
    for status_record in status_records:
        all_status_records.append({
            'username': status_record.username,
            'id': status_record.id,
            'name':status_record.name,
            'commentaire': status_record.commentaire
        })
 

    context = {
        'all_status_records': all_status_records,
    }
    

    # Rendre la page d'accueil avec le contexte et les enregistrements paginés
    return render(request, 'status.html', {**context ,'status_records': status_records})


def adfile(request):
  # Récupérer tous les enregistrements
    ad_records =AdMPReport.objects.all()

    # Pagination
    paginator = Paginator(ad_records, 100)  # 10 enregistrements par page
    page_number = request.GET.get('page')
    try:
        ad_records = paginator.page(page_number)
    except PageNotAnInteger:
        # Si le numéro de page n'est pas un entier, afficher la première page
        ad_records = paginator.page(1)
    except EmptyPage:
        # Si la page est vide, afficher la dernière page
        ad_records = paginator.page(paginator.num_pages)

    # Mettre en forme les enregistrements pour les inclure dans le contexte
    all_ad_records = []
    for ad_record in ad_records:
        all_ad_records.append({
            'username': ad_record.username,
            'id': ad_record.id,
            'status': ad_record.status,
        })

    context = {
        'all_ad_records': all_ad_records,
    }
    

    # Rendre la page d'accueil avec le contexte et les enregistrements paginés
    return render(request, 'adfile.html', {**context, 'ad_records': ad_records})


def RecordListView(request):
    records = Record.objects.all()
    # Divise les enregistrements en pages de 10 éléments
    paginator = Paginator(records, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'home.html', {'page_obj': page_obj})


def logout_user(request):
    logout(request)
    messages.success(request, "You Have Been Logged Out...")
    return redirect('home')


def register_user(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
        # Authenticate et Login
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, "You Have Successfully Registered!")
            return redirect(home)
    else:
        form = SignUpForm()
        return render(request, 'register.html', {'form': form})

    return render(request, 'register.html', {'form': form})


def export_to_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="ElementsASupprimer.csv"'

    # Créer un ensemble pour stocker les identifiants uniques
    unique_ids = set()

    # Récupérer les enregistrements à supprimer depuis la base de données SQL
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, username, last_connected, commentaire 
            FROM website_record 
            WHERE (username NOT REGEXP CONCAT('^', last_name, '[0-9]{4,}$') 
            AND last_connected < DATE_SUB(CURDATE(), INTERVAL 1 MONTH)) 
            OR (username REGEXP CONCAT('^', last_name, '[0-9]{4,}$') 
            AND last_connected < DATE_SUB(CURDATE(), INTERVAL 3 MONTH)) 
        """)
        records_sql = cursor.fetchall()

        # Ajouter les identifiants SQL à l'ensemble
        for record_sql in records_sql:
            unique_ids.add(record_sql[0])  # On suppose que le premier élément de chaque tuple est l'identifiant

    # Récupérer les enregistrements à supprimer depuis la base de données Django
    records_to_delete = Record.objects.filter(last_connected__lt=timezone.now() - timedelta(days=30))

    # Ajouter les identifiants Django à l'ensemble, en évitant les doublons
    for record_django in records_to_delete:
        if record_django.id not in unique_ids:
            unique_ids.add(record_django.id)

    # Récupérer les enregistrements correspondant aux identifiants uniques
    records_to_write = []
    for record_id in unique_ids:
        # Recherchez d'abord dans les enregistrements SQL
        for record_sql in records_sql:
            if record_sql[0] == record_id:  # Si l'identifiant correspond
                records_to_write.append(record_sql)
                break
        else:
            # Sinon, recherchez dans les enregistrements Django
            for record_django in records_to_delete:
                if record_django.id == record_id:  # Si l'identifiant correspond
                    records_to_write.append([record_django.id, record_django.username, record_django.last_connected, record_django.commentaire])
                    break

    # Écrire les enregistrements dans le fichier CSV
    writer = csv.writer(response, delimiter=",")
    writer.writerow(['ID', 'Username', 'Last Connected Date', 'commentaire'])
    for record in records_to_write:
        writer.writerow(record)

    return response


def export_actif(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="records_to_statuts.csv"'

    # Récupérer les enregistrements actifs depuis la base de données Django
    records_actifs = Record.objects.filter(last_connected__gt=timezone.now() - timedelta(days=90), commentaire='Utilisateur actif')

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id,username,last_connected FROM website_record WHERE last_connected > DATE_SUB(CURDATE(), INTERVAL 3 MONTH) and commentaire='Utilisateur actif'")
        records_sql = cursor.fetchall()

    # Créer une liste pour stocker les enregistrements à écrire dans le fichier CSV
    records_to_write = []

    # Ajouter les enregistrements SQL à la liste
    for record_sql in records_sql:
        records_to_write.append(record_sql)

    # Ajouter les enregistrements Django à la liste
    for record_django in records_actifs:
        records_to_write.append([record_django.id, record_django.username, record_django.last_connected])

    # Écrire les enregistrements dans le fichier CSV
    writer = csv.writer(response, delimiter=",")
    writer.writerow(['ID', 'Username', 'Last Connected Date'])
    for record in records_to_write:
        writer.writerow(record)

    return response


def export_to_gnoc(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="records_gnoc.csv"'

    # Récupérer les enregistrements GNOC depuis la base de données Django
    records_gnoc = Record.objects.filter(username__regex=r'[a-zA-Z]{4}[0-9]{4}', last_connected__gt=timezone.now() - timedelta(days=30))

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id,username,last_connected,commentaire FROM website_record WHERE username REGEXP '[a-zA-Z]{4}[0-9]{4}' and last_connected > DATE_SUB(CURDATE(), INTERVAL 1 MONTH)")
        records_sql = cursor.fetchall()

    # Créer une liste pour stocker les enregistrements à écrire dans le fichier CSV
    records_to_write = []

    # Ajouter les enregistrements SQL à la liste
    for record_sql in records_sql:
        records_to_write.append(record_sql)

    # Ajouter les enregistrements Django à la liste
    for record_django in records_gnoc:
        records_to_write.append([record_django.id, record_django.username, record_django.last_connected, record_django.commentaire])

    # Écrire les enregistrements dans le fichier CSV
    writer = csv.writer(response, delimiter=",")
    writer.writerow(['ID', 'Username', 'Last Connected Date', 'commentaire'])
    for record in records_to_write:
        writer.writerow(record)

    return response


def export_tmp(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="records_tmp.csv"'

    # Récupérer les enregistrements à supprimer depuis la base de données SQL
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, username, last_connected, commentaire FROM website_record WHERE (LOWER(username) LIKE 'tmp%' OR  LOWER(username) LIKE 'ext%' OR LOWER(username) LIKE 'stg%' OR LOWER(username) LIKE 'Int%') AND last_connected > DATE_SUB(CURDATE(), INTERVAL 1 MONTH)"
        )
        records_sql = cursor.fetchall()

    # Récupérer les enregistrements à supprimer depuis la base de données Django
    records_tmp = Record.objects.filter(
        last_connected__gte=timezone.now() - timedelta(days=30),
        username__istartswith="tmp",
    ).filter(
        username__istartswith="ext"
    ).filter(
        username__istartswith="INT"
    )

    # Créer un dictionnaire pour stocker les enregistrements avec l'identifiant comme clé
    records_dict = {}

    # Ajouter les enregistrements SQL dans le dictionnaire
    for record_sql in records_sql:
        records_dict[record_sql[0]] = record_sql

    # Ajouter les enregistrements Django dans le dictionnaire en évitant les doublons
    for record_tmp in records_tmp:
        if record_tmp.id not in records_dict:
            records_dict[record_tmp.id] = [record_tmp.id, record_tmp.username, record_tmp.last_connected, record_tmp.commentaire]

    # Écrire les enregistrements dans le fichier CSV
    writer = csv.writer(response, delimiter=",")
    writer.writerow(['ID', 'Username', 'Last Date Connected', 'Commentaire'])
    for record in records_dict.values():
        writer.writerow(record)

    return response


def export_to_desk(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="records_desc.csv"'

    records_to_delete = Record.objects.filter(
        last_connected__lt=timezone.now() - timedelta(days=30),
       username__istartswith="pcci",
    ).filter(
        username__istartswith="stl"
    ).filter(
        username__istartswith="1431"
    ).filter(
        username__istartswith="1413"
    ).filter(
        username__istartswith="ksv"
    ).filter(
        username__istartswith="w2c"
    ).filter(
        username__istartswith="pop_"
    ).filter(
        username__istartswith="pdist"
    ).filter(
        username__istartswith="sitel"
    ).filter(
        username__istartswith="psup"
    )

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, username, last_connected, commentaire FROM website_record WHERE (LOWER(username) LIKE 'pcci%' OR LOWER(username) LIKE 'stl%' OR LOWER(username) LIKE '1431%' OR LOWER(username) LIKE '1413%' OR LOWER(username) LIKE 'ksv%' OR LOWER(username) LIKE 'w2c%' OR LOWER(username) LIKE 'pop_%' OR LOWER(username) LIKE 'pdist%' OR LOWER(username) LIKE 'sitel%' OR LOWER(username) LIKE 'psup%') AND last_connected > DATE_SUB(CURDATE(), INTERVAL 1 MONTH)")
        records_sql = cursor.fetchall()

    # Créer une liste pour stocker les enregistrements à écrire dans le fichier CSV
    records_to_write = []

    # Ajouter les enregistrements SQL à la liste
    for record_sql in records_sql:
        records_to_write.append(record_sql)

    # Ajouter les enregistrements Django à la liste
    for record_django in records_to_delete:
        records_to_write.append([record_django.id, record_django.username, record_django.last_connected, record_django.commentaire])

    # Écrire les enregistrements dans le fichier CSV
    writer = csv.writer(response, delimiter=",")
    writer.writerow(['ID', 'Username', 'Last Connected Date', 'commentaire'])
    for record in records_to_write:
        writer.writerow(record)

    return response


def inserer_donnees(connection, donnees_csv):
    cursor = connection.cursor()
    try:
        for index, row in donnees_csv.iterrows():
            # Insérer les données de base
            cursor.execute("INSERT INTO website_record (created_at, username, first_name, last_name, last_connected) VALUES (%s, %s, %s, %s, %s)",
                           (timezone.now(), row['username'], row['first_name'], row['last_name'], parser.parse(row['last_connected']).strftime("%Y-%m-%d")))
            
            # Récupérer la date de la dernière connexion
            last_connected = parser.parse(row['last_connected'])
            
            # Définir la durée pour les commentaires en fonction du username
            if re.match(f"^{row['last_name']}[0-9]{{4,}}$".lower(), row['username'].lower()):
                comment_interval = relativedelta(months=3)  # 3 mois pour les utilisateurs internes
            else:
                comment_interval = relativedelta(months=1)  # 1 mois par défaut
            
            # Comparer la date de la dernière connexion avec la durée pour les commentaires
            if last_connected < datetime.now() - comment_interval:
                comment = "Utilisateur inactif depuis plus de {} mois".format(comment_interval.months)
                setTraitement = "A supprimer"
            else:
                comment = "Utilisateur actif"
                setTraitement = "A garder"


            # Mettre à jour le commentaire dans la base de données
            cursor.execute("UPDATE website_record SET commentaire = %s, traitement = %s WHERE username = %s", (comment, setTraitement, row['username']))
        
        # Commit après toutes les opérations
        connection.commit()
        print("Données insérées avec succès.")
    except mysql.connector.Error as e:
        print("Erreur lors de l'insertion des données :", e)
        connection.rollback()
    finally:
        cursor.close()
        connection.close()


def insert(request):
    if request.method == 'POST' and request.FILES.get('file'):
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            # Vérifier si le fichier est un fichier Excel ou CSV
            if file.name.endswith('.xls') or file.name.endswith('.xlsx'):
                try:
                    # Utiliser pandas pour lire les données du fichier Excel
                    donnees = pd.read_excel(file)
                except Exception as e:
                    return HttpResponse("Erreur lors de la lecture du fichier Excel : {}".format(e))
            elif file.name.endswith('.csv'):
                try:
                    # Utiliser pandas pour lire les données du fichier CSV
                    donnees = pd.read_csv(file)
                except Exception as e:
                    return HttpResponse("Erreur lors de la lecture du fichier CSV : {}".format(e))
            else:
                return HttpResponse("Le fichier doit être au format Excel ou CSV.")
            
            # Connexion à la base de données MySQL
            try:

                connection = connect_to_database()

                if connection.is_connected():
                    print("Connexion à la base de données MySQL réussie.")
                    inserer_donnees(connection, donnees)
                    connection.close()
                    print("Connexion à la base de données MySQL fermée.")
            except mysql.connector.Error as e:
                print("Erreur lors de la connexion à la base de données MySQL :", e)
                return HttpResponse("Erreur lors de la connexion à la base de données MySQL")
            except Exception as e:
                print("Une erreur s'est produite lors de l'insertion des données dans la base de données MySQL :", e)
                return HttpResponse("Une erreur s'est produite lors de l'insertion des données dans la base de données MySQL")
            return redirect('home')
    else:
        form = UploadCSVForm()
    return render(request, 'AddFile.html', {'form': form})


def inserer_status_data(connection, donnees):
    cursor = connection.cursor()
    try:
        for index, row in donnees.iterrows():
            # Vérifier si la valeur est NaN et la remplacer par None
            
            # Affichez les valeurs pour le débogage
            print("Insertion de la ligne :", row)
            
            cursor.execute("INSERT INTO website_adstatus (created_at, username, name) VALUES (%s, %s, %s)",
                           (timezone.now(), row['username'], row['name']))
            
            
            # Comparer la date de la dernière connexion avec la durée pour les commentaires
            if row['username']:
                comment = "MAJ non effectue"
            else:
                comment = "A supprimer"

            # Mettre à jour le commentaire dans la base de données
            cursor.execute("UPDATE website_adstatus SET commentaire = %s WHERE username = %s", (comment, row['username']))
        
        # Commit après toutes les opérations
        connection.commit()
        print("Données insérées avec succès.")
    except mysql.connector.Error as e:
        print("Erreur lors de l'insertion des données :", e)
        connection.rollback()
    finally:
        cursor.close()
        connection.close()


def insert_status(request):
    if request.method == 'POST' and request.FILES.get('file'):
        form = UploadStatusForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            # Vérifier si le fichier est un fichier Excel ou CSV
            if file.name.endswith('.xls') or file.name.endswith('.xlsx'):
                try:
                    # Utiliser pandas pour lire les données du fichier Excel
                    donnees = pd.read_excel(file)
                except Exception as e:
                    return HttpResponse("Erreur lors de la lecture du fichier Excel : {}".format(e))
            elif file.name.endswith('.csv'):
                try:
                    # Utiliser pandas pour lire les données du fichier CSV
                    donnees = pd.read_csv(file)
                except Exception as e:
                    return HttpResponse("Erreur lors de la lecture du fichier CSV : {}".format(e))
            else:
                return HttpResponse("Le fichier doit être au format Excel ou CSV.")
            
            # Connexion à la base de données MySQL
            try:

                connection = connect_to_database()

                if connection.is_connected():
                    print("Connexion à la base de données MySQL réussie.")
                    inserer_status_data(connection, donnees)
                    connection.close()
                    print("Connexion à la base de données MySQL fermée.")
            except mysql.connector.Error as e:
                print("Erreur lors de la connexion à la base de données MySQL :", e)
                return HttpResponse("Erreur lors de la connexion à la base de données MySQL")
            except Exception as e:
                print("Une erreur s'est produite lors de l'insertion des données dans la base de données MySQL :", e)
                return HttpResponse("Une erreur s'est produite lors de l'insertion des données dans la base de données MySQL")
            return redirect('status')
    else:
        form = UploadStatusForm()
    return render(request, 'AddFileStatus.html', {'form': form})


def inserer_admp_data(connection, donnees):
    cursor = connection.cursor()
    try:
        for index, row in donnees.iterrows():
            username = row.get('username')
            status = row.get('status')
            
            # Vérifier si les valeurs de username et status sont présentes et valides
            if username and status == 'enabled':
                # Insérer les données de base
                cursor.execute("INSERT INTO website_admpreport (created_at, username, status) VALUES (%s, %s, %s)",
                               (timezone.now(), username, status))
        
        # Commit après toutes les opérations
        connection.commit()
        print("Données insérées avec succès.")
    except mysql.connector.Error as e:
        print("Erreur lors de l'insertion des données :", e)
        connection.rollback()
    finally:
        cursor.close()


def update_status_from_adm():
    # Récupérer tous les enregistrements du modèle Status
    status_records = ADStatus.objects.all()

    for status_record in status_records:
        username = status_record.username
        commentaire = status_record.commentaire
        last_4_characters = username[-4:]
        
        # Vérifier si le username existe dans le modèle Adm
        try:
            ad_record = AdMPReport.objects.get(username__endswith=last_4_characters)
            status = ad_record.status
            if status=='desabled':
                commentaire="A supprimer"
            else:
                commentaire="A garder"
        except AdMPReport.DoesNotExist:
            # Si le username n'existe pas dans Adm, mettre à jour status avec "not found" 6 
            commentaire="A supprimer, non présent dans l'AD"
        
        # Mettre à jour l'enregistrement Status avec la valeur de status récupérée
        status_record.commentaire = commentaire
        status_record.save()


def update_status(request):
    # Appeler la fonction pour mettre à jour les status depuis Adm
    update_status_from_adm()

    # Récupérer tous les enregistrements mis à jour du modèle Status
    updated_status_records = ADStatus.objects.all()

    # return render(request, 'status_update_result.html', {'updated_status_records': updated_status_records})
    return redirect("status")


def insert_admp(request):
    if request.method == 'POST' and request.FILES.get('file'):
        form = UploadADForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            # Vérifier si le fichier est un fichier Excel ou CSV
            if file.name.endswith('.xls') or file.name.endswith('.xlsx'):
                try:
                    # Utiliser pandas pour lire les données du fichier Excel
                    donnees = pd.read_excel(file)
                except Exception as e:
                    return HttpResponse("Erreur lors de la lecture du fichier Excel : {}".format(e))
            elif file.name.endswith('.csv'):
                try:
                    # Utiliser pandas pour lire les données du fichier CSV
                    donnees = pd.read_csv(file)
                except Exception as e:
                    return HttpResponse("Erreur lors de la lecture du fichier CSV : {}".format(e))
            else:
                return HttpResponse("Le fichier doit être au format Excel ou CSV.")
            
            # Connexion à la base de données MySQL
            try:

                connection = connect_to_database()

                if connection.is_connected():
                    print("Connexion à la base de données MySQL réussie.")
                    inserer_admp_data(connection, donnees)
                    connection.close()
                    print("Connexion à la base de données MySQL fermée.")
            except mysql.connector.Error as e:
                print("Erreur lors de la connexion à la base de données MySQL :", e)
                return HttpResponse("Erreur lors de la connexion à la base de données MySQL")
            except Exception as e:
                print("Une erreur s'est produite lors de l'insertion des données dans la base de données MySQL :", e)
                return HttpResponse("Une erreur s'est produite lors de l'insertion des données dans la base de données MySQL")
            
            return redirect('adfile')
    else:
        form = UploadADForm()
    return render(request, 'AddFileAD.html', {'form': form})


def export_status_desabled(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="ElementsASupprimer.csv"'

    # Créer un ensemble pour stocker les identifiants uniques
    unique_ids = set()

    # Récupérer les enregistrements à supprimer depuis la base de données SQL
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, username, name, commentaire 
            FROM website_adstatus
            WHERE commentaire!='A garder'
        """)
        records_sql = cursor.fetchall()

        # Ajouter les identifiants SQL à l'ensemble
        for record_sql in records_sql:
            unique_ids.add(record_sql[0])  # On suppose que le premier élément de chaque tuple est l'identifiant

    # Récupérer les enregistrements à supprimer depuis la base de données Django
    records_to_delete = ADStatus.objects.exclude(commentaire='A garder')

    # Ajouter les identifiants Django à l'ensemble, en évitant les doublons
    for record_django in records_to_delete:
        if record_django.id not in unique_ids:
            unique_ids.add(record_django.id)

    # Récupérer les enregistrements correspondant aux identifiants uniques
    records_to_write = []
    for record_id in unique_ids:
        # Recherchez d'abord dans les enregistrements SQL
        for record_sql in records_sql:
            if record_sql[0] == record_id:  # Si l'identifiant correspond
                records_to_write.append(record_sql)
                break
        else:
            # Sinon, recherchez dans les enregistrements Django
            for record_django in records_to_delete:
                if record_django.id == record_id:  # Si l'identifiant correspond
                    records_to_write.append([record_django.id, record_django.username, record_django.name, record_django.commentaire])
                    break

    # Écrire les enregistrements dans le fichier CSV
    writer = csv.writer(response, delimiter=",")
    writer.writerow(['ID', 'Username', 'Name', 'commentaire'])
    for record in records_to_write:
        writer.writerow(record)

    return response


def export_status_gnoc(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="records_gnoc.csv"'

    # Récupérer les enregistrements GNOC depuis la base de données Django
    records_gnoc = ADStatus.objects.filter(username__regex=r'^[a-zA-Z]{4}\d{4}$', status='enabled')

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, username, name, commentaire FROM website_adstatus WHERE username REGEXP '^[a-zA-Z]{4}[0-9]{4}$'"
        )
        records_sql = cursor.fetchall()

    # Créer un ensemble pour stocker les identifiants uniques
    unique_ids = set()

    # Ajouter les enregistrements SQL à l'ensemble des identifiants
    for record_sql in records_sql:
        unique_ids.add(record_sql[0])  # On suppose que le premier élément de chaque tuple est l'identifiant

    # Ajouter les enregistrements Django à l'ensemble des identifiants
    for record_django in records_gnoc:
        unique_ids.add(record_django.id)

    # Récupérer les enregistrements correspondant aux identifiants uniques
    records_to_write = []
    for record_id in unique_ids:
        # Recherchez d'abord dans les enregistrements SQL
        for record_sql in records_sql:
            if record_sql[0] == record_id:  # Si l'identifiant correspond
                records_to_write.append(record_sql)
                break
        else:
            # Sinon, recherchez dans les enregistrements Django
            for record_django in records_gnoc:
                if record_django.id == record_id:  # Si l'identifiant correspond
                    records_to_write.append([record_django.id, record_django.username, record_django.name, record_django.commentaire])
                    break

    # Écrire les enregistrements dans le fichier CSV
    writer = csv.writer(response, delimiter=",")
    writer.writerow(['ID', 'Username', 'Name', 'Commentaire'])
    for record in records_to_write:
        writer.writerow(record)

    return response


def export_tmp_status(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="records_tmp.csv"'

    # Récupérer les enregistrements à supprimer depuis la base de données SQL
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, username, name, commentaire FROM website_adstatus WHERE ((LOWER(username) LIKE 'tmp%' OR  LOWER(username) LIKE 'ext%' OR LOWER(username) LIKE 'stg%' OR LOWER(username) LIKE 'Int%') and commentaire='A garder' )"
        )
        records_sql = cursor.fetchall()

    # Récupérer les enregistrements à supprimer depuis la base de données Django
    records_tmp = ADStatus.objects.filter(
        username__istartswith="tmp",
    ).filter(
        username__istartswith="ext"
    ).filter(
        username__istartswith="INT"
    ).exclude(commentaire__istartswith="A supprimer")

    # Créer un dictionnaire pour stocker les enregistrements avec l'identifiant comme clé
    records_dict = {}

    # Ajouter les enregistrements SQL dans le dictionnaire
    for record_sql in records_sql:
        records_dict[record_sql[0]] = record_sql

    # Ajouter les enregistrements Django dans le dictionnaire en évitant les doublons
    for record_tmp in records_tmp:
        if record_tmp.id not in records_dict:
            records_dict[record_tmp.id] = [record_tmp.id, record_tmp.username, record_tmp.status, record_tmp.commentaire]

    # Écrire les enregistrements dans le fichier CSV
    writer = csv.writer(response, delimiter=",")
    writer.writerow(['ID', 'Username', 'Name', 'Commentaire'])
    for record in records_dict.values():
        writer.writerow(record)

    return response


def export_status_desc(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="records_desc.csv"'

    # Récupérer les enregistrements à supprimer depuis la base de données SQL
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, username, name, commentaire FROM website_adstatus WHERE (LOWER(username) LIKE 'pcci%' OR LOWER(username) LIKE 'stl%' OR LOWER(username) LIKE '1431%' OR LOWER(username) LIKE '1413%' OR LOWER(username) LIKE 'ksv%' OR LOWER(username) LIKE 'w2c%' OR LOWER(username) LIKE 'pop_%' OR LOWER(username) LIKE 'pdist%' OR LOWER(username) LIKE 'sitel%' OR LOWER(username) LIKE 'psup%')"
        )
        records_sql = cursor.fetchall()

    # Récupérer les enregistrements à supprimer depuis la base de données Django
        records_to_delete = ADStatus.objects.filter(
       username__istartswith="pcci",
    ).filter(
        username__istartswith="stl"
    ).filter(
        username__istartswith="1431"
    ).filter(
        username__istartswith="1413"
    ).filter(
        username__istartswith="ksv"
    ).filter(
        username__istartswith="w2c"
    ).filter(
        username__istartswith="pop_"
    ).filter(
        username__istartswith="pdist"
    ).filter(
        username__istartswith="sitel"
    ).filter(
        username__istartswith="psup"
    )


    # Créer un dictionnaire pour stocker les enregistrements avec l'identifiant comme clé
    records_dict = {}

    # Ajouter les enregistrements SQL dans le dictionnaire
    for record_sql in records_sql:
        records_dict[record_sql[0]] = record_sql

    # Ajouter les enregistrements Django dans le dictionnaire en évitant les doublons
    for record_django in records_to_delete:
        if record_django.id not in records_dict:
            records_dict[record_django.id] = [record_django.id, record_django.username, record_django.name, record_django.commentaire]

    # Écrire les enregistrements dans le fichier CSV
    writer = csv.writer(response, delimiter=",")
    writer.writerow(['ID', 'Username', 'Name', 'commentaire'])
    for record in records_dict.values():
        writer.writerow(record)

    return response


def temporaire_drh(request):

    # Récupérer tous les enregistrements
    tmp_records = TemporaireDRH.objects.all()

    # Pagination
    paginator = Paginator(tmp_records, 100)  # 10 enregistrements par page
    page_number = request.GET.get('page')
    try:
        tmp_records = paginator.page(page_number)
    except PageNotAnInteger:
        # Si le numéro de page n'est pas un entier, afficher la première page
        tmp_records = paginator.page(1)
    except EmptyPage:
        # Si la page est vide, afficher la dernière page
        tmp_records = paginator.page(paginator.num_pages)

    # Mettre en forme les enregistrements pour les inclure dans le contexte
    tmp_all_records = []
    for tmp_record in tmp_records:
        tmp_all_records.append({
            'username': tmp_record.username,
            'id': tmp_record.id,
            'date_end': tmp_record.date_end.strftime('%Y-%m-%d'),
        })

    context = {
        'tmp_all_records': tmp_all_records,
    }
    

    # Rendre la page d'accueil avec le contexte et les enregistrements paginés
    return render(request, 'TemporaireDRH.html', {**context, 'tmp_records': tmp_records})


def inserer_data_tmp_drh(connection, donnees_csv):
    cursor = connection.cursor()
    try:
        for index, row in donnees_csv.iterrows():
            try:
                # Insérer les données de base
                cursor.execute("INSERT INTO website_temporairedrh (created_at, username, date_end) VALUES (%s, %s, %s)",
                               (timezone.now(), row['username'], parser.parse(row['date_end']).strftime("%Y-%m-%d")))
            except mysql.connector.Error as e:
                if e.errno == 1062:  # Duplicate entry error
                    # Récupérer la dernière valeur pour le nom d'utilisateur
                    cursor.execute("SELECT * FROM website_temporairedrh WHERE username = %s ORDER BY id DESC LIMIT 1",
                                   (row['username'],))
                    last_row = cursor.fetchone()
                    # Mettre à jour la dernière valeur avec les nouvelles données
                    cursor.execute("UPDATE website_temporairedrh SET created_at = %s, date_end = %s WHERE id = %s",
                                   (timezone.now(), parser.parse(row['date_end']).strftime("%Y-%m-%d"), last_row[0]))
                    print("L'entrée avec le même nom d'utilisateur a été mise à jour.")
                else:
                    raise  # Renvoyer l'erreur si ce n'est pas une erreur de duplication
        # Commit après toutes les opérations
        connection.commit()
        print("Données insérées avec succès.")
    except mysql.connector.Error as e:
        print("Erreur lors de l'insertion des données :", e)
        connection.rollback()
    finally:
        cursor.close()
        connection.close()


def insert_tmp_drh(request):
    if request.method == 'POST' and request.FILES.get('file'):
        form = UploadTmpDRHForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            # Vérifier si le fichier est un fichier Excel ou CSV
            if file.name.endswith('.xls') or file.name.endswith('.xlsx'):
                try:
                    # Utiliser pandas pour lire les données du fichier Excel
                    donnees = pd.read_excel(file)
                except Exception as e:
                    return HttpResponse("Erreur lors de la lecture du fichier Excel : {}".format(e))
            elif file.name.endswith('.csv'):
                try:
                    # Utiliser pandas pour lire les données du fichier CSV
                    donnees = pd.read_csv(file)
                except Exception as e:
                    return HttpResponse("Erreur lors de la lecture du fichier CSV : {}".format(e))
            else:
                return HttpResponse("Le fichier doit être au format Excel ou CSV.")
            
            # Connexion à la base de données MySQL
            try:

                connection = connect_to_database()

                if connection.is_connected():
                    print("Connexion à la base de données MySQL réussie.")
                    inserer_data_tmp_drh(connection, donnees)
                    connection.close()
                    print("Connexion à la base de données MySQL fermée.")
            except mysql.connector.Error as e:
                print("Erreur lors de la connexion à la base de données MySQL :", e)
                return HttpResponse("Erreur lors de la connexion à la base de données MySQL")
            except Exception as e:
                print("Une erreur s'est produite lors de l'insertion des données dans la base de données MySQL :", e)
                return HttpResponse("Une erreur s'est produite lors de l'insertion des données dans la base de données MySQL")
            return redirect('temporaire_drh')
    else:
        form = UploadTmpDRHForm()
    return render(request, 'adtemporairefile.html', {'form': form})


def extraire_chiffres_dans_ordre(mot):
    chiffres = re.findall(r'\d', mot)  # Utilisation d'une expression régulière pour trouver tous les chiffres dans le mot
    chiffres_dans_ordre = ''.join(chiffres)  # Joindre les chiffres trouvés dans l'ordre
    return chiffres_dans_ordre


def update_status_from_temporaireDRH():
    # Récupérer tous les enregistrements du modèle Status
    status_records = ADStatus.objects.filter(
        username__istartswith="tmp"
    ) | ADStatus.objects.filter(
        username__istartswith="ext"
    ) | ADStatus.objects.filter(
        username__istartswith="INT"
    )

    # Parcourir chaque enregistrement de status_records
    for status_record in status_records:
        username = status_record.username
        commentaire = ""


        # Vérifier si le username existe dans le modèle TemporaireDRH
        try:
            tmp_record = TemporaireDRH.objects.get(username=username)
            # matricule_rh = extraire_chiffres_dans_ordre(tmp_record.username)
            # matricule_etrx = extraire_chiffres_dans_ordre(username)

            date_end = tmp_record.date_end

            # Comparaison des matricules extraitsh
            if date_end < date.today():
                commentaire = "Fin de contrat, à supprimer"
            else:
                commentaire = "A garder"

        except TemporaireDRH.DoesNotExist:
            # Si le username n'existe pas dans TemporaireDRH, mettre à jour le commentaire avec "Non trouvé"
            commentaire = "À supprimer, non présent dans L'AD 2024"

        # Mettre à jour le commentaire dans l'enregistrement Status
        status_record.commentaire = commentaire  
        status_record.save()


def update_status_tmp(request):
    # Appeler la fonction pour mettre à jour les status depuis Adm
    update_status_from_temporaireDRH()

    # Récupérer tous les enregistrements mis à jour du modèle Status
    updated_status_records =ADStatus.objects.filter(
        username__istartswith="tmp",
    ).filter(
        username__istartswith="ext"
    ).filter(
        username__istartswith="INT"
    )

    updated_date_records =Record.objects.filter(
        username__istartswith="tmp",
    ).filter(
        username__istartswith="ext"
    ).filter(
        username__istartswith="INT"
    )

    # return render(request, 'DrhUpdate.html', {'updated_status_records': updated_status_records,'updated_date_records': updated_date_records})
    return redirect("status")


def supprimer_toutes_donnees(request):
    # Supprimer toutes les données de votre modèle
    Record.objects.all().delete()
    AdMPReport.objects.all().delete()
    ADStatus.objects.all().delete()
    TemporaireDRH.objects.all().delete()
    # Rediriger vers une page de confirmation ou une autre page de votre choix
    return redirect('welcome')

def supprimer_record_data(request):
    # Supprimer toutes les données de votre modèle
    Record.objects.all().delete()

    return redirect('home')

def supprimer_tmp_data(request):
    # Supprimer toutes les données de votre modèle
    TemporaireDRH.objects.all().delete()

    return redirect('temporaire_drh')

def supprimer_status_data(request):
    # Supprimer toutes les données de votre modèle
    ADStatus.objects.all().delete()

    return redirect('status')

def supprimer_ad_data(request):
    # Supprimer toutes les données de votre modèle
    AdMPReport.objects.all().delete()

    return redirect('adfile')


def export_status_actif(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="records_to_statuts_actifs.csv"'

    # Récupérer les enregistrements actifs depuis la base de données Django
    records_actifs = ADStatus.objects.filter(commentaire='A garder').values_list('id', 'username', 'name', 'commentaire')

    # Écrire les enregistrements dans le fichier CSV
    writer = csv.writer(response, delimiter=",")
    writer.writerow(['ID', 'Username', 'Name', 'Commentaire'])

    for record in records_actifs:
        writer.writerow(record)

    return response

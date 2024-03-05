from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import SignUpForm, AddRecordForm, UpdateDetailsForm, FilterForm
from .models import Record
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import os
import tempfile
import xlrd
from django.http import HttpResponse
import csv
from django.db import connection
import mysql.connector
import pandas as pd
import csv
from io import TextIOWrapper
from .forms import UploadCSVForm
from io import StringIO
from dateutil.relativedelta import relativedelta
import re
from django.utils import timezone

def home(request):
    now = datetime.now().date()

    # Calculer la date d'il y a trois mois
    # Approximation de trois mois à 30 jours chacun
    three_months_ago = now - timedelta(days=3*30)

    # Récupérer tous les enregistrements
    records = Record.objects.all()

    # Pagination
    paginator = Paginator(records, 8)  # 10 enregistrements par page
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
    record_to_statuts = []
    records_tmp = []
    records_gnoc = []
    records_desk = []
    for record in records:
        all_records.append({
            'username': record.username,
            'email': record.email,
            'statuts': record.statuts,
            'id': record.id,
            'last_connected': record.last_connected.strftime('%Y-%m-%d'),
            'commentaire': record.commentaire
        })
        # Vérifier si l'enregistrement doit être supprimé
        if record.last_connected < three_months_ago or record.statuts == 'inactif':
            record_to_delete.append(record.id)
        if record.statuts == "active":
            record_to_statuts.append(record.id)

    context = {
        'three_months_ago': three_months_ago,
        'all_records': all_records,
        'record_to_delete': record_to_delete,
        'record_to_statuts': record_to_statuts,
        'records_tmp': records_tmp
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


def customer_record(request, pk):
    if request.user.is_authenticated:
        customer_record = Record.objects.get(id=pk)
        return render(request, 'record.html', {'customer_record': customer_record})
    else:
        messages.success(request, "You Must Be Logged In To View That Page...")
        return redirect(home)


def delete_record(request, pk):
    if request.user.is_authenticated:
        delete_it = Record.objects.get(id=pk)
        delete_it.delete()
        messages.success(request, "Record Deleted Successfully...")
        return redirect('home')
    else:
        messages.success(request, "You Must Be Logged In To Do That...")
        return redirect('home')


def add_record(request):
    form = AddRecordForm(request.POST or None)
    if request.user.is_authenticated:
        if request.method == "POST":
            if form.is_valid():
                add_record = form.save()
                messages.success(request, "Record Added...")
                return redirect('home')
        return render(request, 'add_record.html', {'form': form})
    else:
        messages.success(request, "You Must Be Logged In...")
        return redirect('home')


def update_record(request, pk):
    if request.user.is_authenticated:
        current_record = Record.objects.get(id=pk)
        form = AddRecordForm(request.POST or None, instance=current_record)
        if form.is_valid():
            form.save()
            messages.success(request, "Record Has Been Updated!")
            return redirect('home')
        return render(request, 'update_record.html', {'form': form})
    else:
        messages.success(request, "You Must Be Logged In...")
        return redirect('home')


def difference_date(request):
    instances = Record.objects.all()
    for instance in instances:
        instance.difference = instance.difference_date()
    return render(request, 'votre_template.html', {'instances': instances})


def update_details(request):
    message = ''

    if request.method == 'POST':
        form = UpdateDetailsForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']

            # Créez un fichier temporaire pour stocker le contenu du fichier Excel
            fd, tmp = tempfile.mkstemp()
            with os.fdopen(fd, 'w') as out:
                out.write(excel_file.read())

            # Ouvrez le fichier Excel avec xlrd
            book = xlrd.open_workbook(tmp)
            sh = book.sheet_by_index(0)

            # Parcourez les lignes du fichier Excel et enregistrez les données dans votre modèle
            for rx in range(1, sh.nrows):
                obj = Record(
                    user_id=str(sh.row(rx)[0].value),
                    created_at=str(sh.row(rx)[1].value),
                    username=str(sh.row(rx)[2].value),
                    first_name=str(sh.row(rx)[3].value),
                    last_name=str(sh.row(rx)[4].value),
                    email=str(sh.row(rx)[5].value),
                    statuts=str(sh.row(rx)[6].value),
                    last_connected=str(sh.row(rx)[7].value),
                    # Ajoutez d'autres champs selon votre modèle
                )
                obj.save()

            os.unlink(tmp)  # Supprimez le fichier temporaire

            message = 'Données importées avec succès !'
        else:
            message = 'Entrées invalides'
    else:
        form = UpdateDetailsForm()

    return render(request, 'update_details.html', {'form': form, 'message': message})


def extract_data(request):
    if request.method == 'POST':
        form = FilterForm(request.POST)
        if form.is_valid():
            filter_choice = form.cleaned_data['filter_choice']
            if filter_choice == 'GNOC':
                extracted_data = Record.objects.filter(category='Category1')
            elif filter_choice == 'DESC':
                extracted_data = Record.objects.filter(category='Category2')
            # Ajoutez d'autres conditions pour d'autres filtres au besoin
            else:
                extracted_data = None  # Aucun filtre sélectionné

            return render(request, 'results.html', {'data': extracted_data})
    else:
        form = FilterForm()
    return render(request, 'extract_data.html', {'form': form})


def export_to_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="ElementsASupprimer.csv"'

    # Récupérer les enregistrements à supprimer depuis la base de données
    records_to_delete = Record.objects.filter(
        statuts="inactive")  # Adapter selon votre modèle

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, username, email, last_name, statuts, last_connected, commentaire 
            FROM website_record 
            WHERE (username NOT REGEXP CONCAT('^', last_name, '[0-9]{4,}$') 
            AND last_connected < DATE_SUB(CURDATE(), INTERVAL 1 MONTH)) 
            OR (username REGEXP CONCAT('^', last_name, '[0-9]{4,}$') 
            AND last_connected < DATE_SUB(CURDATE(), INTERVAL 3 MONTH)) 
            OR statuts='inactif'
        """)
        records = cursor.fetchall()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="ElementsASupprimer.csv"'

    writer = csv.writer(response, delimiter=",")
    writer.writerow(['ID', 'Username', 'Email','last_name',
                     'status', 'Last Connected Date','commentaire'])
    for record in records:
        writer.writerow(record)

    for record in records_to_delete:
        writer.writerow([record.id, record.username, record.email,record.last_name,
                         record.statuts, record.last_connected,record.commentaire])

    return response


def export_actif(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="records_to_statuts.csv"'

    # Récupérer les enregistrements à supprimer depuis la base de données
    records_statuts = Record.objects.filter(
        statuts="inactive")  # Adapter selon votre modèle

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id,username,email,statuts,last_connected FROM website_record WHERE last_connected > DATE_SUB(CURDATE(), INTERVAL 3 MONTH) and statuts='actif' ")
        records = cursor.fetchall()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="records_to_statuts.csv"'

    writer = csv.writer(response, delimiter=",")
    writer.writerow(['ID', 'Username', 'Email',
                     'Last Connected Date'])
    for record in records:
        writer.writerow(record)

    for record in records_statuts:
        writer.writerow([record.id, record.username, record.email,
                         record.last_connected])

    return response


def export_to_gnoc(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="records_gnoc.csv"'

    # Récupérer les enregistrements à supprimer depuis la base de données
    records_gnoc = Record.objects.filter(
        statuts="inactive")  # Adapter selon votre modèle

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id,username,email,statuts,last_connected,commentaire FROM website_record WHERE username REGEXP '[a-zA-Z]{4}[0-9]{4}' and last_connected > DATE_SUB(CURDATE(), INTERVAL 1 MONTH) and statuts!='inactif'")
        records = cursor.fetchall()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="records_gnoc.csv"'

    writer = csv.writer(response, delimiter=",")
    writer.writerow(['ID', 'Username', 'Email', 'Statuts','Last Connected Date','commentaire'])
    for record in records:
        writer.writerow(record)

    for record in records_gnoc:
        writer.writerow([record.id, record.username, record.email,
                        record.statuts,record.last_connected,record.commentaire])

    return response


def export_tmp(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="records_tmp.csv"'

    # Récupérer les enregistrements à supprimer depuis la base de données
    records_tmp = Record.objects.filter(
        statuts="inactive")   # Adapter selon votre modèle

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id,username,email,statuts,last_connected,commentaire FROM website_record WHERE (LOWER(username) LIKE 'tmp%' OR  LOWER(username) LIKE 'ext%' OR LOWER(username) LIKE 'stg%' OR LOWER(username) LIKE 'Int%') and last_connected > DATE_SUB(CURDATE(), INTERVAL 1 MONTH) and statuts!='inactif'")
        records = cursor.fetchall()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="records_tmp.csv"'

    writer = csv.writer(response, delimiter=",")
    writer.writerow(['ID', 'Username', 'Email', 'Statuts','Last Connected Date','commentaire'])
    for record in records:
        writer.writerow(record)

    for record in records_tmp:
        writer.writerow([record.id, record.username, record.email,
                        record.statuts,record.last_connected, record.commentaire])

    return response


def export_to_desk(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="records_desk.csv"'

    # Récupérer les enregistrements à supprimer depuis la base de données
    records_to_delete = Record.objects.filter(
        statuts="inactive")  # Adapter selon votre modèle

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id,username,email,statuts,last_connected,commentaire FROM website_record WHERE (LOWER(username) LIKE 'pcci%' OR LOWER(username) LIKE 'stl%' OR LOWER(username) LIKE '1431%' OR LOWER(username) LIKE '1413%' OR LOWER(username) LIKE 'ksv%' OR LOWER(username) LIKE 'w2c%' OR LOWER(username) LIKE 'pop_%' OR LOWER(username) LIKE 'pdist%' OR LOWER(username) LIKE 'sitel%' OR LOWER(username) LIKE 'psup%') and last_connected > DATE_SUB(CURDATE(), INTERVAL 1 MONTH) and statuts!='inactif'")
        records = cursor.fetchall()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="records_desk.csv"'

    writer = csv.writer(response, delimiter=",")
    writer.writerow(['ID', 'Username', 'Email',
                    'statuts', 'Last Connected Date','commentaire'])
    for record in records:
        writer.writerow(record)

    for record in records_to_delete:
        writer.writerow([record.id, record.username,
                        record.email,record.statuts ,record.last_connected,record.commentaire])

    return response


def inserer_donnees(connection, donnees_csv):
    cursor = connection.cursor()
    try:
        for index, row in donnees_csv.iterrows():
            # Insérer les données de base
            cursor.execute("INSERT INTO website_record (created_at, username, first_name, last_name, email, statuts, last_connected) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                           (timezone.now(), row['username'], row['first_name'], row['last_name'], row['email'], row['statuts'], row['last_connected']))
            
            # Récupérer la date de la dernière connexion
            last_connected = row['last_connected']
            statuts = row['statuts']
            # Convertir la date de la dernière connexion en objet datetime
            last_connected_date = datetime.strptime(last_connected, "%Y-%m-%d")
            
            # Définir la durée pour les commentaires en fonction du username
            if re.match(f"^{row['last_name']}[0-9]{{4,}}$", row['username']):
                comment_interval = relativedelta(months=3)  # 3 mois pour les utilisateurs internes
            else:
                comment_interval = relativedelta(months=1)  # 1 mois par défaut
            
            # Comparer la date de la dernière connexion avec la durée pour les commentaires
            if last_connected_date < datetime.now() - comment_interval:
                comment = "Utilisateur inactif depuis plus de {} mois".format(comment_interval.months)
            elif statuts=='inactif':
                comment = "Utilisateur inactif"
            else:
                comment = "Utilisateur actif"

            # Mettre à jour le commentaire dans la base de données
            cursor.execute("UPDATE website_record SET commentaire = %s WHERE username = %s", (comment, row['username']))
        
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
    if request.method == 'POST' and request.FILES.get('csv_file'):
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            decoded_file = csv_file.read().decode('utf-8')
            
            try:
                # Convertir le contenu décodé en un objet StringIO
                csv_data = StringIO(decoded_file)
                # Utiliser pandas pour lire les données CSV
                donnees_csv = pd.read_csv(csv_data)
                
                connection = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="admin",
                    database="fiabliz"
                )
                if connection.is_connected():
                    print("Connexion à la base de données MySQL réussie.")
                    inserer_donnees(connection, donnees_csv)
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
    return render(request, 'test.html', {'form': form})


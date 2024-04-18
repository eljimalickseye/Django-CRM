from django.db import models
from django.utils import timezone

class Record(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    username = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    last_connected = models.DateField(null=True, blank=True)
    commentaire = models.CharField(max_length=200, null=True)
    traitement = models.CharField(max_length=200, null=True)

    class Meta:
        # Ajouter des contraintes ou des index si nécessaire
        verbose_name = "Record"
        verbose_name_plural = "Records"

    def __str__(self):
        return self.username

    # Exemple de méthode utilitaire
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    

class AdMPReport(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    first_name = models.CharField(max_length=100,null=True)
    last_name = models.CharField(max_length=100,null=True)
    full_name = models.CharField(max_length=100,null=True)
    display_name = models.CharField(max_length=100,null=True)
    sam_account_name = models.CharField(max_length=50, null=True) #username
    email_address = models.CharField(max_length=100, null=True)
    account_status = models.CharField(max_length=50,null=True) #status
    initials= models.CharField(max_length=50, null=True)

    class Meta:
        # Ajouter des contraintes ou des index si nécessaire
        verbose_name = "AdMPReport"
        verbose_name_plural = "AdMPReports"
    
    def __str__(self):
        return self.sam_account_name
    

class ADStatus(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    username = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=50)
    commentaire = models.CharField(max_length=200, null=True)


    class Meta:
        # Ajouter des contraintes ou des index si nécessaire
        verbose_name = "ADStatus"
        verbose_name_plural = "ADStatus"
    
    def __str__(self):
        return self.username
    

class TemporaireDRH(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    username = models.CharField(max_length=50, unique=True)
    date_end = models.DateField(null=True, blank=True)

    class Meta:
        # Ajouter des contraintes ou des index si nécessaire
        verbose_name = "TemporaireDRH"
        verbose_name_plural = "TemporairesDRH"

    def __str__(self):
        return self.username

    # Exemple de méthode utilitaire
    def get_full_name(self):
        return f"{self.username}"


# EXTRACTION DE NAC

class Extraction_nac(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    Name = models.CharField(max_length=50, unique=True)
    Password = models.CharField(max_length=50)
    Profile = models.CharField(max_length=50)
    Locale = models.CharField(max_length=50)
    Description = models.CharField(max_length=100)
    UserType = models.CharField(max_length=50)
    PasswordUpdateDate = models.DateTimeField(null=True, blank=True)
    MailAddress = models.CharField(max_length=200, null=True)
    commentaire = models.CharField(max_length=200, null=True)

    class Meta:
        # Ajouter des contraintes ou des index si nécessaire
        verbose_name = "Extraction_nac"
        verbose_name_plural = "Extraction_nacs"

    def __str__(self):
        return self.Name

    # Exemple de méthode utilitaire
    def get_full_name(self):
        return f"{self.Name}"
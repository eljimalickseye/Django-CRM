from django.db import models
from django.utils import timezone

class Record(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    username = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    last_connected = models.DateField(null=True, blank=True)
    commentaire = models.CharField(max_length=200, null=True)

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
    username = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=50)

    class Meta:
        # Ajouter des contraintes ou des index si nécessaire
        verbose_name = "AdMPReport"
        verbose_name_plural = "AdMPReports"
    
    def __str__(self):
        return self.username
    

class ADStatus(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    username = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=50)
    status = models.CharField(max_length=50, null=True)
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

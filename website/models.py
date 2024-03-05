from django.db import models
from django.utils import timezone

class Record(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    username = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=100)
    last_connected = models.DateField(null=True)
    statuts = models.CharField(max_length=20, null=True)
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

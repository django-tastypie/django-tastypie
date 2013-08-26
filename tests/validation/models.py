from django.db import models


class ValidatedModel(models.Model):
    content = models.CharField(max_length=20)

    def save(self, *args, **kwargs):
        self.full_clean()
        super(ValidatedModel, self).save(*args, **kwargs)

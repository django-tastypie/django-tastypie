from django.db import models


class ValidatedModel(models.Model):
    """
    Simple model that runs its own validation on save().
    """

    content = models.CharField(max_length=20)

    def save(self, *args, **kwargs):
        self.full_clean()
        super(ValidatedModel, self).save(*args, **kwargs)

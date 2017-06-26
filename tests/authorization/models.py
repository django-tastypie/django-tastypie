from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models
from django.template.defaultfilters import slugify
from tastypie.utils.timezone import now


class AuthorProfile(models.Model):
    user = models.OneToOneField(User, related_name='author_profile',
                                on_delete=models.CASCADE)
    short_bio = models.CharField(max_length=255, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    # We'll use the ``sites`` the author is assigned to as a way to control
    # the permissions.
    sites = models.ManyToManyField(Site, related_name='author_profiles')

    def __unicode__(self):
        return u"Profile: {0}".format(self.user.username)


class Article(models.Model):
    # We'll also use the ``authors`` to control perms.
    authors = models.ManyToManyField(AuthorProfile, related_name='articles')
    title = models.CharField(max_length=255)
    slug = models.SlugField(blank=True)
    content = models.TextField(blank=True, default='')
    added_on = models.DateTimeField(default=now)

    def __unicode__(self):
        return u"{0} - {1}".format(self.title, self.slug)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        return super(Article, self).save(*args, **kwargs)

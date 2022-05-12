from django.db import models


class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    image = models.ImageField(upload_to='post_images')

    def __str__(self):
        return self.title


class SearchRequest(models.Model):
    id = models.TextField(primary_key=True)
    archive = models.FileField(upload_to='uploads/')
    keywords = models.TextField(default="")

class Todo(models.Model):
    title = models.CharField(max_length=120)
    description = models.TextField()
    completed = models.BooleanField(default=False)

    def _str_(self):
        return self.title


class Details:
    def __init__(self, content):
        self.content = content


class Entry:
    def __init__(self, lvl, title, page, dest):
        self.lvl = lvl
        self.title = title
        self.page = page
        self.dest = dest
# Create your models here.

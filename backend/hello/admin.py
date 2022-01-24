from django.contrib import admin
from .models import Todo
from .models import Post


class TodoAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'completed')


# Register your models here.


admin.site.register(Todo, TodoAdmin)
admin.site.register(Post)
# Register your models here.

from django.contrib import admin

from .models import Post, Vote, Profile


admin.site.register(Post)
admin.site.register(Vote)
admin.site.register(Profile)

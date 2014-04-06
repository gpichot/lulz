from django.contrib import admin

from .models import Post, Vote, User, Group


admin.site.register(Post)
admin.site.register(Vote)
admin.site.register(User)
admin.site.register(Group)

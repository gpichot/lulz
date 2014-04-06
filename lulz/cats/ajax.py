import json

from django.shortcuts import get_object_or_404
from django.db.models import Count, Q

from dajaxice.decorators import dajaxice_register

from taggit.models import Tag

from .strates import detect_input, strate
from .models import Post, Vote, Group, User

@dajaxice_register
def suggest(request, url):
    return json.dumps(strate(url))

@dajaxice_register
def upvote(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.add_vote(Vote.UP, request.user)

    return json.dumps({'pk': post.pk, 'likes': post.likes, })
    
@dajaxice_register
def downvote(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.add_vote(Vote.DOWN, request.user)

    return json.dumps({'pk': post.pk, 'likes': post.likes, })

@dajaxice_register
def chan_list(request):
    chans = Tag.objects.exclude(followers=request.user).annotate(
        nb_followers=Count('followers'), 
        references=Count('post'),
    ).order_by('name').values('name', 'nb_followers', 'references')

    return json.dumps(list(chans))

@dajaxice_register
def user_list(request, pk):
    group = get_object_or_404(Group, pk=pk)

    users = User.objects.exclude(groups=pk).exclude(pk=-1).all().order_by('username').values(
        'username', 'first_name', 'last_name'
    )

    return json.dumps(list(users))

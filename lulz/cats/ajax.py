import json
from dajaxice.decorators import dajaxice_register
from django.shortcuts import get_object_or_404


from .strates import detect_input, strate
from .models import Post, Vote

@dajaxice_register
def suggest(request, url):
    return json.dumps(strate(url))

@dajaxice_register
def upvote(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.add_vote(Vote.UP)

    return json.dumps({'pk': post.pk, 'likes': post.likes, })
    
@dajaxice_register
def downvote(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.add_vote(Vote.DOWN)

    return json.dumps({'pk': post.pk, 'likes': post.likes, })

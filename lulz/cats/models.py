from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now
from django.utils.functional import cached_property

from django.contrib import auth

from mptt.models import MPTTModel, TreeForeignKey

from object_permissions import register

from taggit.managers import TaggableManager
from taggit.models import Tag

from .strates import strate

register(['auth.can_manage_group'], auth.models.Group)

class Post(MPTTModel):
    message = models.TextField(_('Message'), blank=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name="answers")
    url = models.URLField(_('Url'), null=True, blank=True)
    posted_at = models.DateTimeField(_('Posted at'))
    likes = models.IntegerField(_('Vote number'), default=0)
    tags = TaggableManager(blank=True)
    group = models.ForeignKey(auth.models.Group, blank=True, null=True, related_name='posts')
    author = models.ForeignKey(auth.models.User, related_name='posts')

    def __init__(self, *args, **kwargs):
        super(Post, self).__init__(*args, **kwargs)

        if self.pk is None:
            self.posted_at = now()

    def add_vote(self, score):
        # TODO : will need to be updated to update_or_create in future releases
        (vote, created)  = Vote.objects.get_or_create(
            post=self,
        )
        if created or score != vote.score:
            vote.score = score; 
            self.likes += score
            self.save()

    def has_template(self):
        return self.url is not None

    @cached_property
    def metadata(self):
        return self.get_metadata()

    def get_metadata(self):
        return strate(self.url)

    class MPTTMeta:
        order_insertion_by = ['posted_at']

class Vote(models.Model):
    UP = 1
    DOWN = -1
    VOTE_CHOICES = (
        (DOWN, _('Down')),
        (UP, _('Up')),
    )
    post = models.ForeignKey(Post, related_name="votes")
    score = models.SmallIntegerField(_('Is an upvote'), choices=VOTE_CHOICES)
    voted_at = models.DateTimeField(_('Voted at'))
    changed_at = models.DateTimeField(_('Changed at'), blank=True, null=True)

    def __init__(self, *args, **kwargs):
        super(Vote, self).__init__(*args, **kwargs)
        if self.pk is None:
            self.voted_at = now()

    def save(self, *args, **kwargs):
        if self.pk is not None:
            self.changed_at = now()


class Profile(models.Model):
    user = models.OneToOneField(auth.models.User, related_name="profile")
    groups = models.ManyToManyField(auth.models.Group, related_name="members")
    followed_tags = models.ManyToManyField(Tag, related_name="followers")

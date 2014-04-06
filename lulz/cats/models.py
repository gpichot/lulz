from django.db import models
from django.core.urlresolvers import reverse

from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now
from django.utils.functional import cached_property
from django.utils.text import slugify

from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth import get_user_model
from django.contrib.auth.models import UserManager

from mptt.models import MPTTModel, TreeForeignKey

#from object_permissions import register

from taggit.managers import TaggableManager
from taggit.models import Tag

from .strates import strate


class User(models.Model):
    username = models.CharField(_('Username'), max_length=30, unique=True)
    first_name = models.CharField(_('First name'), max_length=30)
    last_name = models.CharField(_('Last name'), max_length=50)
    email = models.EmailField(_('Email'))
    password = models.CharField(_('Password'), max_length=50)
    followed_tags = models.ManyToManyField(Tag, related_name="followers")
    last_login = models.DateTimeField(_('Last login'), null=True)
    is_active = models.BooleanField(_('Is active'), default=True)
    is_superuser = models.BooleanField(_('Is superuser'), default=False)
    
    objects = UserManager()    

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', ]

    def __unicode__(self):
        return self.username

    def check_password(self, raw_password):
        def setter(raw_password):
            self.set_password(raw_password)
            self.save(update_fields=["password"])
        return check_password(raw_password, self.password, setter)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        
    def is_authenticated(self):
        return True

class Group(models.Model):
    name = models.CharField(_('Name'), max_length=140)
    hidden = models.BooleanField(_('Is hidden'), default=True)
    members = models.ManyToManyField(User, related_name='groups')
    
    def __unicode__(self):
        return self.name

    def slug(self):
        return slugify(self.name)

    def get_absolute_url(self):
        return reverse('group-detail', kwargs={
            'pk': self.pk,
            'slug': slugify(self.name),
        })

    class Meta:
        permissions = (
            ('manage_group', 'Manage group'),
        )

class Post(MPTTModel):
    message = models.TextField(_('Message'), blank=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name="answers")
    url = models.URLField(_('Url'), null=True, blank=True)
    posted_at = models.DateTimeField(_('Posted at'))
    likes = models.IntegerField(_('Vote number'), default=0)
    tags = TaggableManager(blank=True)
    group = models.ForeignKey(Group, blank=True, null=True, related_name='posts')
    author = models.ForeignKey(User, related_name='posts')

    def __init__(self, *args, **kwargs):
        super(Post, self).__init__(*args, **kwargs)

        if self.pk is None:
            self.posted_at = now()

    def add_vote(self, score, user):
        # TODO : will need to be updated to update_or_create in future releases
        (vote, created)  = Vote.objects.get_or_create(
            post=self,
            user=user,
        )

        if created or score != vote.score:
            vote.score = score; 
            self.likes += score
            if not created:
                self.likes += score
            vote.save()
            self.save()

    def has_template(self):
        return self.url is not None

    @cached_property
    def metadata(self):
        return self.get_metadata()

    def get_metadata(self):
        return strate(self.url)

    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'pk': self.pk, })

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
    user = models.ForeignKey(User, related_name="votes")
    score = models.SmallIntegerField(_('Is an upvote'), choices=VOTE_CHOICES, default=UP)
    voted_at = models.DateTimeField(_('Voted at'))
    changed_at = models.DateTimeField(_('Changed at'), blank=True, null=True)

    def __init__(self, *args, **kwargs):
        super(Vote, self).__init__(*args, **kwargs)
        if self.pk is None:
            self.voted_at = now()

    def save(self, *args, **kwargs):
        if self.pk is not None:
            self.changed_at = now()
        super(Vote, self).save(*args, **kwargs)

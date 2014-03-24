from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from django.views import generic
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth import logout, login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType

from .forms import PostForm, GroupForm
from .models import Post, Profile


class PostListAndCreateView(generic.CreateView):
    form_class = PostForm
    model = Post
    
    def form_valid(self, form):
        ob = form.save(commit=False)
        ob.author = self.request.user
        ob.save()

        return super(PostListAndCreateView, self).form_valid(form)

    def get_post_queryset(self):
        return Post.objects.filter(parent=None).order_by('-posted_at').select_related('author').prefetch_related('tags').annotate(answers_count=Count('answers'))

    def get_context_data(self, *args, **kwargs):
        context = super(PostListAndCreateView, self).get_context_data(*args, **kwargs)

        context['last_posts'] = self.get_post_queryset()[:20]
        context['answer_form'] = PostForm()

        return context

class Home(PostListAndCreateView):
    template_name = 'cats/home.html'
    
    def dispatch(self, *args, **kwargs):
        if not self.request.user is None:
            return super(Home, self).dispatch(*args, **kwargs)
        else:
            redirect(reverse('hot'))

    def get_post_queryset(self):
        qs = super(Home, self).get_post_queryset()

        return qs.filter(group=None)

    def get_success_url(self, *args, **kwargs):
        return reverse('home')

class HotView(Home):
    
    def get_post_queryset(self):
        qs = super(HotView, self).get_post_queryset()

        return qs.filter(likes__gte=10)

    def get_success_url(self, *args, **kwargs):
        return reverse('hot')

class TrendingView(Home):
    def get_post_queryset(self):
        qs = super(TrendingView, self).get_post_queryset()

        return qs.filter(likes__lt=10)

    def get_success_url(self, *args, **kwargs):
        return reverse('trending')


class TagView(generic.ListView):
    model = Post
    url_tag_name = 'tag'
    context_object_name = 'posts'

    def get_queryset(self, *args, **kwargs):
        qs = super(TagView, self).get_queryset(*args, **kwargs)

        return qs.filter(parent=None, tags__name__in=[self.kwargs.get('tag')])

    def get_context_data(self, *args,**kwargs):
        context = super(TagView, self).get_context_data(*args, **kwargs)

        context['tag'] = self.kwargs.get('tag')

        return context

class FollowedChansView(generic.UpdateView):
    model = Profile
    fields = ('followed_tags', )

    def get_object(self, *args, **kwargs):
        return self.request.user.profile

    def get_success_url(self, *args, **kwargs):
        return reverse('home')

class SignUpView(generic.CreateView):
    template_name = 'cats/sign_up.html'
    form_class = UserCreationForm
    model = User

    def form_valid(self, form):
        ob = form.save()
        ob.profile = Profile()
        ob.profile.save()

        return super(SignUpView, self).form_valid(form)

    def get_success_url(self, *args, **kwargs):
        return reverse('home')

class SignInView(generic.FormView):
    template_name = 'cats/sign_in.html'
    form_class = AuthenticationForm
    
    def form_valid(self, form):
        login(self.request, form.user_cache) 

        return super(SignInView, self).form_valid(form)

    def get_success_url(self, *args, **kwargs):
        messages.success(self.request, _("""You are connected."""))

        return reverse('home')

class LogOutView(generic.RedirectView):
    
    def get_redirect_url(self, *args, **kwargs):
        logout(self.request)
        messages.success(self.request, _("""You are logged out."""))

        return reverse('home')

class GroupView(PostListAndCreateView):
    template_name = 'cats/group_detail.html'

    def get(self, *args, **kwargs):
        self.group = get_object_or_404(Group, 
            pk=self.kwargs.get('pk'),
            user=self.request.user
        )
        return super(GroupView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.group = get_object_or_404(Group, pk=self.kwargs.get('pk'))
        return super(GroupView, self).post(*args, **kwargs)


    def get_post_queryset(self):
        qs = super(GroupView, self).get_post_queryset()

        return qs.filter(group=self.group)

    def form_valid(self, form):
        post = form.save(commit=False)
        post.group = self.group
        post.author = self.request.user

        return super(GroupView, self).form_valid(post)


    def get_context_data(self, *args, **kwargs):
        context = super(GroupView, self).get_context_data(*args, **kwargs)

        context['group'] = self.group

        return context

    def get_success_url(self):
        return reverse('group-detail', kwargs={'pk': self.group.pk, })


class CreateGroupView(generic.CreateView):
    template_name = 'cats/group_create.html'
    form_class = GroupForm
    model = Group

    def form_valid(self, form):
        response = super(CreateGroupView, self).form_valid(form)

        self.object.user_set.add(self.request.user)
        self.object.save()

        self.request.user.grant('auth.can_manage_group', self.object)

        return response


    def get_success_url(self, *args, **kwargs):
        return reverse('home')

from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from django.views import generic
from django.core.urlresolvers import reverse

from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify

from django.contrib.auth import logout, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Permission
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType

from guardian.shortcuts import assign_perm

from .forms import UserForm, AuthenticationForm, PostForm, GroupForm, \
    AddTagForm, AddMemberForm
from .models import Post, User, Group


class PostListAndCreateView(generic.CreateView):
    form_class = PostForm
    model = Post
    
    def form_valid(self, form):

        if not hasattr(form, '_state'):
            ob = form.save(commit=False)
        else:
            ob = form

        ob.author = self.request.user
        ob.save()

        return super(PostListAndCreateView, self).form_valid(form)

    def get_post_queryset(self):
        return Post.objects.filter(parent=None).order_by('-posted_at').select_related('author').prefetch_related('tags')

    def get_context_data(self, *args, **kwargs):
        context = super(PostListAndCreateView, self).get_context_data(*args, **kwargs)

        context['last_posts'] = self.get_post_queryset()[:20]
        context['answer_form'] = PostForm()
        context['only_famous_posts'] = True

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
        if self.request.user.is_authenticated():
            qs = qs.filter(
                Q(group__members=self.request.user)
                | Q(group=None)
            )
        else:
            qs = qs.filter(Q(group=None))

        return qs

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

        return qs.filter(parent=None, tags__name__in=[self.kwargs.get('tag')]).order_by('-posted_at')

    def get_context_data(self, *args,**kwargs):
        context = super(TagView, self).get_context_data(*args, **kwargs)

        context['tag'] = self.kwargs.get('tag')

        return context


class FollowedChansView(generic.FormView):
    form_class = AddTagForm
    template_name = 'cats/tags_add.html'

    def form_valid(self, form):
        ob = form.get_chan()
        self.request.user.followed_tags.add(ob)
        self.request.user.save()

        messages.success(self.request, _(
            'From now, you are following %(chan)s' % {
                'chan': ob,
            }
        ))

        return super(FollowedChansView, self).form_valid(form)

    def get_object(self, *args, **kwargs):
        return self.request.user

    def get_success_url(self, *args, **kwargs):
        return reverse('home')


class SignUpView(generic.CreateView):
    template_name = 'cats/sign_up.html'
    form_class = UserForm
    model = User

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
        self.group = self.request.user.groups.get(
            pk=self.kwargs.get('pk'),
        )
        return super(GroupView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.group = self.request.user.groups.get(
            pk=self.kwargs.get('pk'),
        )
        return super(GroupView, self).post(*args, **kwargs)


    def get_post_queryset(self):
        qs = super(GroupView, self).get_post_queryset()

        return qs.filter(group=self.group)

    def form_valid(self, form):
        post = form.save(commit=False)
        post.group = self.group
        post.author = self.request.user
        post.save()
        for chan in form.cleaned_data['tags']:
            post.tags.add(chan)

        return super(GroupView, self).form_valid(post)


    def get_context_data(self, *args, **kwargs):
        context = super(GroupView, self).get_context_data(*args, **kwargs)

        context['group'] = self.group

        return context

    def get_success_url(self):
        return reverse('group-detail', kwargs={
            'pk': self.group.pk,
            'slug': slugify(self.group.name),
        })


class CreateGroupView(generic.CreateView):
    template_name = 'cats/group_create.html'
    form_class = GroupForm
    model = Group

    def form_valid(self, form):
        response = super(CreateGroupView, self).form_valid(form)

        self.object.members.add(self.request.user)
        self.object.save()

        assign_perm(
            'manage_group', self.request.user, self.object
        )

        return response


    def get_success_url(self, *args, **kwargs):
        return reverse('home')


class GroupMembersView(generic.ListView):
    model = User
    template_name = 'cats/group_members.html'
    context_object_name = 'members'

    def get_queryset(self, *args, **kwargs):
        qs = super(GroupMembersView, self).get_queryset(*args, **kwargs)
        
        self.group = get_object_or_404(Group, pk=self.kwargs.get('pk'))

        return qs.filter(groups=self.group)

    def get_context_data(self, *args, **kwargs):
        cd = super(GroupMembersView, self).get_context_data(*args, **kwargs)

        cd['group'] = self.group

        return cd
class GroupMemberAddView(generic.FormView):
    form_class = AddMemberForm
    template_name = 'cats/group_members_add.html'

    def get(self, *args, **kwargs):
        self.group = get_object_or_404(Group, pk=self.kwargs.get('pk'))

        return super(GroupMemberAddView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.group = get_object_or_404(Group, pk=self.kwargs.get('pk'))

        return super(GroupMemberAddView, self).post(*args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        
        self.group.members.add(user)
        user.save()

        messages.success(self.request, _(
            '%(user)s is now member of the group %(group)s' % {
                'group': self.group,
                'user': user,
            }
        ))

        return super(GroupMemberAddView, self).form_valid(form)

    def get_context_data(self, *args, **kwargs):
        cd = super(GroupMemberAddView, self).get_context_data(*args, **kwargs)
        
        cd['group'] = self.group

        return cd

    def get_success_url(self, *args, **kwargs):
        return reverse('home')

class PostView(generic.FormView):
    form_class = PostForm
    template_name = 'cats/post_detail.html'
    context_object_name = 'form'
    model = Post

    def get_context_data(self, *args, **kwargs):
        cd = super(PostView, self).get_context_data(*args, **kwargs)
        
        cd['post'] = get_object_or_404(Post, pk=self.kwargs.get('pk'))

        return cd

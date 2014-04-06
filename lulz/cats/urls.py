from django.conf.urls import patterns, include, url

from views import Home, TagView, SignUpView, SignInView, LogOutView, \
    CreateGroupView, GroupView, HotView, TrendingView, \
    FollowedChansView, GroupMembersView, GroupMemberAddView, \
    PostView

from dajaxice.core import dajaxice_autodiscover, dajaxice_config
dajaxice_autodiscover()

urlpatterns = patterns('',

    url(r'^$', Home.as_view(), name="home"),

    url(r'^hot$', HotView.as_view(), name="hot"),

    url(r'^trending$', TrendingView.as_view(), name="trending"),

    url(r'^channel/(?P<tag>[\w-]+)$', TagView.as_view(), name="tag"),

    url(r'^post/(?P<pk>\d+)$', PostView.as_view(), name="post-detail"),

    url(r'^user/sign-up$', SignUpView.as_view(), name="user-sign-up"),
     
    url(r'^user/sign-in$', SignInView.as_view(), name="user-sign-in"),
     
    url(r'^user/logout$', LogOutView.as_view(), name="user-log-out"),

    url(r'^user/followed-chans', FollowedChansView.as_view(), name="user-followed-chans"),

    url(r'^group/create$', CreateGroupView.as_view(), name="group-create"),

    url(r'^group/(?P<pk>\d+)/detail/(?P<slug>[\w-]+)$', GroupView.as_view(), name="group-detail"),

    url(
        r'^group/(?P<pk>\d+)/members/(?P<slug>[\w-]+)$',
        GroupMembersView.as_view(),
        name="group-members",
    ),

    url(
        r'^group/(?P<pk>\d+)/members/(?P<slug>[\w-]+)/add$',
        GroupMemberAddView.as_view(),
        name="group-member-add",
    ),

    url(dajaxice_config.dajaxice_url, include('dajaxice.urls')),

)

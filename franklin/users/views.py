from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.views.generic import ListView, TemplateView
from django.shortcuts import redirect, render, render_to_response

from social.apps.django_app.utils import psa

from .helpers import LoginRequiredMixin
from builder.models import Site


class UserLogin(TemplateView):
    """ Login with GitHub

    Extends: TemplateView
    """
    template_name = 'login.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return redirect('user:dashboard')
        next = request.GET.get('next')
        if not next:
            next = reverse('user:dashboard')
        return render(request, self.template_name, 
                      self.get_context_data(next=next))


class UserDashboard(LoginRequiredMixin, ListView):
    """ Placeholder for the future dashboard we will create

    Extends: ListView
    """
    model = Site
    template_name = 'dashboard.html'
    
    def init_user_repos(self):
        if not hasattr(self, 'user_repos') or not hasattr(self, 'active_repos'):
            self.user_repos = self.request.user.details.get_user_repos()
            repo_ids = []
            for repo in self.user_repos:
                repo_ids.append(repo.get('id', ''))
            self.active_repos = Site.objects.filter(github_id__in=repo_ids)
            # TODO - remove active_repos from the list of user_repos

    def dispatch(self, request, *args, **kwargs):
        self.init_user_repos()
        return super(UserDashboard, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.active_repos

    def get_context_data(self, **kwargs):
        context = super(UserDashboard, self).get_context_data(**kwargs)
        if 'repos' not in context or context['repos'] is None:
            context['repos'] = self.user_repos
            return context

    def post(self, request, *args, **kwargs):
        if 'setup' in self.request.POST:
            repo_id = self.request.POST.get('setup')
            # do the registration step API endpoint call.
        elif 'disable' in self.request.POST:
            repo_id = self.request.POST.get('disable')
            site_to_delete = Site.objects.get(pk=repo_id)
            # TODO - Make a call to builder to delete all stored content for
            # this site. On success of that, delete all environments and builds
            # in the DB for this site. Then delete the site.
        self.object_list = self.get_queryset()
        return self.render_to_response(self.get_context_data())

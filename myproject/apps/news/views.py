from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from news.forms import NewsItemForm

from .models import NewsGalleryImage, NewsItem, NewsType


class NewsFeedView(ListView):
    """Лента новостей с фильтром по рубрике и подгрузкой фрагментом (fragment=1)."""

    model = NewsItem
    context_object_name = 'news_items'
    paginate_by = 8
    template_name = 'news/news_dashboard.html'

    def get_template_names(self):
        if self.request.GET.get('fragment'):
            return ['news/includes/_news_feed_fragment.html']
        return [self.template_name]

    def get_queryset(self):
        qs = NewsItem.objects.all().prefetch_related('gallery_images')
        t = (self.request.GET.get('type') or '').strip()
        if t and t in NewsType.values:
            qs = qs.filter(news_type=t)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['news_type_tabs'] = NewsType.choices
        ctx['active_type'] = (self.request.GET.get('type') or '').strip()
        if ctx['active_type'] not in NewsType.values and ctx['active_type']:
            ctx['active_type'] = ''
        return ctx


class NewsDetailView(DetailView):
    model = NewsItem
    context_object_name = 'news'
    template_name = 'news/news_detail.html'

    def get_queryset(self):
        return NewsItem.objects.prefetch_related('gallery_images')


class NewsItemCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = NewsItem
    form_class = NewsItemForm
    template_name = 'news/news_item_create.html'
    success_url = reverse_lazy('news:news_dashboard')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            for order, f in enumerate(self.request.FILES.getlist('gallery_files')):
                NewsGalleryImage.objects.create(
                    news_item=self.object,
                    image=f,
                    sort_order=order,
                )
        return HttpResponseRedirect(self.get_success_url())

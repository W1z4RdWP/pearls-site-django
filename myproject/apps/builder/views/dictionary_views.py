import json

from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import DetailView

from builder.audit_logger import log_create, log_delete
from builder.models import DictionarySection, DictionaryTerm


@require_POST
def dictionary_reorder(request):
    import json
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        # ids — список id в новом порядке
        for order, term_id in enumerate(ids, start=1):
            DictionaryTerm.objects.filter(id=term_id).update(order=order)
        return JsonResponse({'result': 'ok'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

        


class DictionarySectionDetailView(DetailView):
    model = DictionarySection
    context_object_name = 'section'
    template_name = 'builder/includes/_dictionary_section_detail.html'
    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get('ajax') == '1':
            section = context['section']
            terms = [
                {
                    'id': term.id,
                    'order': term.order,
                    'term': term.term,
                    'slang': term.slang,
                    'definition': term.definition,
                    'photo': term.photo.url if term.photo else '',
                }
                for term in section.terms.all()
            ]
            html = render_to_string(self.template_name, context, request=self.request)
            return JsonResponse({'html': html, 'data': terms, 'section_id': section.id})
        return super().render_to_response(context, **response_kwargs)




@csrf_exempt  # Для продакшена лучше использовать CSRF и авторизацию!
def save_terms(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не разрешен'}, status=405)
    try:
        data = json.loads(request.body)
        section_id = data.get('section_id')
        terms = data.get('terms', [])
        from builder.models import DictionarySection, DictionaryTerm
        section = DictionarySection.objects.get(id=section_id)
        existing_terms = {t.id: t for t in section.terms.all()}
        sent_ids = set()
        for term_data in terms:
            term_id = term_data.get('id')
            if term_id:
                sent_ids.add(term_id)
                term = existing_terms.get(term_id)
                if term:
                    term.term = term_data.get('term', '')
                    term.slang = term_data.get('slang', '')
                    term.definition = term_data.get('definition', '')
                    term.order = term_data.get('order', 0)
                    term.save()
            else:
                new_term = DictionaryTerm.objects.create(
                    section=section,
                    term=term_data.get('term', ''),
                    slang=term_data.get('slang', ''),
                    definition=term_data.get('definition', ''),
                    order=term_data.get('order', 0)
                )
                # Логируем создание нового термина
                log_create(request.user, new_term, request, comment="Создан новый термин словаря")
                sent_ids.add(new_term.id)
        # Удаляем термины, которых нет в присланном списке
        for tid, term in existing_terms.items():
            if tid not in sent_ids:
                # Логируем удаление термина
                log_delete(request.user, term, request, comment="Удален термин словаря")
                term.delete()
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

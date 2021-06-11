from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    """Класс для страницы about/author.
    """
    template_name = 'about/about.html'


class AboutTechView(TemplateView):
    """Класс для страницы about/tech.
    """
    template_name = 'about/tech.html'


class AboutProjectView(TemplateView):
    """Класс для страницы проекта about/.
    """
    template_name = 'about/project.html'

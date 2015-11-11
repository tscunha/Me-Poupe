from django.conf.urls import include, url
from . import views
from distutils.command.config import config

urlpatterns = [
    url(r'^$', views.pag_inicial, name='pag_inicial'),
    url(r'^accounts/criar/$', views.criar_usuario, name='criar_usuario'),
    url(r'^receitas/$', views.lista_receitas, name='lista_receitas'),
    url(r'^receitas/adicionar/$', views.criar_receita, name='criar_receita'),
    url(r'^receitas/validar/(?P<pk>[0-9]+)/$', views.validar_receita, name='validar_receita'),
    url(r'^receitas/apagar/(?P<pk>[0-9]+)/$', views.apagar_receita, name='apagar_receita'),
    url(r'^receitas/form_handler/$', views.rec_form_handler, name='rec_form_handler'),
    url(r'^despesas/$', views.lista_despesas, name='lista_despesas'),
    url(r'^despesas/adicionar/$', views.criar_despesa, name='criar_despesa'),
    url(r'^despesas/validar/(?P<pk>[0-9]+)/$', views.validar_despesa, name='validar_despesa'),
    url(r'^despesas/apagar/(?P<pk>[0-9]+)/$', views.apagar_despesa, name='apagar_despesa'),
    url(r'^despesas/form_handler/$', views.des_form_handler, name='des_form_handler'),
    url(r'^agenda/$', views.agenda, name='agenda'),
    url(r'^agenda/form_handler/$', views.agenda_form_handler, name='agenda_form_handler'),
    url(r'^limpar_tudo/$', views.limpar_tudo, name='limpar_tudo'),
    url(r'^categorias/$', views.lista_categorias, name='lista_categorias'),
    url(r'^categorias/adicionar/$', views.criar_categoria, name='criar_categoria'),
    url(r'^categorias/detalhes/(?P<pk>[0-9]+)/$', views.categoria_detalhes, name='categoria_detalhes'),
    url(r'^config/$', views.config, name='config'),
    url(r'^limpar_tudo/$', views.limpar_tudo, name='limpar_tudo'),
    url('', include('social.apps.django_app.urls', namespace='social')),
]
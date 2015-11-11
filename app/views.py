import datetime
from itertools import chain

from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required


from .forms import UserForm, ReceitaForm, BuscaMesForm, DespesaForm, CategoriaForm
from .models import MetaUsuario, Receita, Mes, Despesa, Categoria, CategoriaMes, Alerta

#######################################################################
## Funcoes de controle para realizadas ao longo do uso do aplicativo ##
#######################################################################

def atualiza_receita(request):
    user = request.user
    hoje = datetime.date.today()
    receitas = Receita.objects.filter(usuario=user)
    
    for r in receitas:
        if r.dataValidacao and r.dataValidacao <= hoje and not r.validada:
            r.validar()
            mes.balanco = mes.balanco + r.valor
            mes.save()
            
def atualiza_despesa(request):
    user = request.user
    hoje = datetime.date.today()
    despesas = Despesa.objects.filter(usuario=user)
    
    for d in despesas:
        if d.dataValidacao and d.dataValidacao <= hoje and not d.validada:
            d.validar()
            
            mes.balanco = mes.balanco - d.valor
            mes.total_gasto = mes.total_gasto + d.valor
            mes.save()
            
            if d.categoria:
                try:
                    categoria_mes = CategoriaMes.objects.get(categoria=d.categoria, mes=mes)
                except CategoriaMes.DoesNotExist:
                    categoria_mes = CategoriaMes.objects.create(categoria=d.categoria, mes=mes)
                categoria_mes.gasto = categoria_mes.gasto + despesa.valor
                categoria_mes.save()
        
            
def pega_categorias(request):
    hoje = datetime.date.today()
    try:
        mes = Mes.objects.get(usuario=request.user, num=hoje.month, ano=hoje.year)
    except Mes.DoesNotExist:
        mes = Mes.objects.create(usuario=request.user, num=hoje.month, ano=hoje.year)
        
    historico = []
    total_cat = 0
    
    for cat_mes in CategoriaMes.objects.filter(mes=mes):
        total_gasto = cat_mes.mes.total_gasto
        
        if total_gasto:
            total_cat = total_cat + cat_mes.gasto
            percent_mes = (cat_mes.gasto / cat_mes.mes.total_gasto) * 100
            percent_mes = float("%.2f" % percent_mes)
        else:
            percent_mes = 0
            
        if cat_mes.objetivo:
            percent_objetivo = (cat_mes.gasto / cat_mes.objetivo) * 100
            percent_objetivo = float("%.2f" % percent_objetivo)
        else:
            percent_objetivo = 0
        historico.append((cat_mes, percent_mes, percent_objetivo))
    
    return historico

def info_sem_categoria(request):
    hoje = datetime.date.today()
    try:
        mes = Mes.objects.get(usuario=request.user, num=hoje.month, ano=hoje.year)
    except Mes.DoesNotExist:
        mes = Mes.objects.create(usuario=request.user, num=hoje.month, ano=hoje.year)
    
    valor_total = 0
    for despesa in Despesa.objects.filter(mes=mes, categoria=None):
        valor_total = valor_total + despesa.valor
    
    if mes.total_gasto:
            percent_mes = (valor_total / mes.total_gasto) * 100
            percent_mes = float("%.2f" % percent_mes)
    else:
        percent_mes = 0
    
    return (valor_total, percent_mes)

def pega_meses(request):
    hoje = datetime.date.today()
    try:
        mes = Mes.objects.get(usuario=request.user, num=hoje.month, ano=hoje.year)
    except Mes.DoesNotExist:
        mes = Mes.objects.create(usuario=request.user, num=hoje.month, ano=hoje.year)
    meses = []
    
    for mes in Mes.objects.filter(usuario=request.user):
        total_gasto = round(mes.total_gasto, 2)
        total_ganho = round(mes.balanco + mes.total_gasto, 2)
        meses.append((mes, total_gasto, total_ganho))
    
    return meses

def apagar_objeto(request, objeto):
    objeto.delete()

####################################################
## Pagina inicial e criacao de usuario ##
####################################################

def pag_inicial(request):   
    if request.user.is_authenticated():
        hoje = datetime.date.today()
        try:
            mes = Mes.objects.get(usuario=request.user, num=hoje.month, ano=hoje.year)
        except Mes.DoesNotExist:
            mes = Mes.objects.create(usuario=request.user, num=hoje.month, ano=hoje.year)
            
        atualiza_receita(request)
        atualiza_despesa(request)
        
        historico = pega_categorias(request)
        meses = pega_meses(request)
        
        lista_receitas = Receita.objects.filter(usuario=request.user, mes=mes).order_by('-id')[:3]
        lista_despesas = Despesa.objects.filter(usuario=request.user, mes=mes).order_by('-id')[:3]
        lista_agenda = list(chain(lista_receitas, lista_despesas))
        
        quant_categorias = len(CategoriaMes.objects.filter(mes=mes).exclude(objetivo=None))
        alertas = Alerta.objects.filter(usuario=request.user)
        sem_categoria = info_sem_categoria(request)
        
        balanco = float("%.2f" % mes.balanco)
        mes_gasto = float("%.2f" % mes.total_gasto)
        
        return render(request, 'pags/inicio_logged.html', {'user': request.user, 
                                                           'mes': mes,
                                                           'hoje': hoje,
                                                           'historico':historico,
                                                           'meses': meses,
                                                           'atividade': lista_agenda,
                                                           'quant_categorias': quant_categorias,
                                                           'alertas': alertas,
                                                           'info_sem_categoria': sem_categoria,
                                                           'balanco': balanco,
                                                           'mes_gasto': mes_gasto})
    else:
        return render(request, 'pags/inicio.html', {})

def criar_usuario(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            new_user = User.objects.create_user(**form.cleaned_data)
            new_user_meta = MetaUsuario.objects.create(userid=new_user)
            Categoria.objects.create(descricao='Sem categoria', usuario=new_user)
            return render(request, 'pags/inicio.html', {})
    else:
        form = UserForm() 

    return render(request, 'pags/novo_usuario.html', {'form': form}) 

####################################################
## Views relacionadas a despesas e receitas ##
####################################################

@login_required
def criar_receita(request):
    if request.method == 'POST':
        form = ReceitaForm(request.user, request.POST)
        if form.is_valid():            
            nova_receita = form.save(commit=False)
            if form.mes:
                nova_receita.mes = form.mes
            nova_receita.usuario = request.user
            
            if nova_receita.validada:
                usuario = request.user
                hoje = datetime.date.today()
                mes = Mes.objects.get(usuario=usuario, num=hoje.month, ano=hoje.year)
                
                nova_receita.validar()
                nova_receita.mes = mes
                nova_receita.dataValidacao = hoje
                mes.balanco = mes.balanco + nova_receita.valor
                mes.save()
            
            nova_receita.save()
            return redirect('app.views.pag_inicial')
        
        historico = pega_categorias(request)
        
        return render(request, 'pags/criar_receita.html', {'form' : form,
                                                           'historico':historico})
    else:
        form = ReceitaForm(request.user)
        
        historico = pega_categorias(request)

        return render(request, 'pags/criar_receita.html', {'form' : form,
                                                           'historico':historico})

@login_required    
def validar_receita(request, pk):
    receita = get_object_or_404(Receita, pk=pk)
    usuario = request.user
    hoje = datetime.date.today()
    mes = Mes.objects.get(usuario=usuario, num=hoje.month, ano=hoje.year)
    
    receita.validar()  
    receita.mes = mes
    receita.dataValidacao = hoje
    receita.save()
    mes.balanco = mes.balanco + receita.valor
    mes.save()  
    return redirect('app.views.lista_receitas')

@login_required
def lista_receitas(request):
    receitas = Receita.objects.filter(usuario=request.user)
    form = BuscaMesForm(request.user)
    
    historico = pega_categorias(request)
    
    return render(request, 'pags/lista_receitas.html', {'receitas': receitas,
                                                        'form': form,
                                                        'historico':historico})
    
@login_required
def editar_receita(request, pk):
    receita = get_object_or_404(Receita, pk=pk)
    
    if request.method == 'POST':
        valor_antigo = receita.valor
        validada_antigo = receita.validada
        dataValidacao_antigo = receita.dataValidacao
        dataCriacao_antigo = receita.dataCriacao
        form = ReceitaForm(request.user, request.POST, instance=receita)
        
        if form.is_valid():            
            rec = form.save(commit=False)
            
            cd = form.cleaned_data
            mes = receita.mes
            
            diferenca = cd['valor'] - valor_antigo
            mes.balanco = mes.balanco + diferenca
            rec.validada = validada_antigo
            rec.dataCriacao = dataCriacao_antigo
            rec.dataValidacao = dataValidacao_antigo
                
            mes.save()
            rec.save()
            
            return HttpResponseRedirect(reverse('lista_receitas'))
        
        return render(request, 'pags/teste.html', {'f': form})
    else:
        form = ReceitaForm(request.user, instance=receita)
        
        historico = pega_categorias(request)
        
        return render(request, 'pags/editar_receita.html', {'form': form,
                                                            'receita': receita,
                                                            'historico':historico})

@login_required
def criar_despesa(request):
    if request.method == 'POST':
        form = DespesaForm(request.user, request.POST)
        if form.is_valid():            
            nova_despesa = form.save(commit=False)
            nova_despesa.mes = form.mes
            nova_despesa.usuario = request.user
            
            categoria = form.cleaned_data['categoria']
            if categoria:
                categoria = Categoria.objects.get(id=categoria)
            else:
                categoria = None
            nova_despesa.categoria = categoria
            
            if nova_despesa.validada:
                usuario = request.user
                hoje = datetime.date.today()
                mes = Mes.objects.get(usuario=usuario, num=hoje.month, ano=hoje.year)
                
                nova_despesa.validar()
                nova_despesa.mes = mes
                nova_despesa.dataValidacao = hoje
                
                mes.balanco = mes.balanco - nova_despesa.valor
                mes.total_gasto = mes.total_gasto + nova_despesa.valor
                mes.save()
                
                if categoria:
                    try:
                        categoria_mes = CategoriaMes.objects.get(categoria=nova_despesa.categoria, mes=mes)
                    except CategoriaMes.DoesNotExist:
                        categoria_mes = CategoriaMes.objects.create(categoria=nova_despesa.categoria, mes=mes)
                    categoria_mes.gasto = categoria_mes.gasto + nova_despesa.valor
                    categoria_mes.save()
            
            nova_despesa.save()
            return redirect('app.views.pag_inicial')
        
        historico = pega_categorias(request)
        
        return render(request, 'pags/criar_despesa.html', {'form' : form,
                                                           'historico':historico})
    else:
        form = DespesaForm(request.user)
        historico = pega_categorias(request)
        
        return render(request, 'pags/criar_despesa.html', {'form': form,
                                                           'historico':historico})

@login_required
def validar_despesa(request, pk):
    despesa = get_object_or_404(Despesa, pk=pk)
    usuario = request.user
    hoje = datetime.date.today()
    mes = Mes.objects.get(usuario=usuario, num=hoje.month, ano=hoje.year)
    
    despesa.validar()
    despesa.mes = mes
    despesa.dataValidacao = hoje
    despesa.save()
    
    mes.balanco = mes.balanco - despesa.valor
    mes.total_gasto = mes.total_gasto + despesa.valor
    mes.save()
    
    if despesa.categoria:
        categoria_mes = CategoriaMes.objects.get(categoria=despesa.categoria, mes=mes)
        categoria_mes.gasto = categoria_mes.gasto + despesa.valor
        categoria_mes.save()
    
    return redirect('app.views.lista_despesas')

@login_required
def lista_despesas(request):
    despesas = Despesa.objects.filter(usuario=request.user)
    form = BuscaMesForm(request.user)
    
    historico = pega_categorias(request)
    
    return render(request, 'pags/lista_despesas.html', {'despesas': despesas,
                                                        'form': form,
                                                        'historico': historico})
    
@login_required
def editar_despesa(request, pk):
    despesa = get_object_or_404(Despesa, pk=pk)
    
    if request.method == 'POST':
        valor_antigo = despesa.valor
        validada_antigo = despesa.validada
        dataValidacao_antigo = despesa.dataValidacao
        dataCriacao_antigo = despesa.dataCriacao
        form = DespesaForm(request.user, request.POST, instance=despesa)
        
        if form.is_valid():            
            des = form.save(commit=False)
            
            cd = form.cleaned_data
            mes = despesa.mes
            
            diferenca = cd['valor'] - valor_antigo
            mes.balanco = mes.balanco - diferenca
            mes.total_gasto = mes.total_gasto + diferenca
            
            des.validada = validada_antigo
            des.dataCriacao = dataCriacao_antigo
            des.dataValidacao = dataValidacao_antigo
            
            if despesa.categoria and despesa.validada:
                cat_mes = CategoriaMes.objects.get(categoria=despesa.categoria, mes=despesa.mes)
                cat_mes.gasto = cat_mes.gasto + diferenca
                cat_mes.save()
                
            mes.save()
            des.save()
            
            return HttpResponseRedirect(reverse('lista_despesas'))
        
        return render(request, 'pags/teste.html', {'f': form})
    else:
        form = DespesaForm(request.user, instance=despesa)
        
        historico = pega_categorias(request)
        
        return render(request, 'pags/editar_despesa.html', {'form': form,
                                                            'despesa': despesa,
                                                            'historico':historico})

@login_required
def agenda(request):
    hoje = datetime.date.today()
    mes = Mes.objects.get(usuario=request.user, num=hoje.month, ano=hoje.year)
    
    lista_receitas = Receita.objects.filter(usuario=request.user, mes=mes)
    lista_despesas = Despesa.objects.filter(usuario=request.user, mes=mes)
    lista_agenda = list(chain(lista_receitas, lista_despesas))
    
    balanco = mes.balanco
    form = BuscaMesForm(request.user)
    
    historico = pega_categorias(request)
    
    return render(request, 'pags/agenda.html', {'lista': lista_agenda,
                                                'form': form,
                                                'balanco': balanco,
                                                'historico':historico})
    
def apagar_despesa(request, pk):
    hoje = datetime.date.today()
    mes = Mes.objects.get(usuario=request.user, num=hoje.month, ano=hoje.year)
    
    despesa = Despesa.objects.get(pk=pk)
    if despesa.validada:
        mes.balanco = mes.balanco + despesa.valor
        mes.total_gasto = mes.total_gasto - despesa.valor
        mes.save()
        
    if despesa.categoria:
        cat_mes = CategoriaMes.objects.get(mes=mes, categoria=despesa.categoria)
        cat_mes.gasto = cat_mes.gasto - despesa.valor
        cat_mes.save()
    despesa.delete()
    
    return redirect('app.views.lista_despesas')
    
def apagar_receita(request, pk):
    hoje = datetime.date.today()
    mes = Mes.objects.get(usuario=request.user, num=hoje.month, ano=hoje.year)
    
    receita = Receita.objects.get(pk=pk)
    if receita.validada:
        mes.balanco = mes.balanco - receita.valor
        mes.save()
    receita.delete()
    
    return redirect('app.views.lista_receitas')

#################################################################################
## Funcao a ser usada pelos form handlers para restringir as pesquisas por mes ##
#################################################################################

def restringir_pesquisa(objeto, mes_visualizar, tipo_exibicao, request):
    mes = Mes.objects.get(id=mes_visualizar)
            
    if tipo_exibicao == '1': # Todos
        resultados_v = objeto.objects.filter(usuario=request.user, 
                                          mes=mes)
        resultados_n = objeto.objects.filter(usuario=request.user, 
                                          dataCriacao__year=mes.ano,
                                          dataCriacao__month=mes.num,
                                          mes=None)
        resultados = resultados_v | resultados_n
    elif tipo_exibicao == '2': # Somente validados
        resultados = objeto.objects.filter(usuario=request.user,
                                          mes=mes,
                                          validada = True) 
    else: # Somente nao-validados
        resultados_v = objeto.objects.filter(usuario=request.user, 
                                          dataValidacao__year=mes.ano,
                                          dataValidacao__month=mes.num,
                                          validada=False)
        resultados_n = objeto.objects.filter(usuario=request.user, 
                                          dataCriacao__year=mes.ano,
                                          dataCriacao__month=mes.num,
                                          mes=None)
        resultados = resultados_v | resultados_n
    
    return resultados

############################################################
## Aqui vao os form handlers: receitas, despesas e agenda ##
############################################################

@login_required
def rec_form_handler(request):
    if request.method == 'POST':
        form = BuscaMesForm(request.user, request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            # Os dados do formulario sao um dicionario em cd
            mes_visualizar = cd['mes']
            tipo_exibicao = cd['tipo']
            
            receitas = restringir_pesquisa(Receita, mes_visualizar, tipo_exibicao, request)
            
            form = BuscaMesForm(request.user)
            return render(request, 'pags/lista_receitas.html', {'receitas': receitas,
                                                                'form': form,
                                                                'tipoexibicao': str(type(tipo_exibicao))})
    else:
        receitas = Receita.objects.filter(usuario=request.user)
        form = BuscaMesForm(request.user)
        return render(request, 'pags/lista_receitas.html', {'receitas': receitas,
                                                            'form': form,
                                                            'tipoexibicao': 0})

@login_required
def des_form_handler(request):
    if request.method == 'POST':
        form = BuscaMesForm(request.user, request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            # Os dados do formulario sao um dicionario em cd
            mes_visualizar = cd['mes']
            tipo_exibicao = cd['tipo']
            
            despesas = restringir_pesquisa(Despesa, mes_visualizar, tipo_exibicao, request)
                
            form = BuscaMesForm(request.user)
            return render(request, 'pags/lista_despesas.html', {'despesas': despesas,
                                                                'form': form})
    else:
        despesas = Despesa.objects.filter(usuario=request.user)
        form = BuscaMesForm(request.user)
        return render(request, 'pags/lista_despesas.html', {'despesas': despesas,
                                                            'form': form})

@login_required
def agenda_form_handler(request):
    hoje = datetime.date.today()
    mes = Mes.objects.get(usuario=request.user, num=hoje.month, ano=hoje.year)
    
    if request.method == 'POST':
        form = BuscaMesForm(request.user, request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            # Os dados do formulario sao um dicionario em cd
            mes_visualizar = cd['mes']
            tipo_exibicao = cd['tipo']
            
            receitas = restringir_pesquisa(Receita, mes_visualizar, tipo_exibicao, request)
            despesas = restringir_pesquisa(Despesa, mes_visualizar, tipo_exibicao, request)
                
            lista_agenda = list(chain(receitas, despesas))
            form = BuscaMesForm(request.user)
    else:
        receitas = Receita.objects.filter(usuario=request.user, mes=mes)
        despesas = Despesa.objects.filter(usuario=request.user, mes=mes)
        lista_agenda = list(chain(lista_receitas, lista_despesas))
        form = BuscaMesForm(request.user)
    
    return render(request, 'pags/agenda.html', {'lista': lista_agenda,
                                                'form': form,
                                                'balanco': mes.balanco})

####################################################
## Views relacionadas a categorias ##
####################################################

@login_required
def lista_categorias(request):
    hoje = datetime.date.today()
    mes = Mes.objects.get(usuario=request.user, num=hoje.month, ano=hoje.year)
    
    categorias = Categoria.objects.filter(usuario=request.user)
    historico = pega_categorias(request)
    
    return render(request, 'pags/lista_categorias.html', {'categorias': categorias,
                                                          'historico':historico})

@login_required
def criar_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():            
            nova_categoria = form.save(commit=False)
            nova_categoria.usuario = request.user
            nova_categoria.save()
            
            cd = form.cleaned_data
            hoje = datetime.date.today()
            mes = Mes.objects.get(usuario=request.user, num=hoje.month, ano=hoje.year)
            
            nova_categoria_mes = CategoriaMes.objects.create(categoria=nova_categoria,
                                                             mes=mes,
                                                             objetivo=cd['objetivo_mensal'])
                            
            return redirect('app.views.pag_inicial')
        
        historico = pega_categorias(request)
        
        return render(request, 'pags/criar_categoria.html', {'form' : form,
                                                             'historico':historico})
    else:
        form = CategoriaForm()
        
        historico = pega_categorias(request)
        
        return render(request, 'pags/criar_categoria.html', {'form': form,
                                                             'historico':historico})
    
@login_required
def categoria_detalhes(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():            
            cat = form.save(commit=False)
            
            cd = form.cleaned_data
            hoje = datetime.date.today()
            mes = Mes.objects.get(usuario=request.user, num=hoje.month, ano=hoje.year)
            
            try:
                categoria_mes = CategoriaMes.objects.get(categoria=categoria, mes=mes)
            except CategoriaMes.DoesNotExist:
                categoria_mes = CategoriaMes.objects.create(categoria=categoria,mes=mes)
                
            categoria_mes.objetivo = cd['objetivo_mensal']
            categoria_mes.save()
            cat.save()
            
            return HttpResponseRedirect(reverse('lista_categorias'))
        
        return render(request, 'pags/teste.html', {'f': form})
    else:
        hoje = datetime.date.today()
        mes = Mes.objects.get(usuario=request.user, num=hoje.month, ano=hoje.year)
        
        categoria_historico = []
            
        for cat_mes in CategoriaMes.objects.filter(categoria=categoria):
            total_gasto = cat_mes.mes.total_gasto
            
            if total_gasto:
                percent_mes = (cat_mes.gasto / cat_mes.mes.total_gasto) * 100
                percent_mes = float("%.2f" % percent_mes)
            else:
                percent_mes = 0
                
            if cat_mes.objetivo:
                percent_objetivo = (cat_mes.gasto / cat_mes.objetivo) * 100
                percent_objetivo = float("%.2f" % percent_objetivo)
            else:
                percent_objetivo = 0
            categoria_historico.append((cat_mes, percent_mes, percent_objetivo))
            
        form = CategoriaForm(instance=categoria)
        
        historico = pega_categorias(request)
        
        return render(request, 'pags/categoria_detalhes.html', {'categoria': categoria,
                                                                'categoria_historico':categoria_historico,
                                                                'historico': historico,
                                                                'form': form})
        
def config(request):
    historico = pega_categorias(request)
    return render(request, 'pags/configuracoes.html', {'historico': historico})

@login_required
def limpar_tudo(request):
    Mes.objects.filter(usuario=request.user).delete()
    Receita.objects.filter(usuario=request.user).delete()
    Despesa.objects.filter(usuario=request.user).delete()
    Categoria.objects.filter(usuario=request.user).delete()
    return redirect('app.views.pag_inicial')
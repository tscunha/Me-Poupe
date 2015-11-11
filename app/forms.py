import datetime
from datetime import timedelta
from django import forms
from django.db import models

from .models import User, Receita, Despesa, Mes, Categoria

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password',)

class ReceitaForm(forms.ModelForm):
    class Meta:
        model = Receita
        fields = ('descricao','valor','validada','dataValidacao',)
        widgets = {
            'dataValidacao': forms.DateInput(attrs={'class':'datepicker'}),
        }
        
    def __init__(self, user, *args, **kwargs):
        self.user = user
        self.mes = None
        super(ReceitaForm, self).__init__(*args, **kwargs)
        
    def clean(self):
        cleaned_data = super(ReceitaForm, self).clean()
        validada = cleaned_data.get("validada")
        dataValidacao = cleaned_data.get("dataValidacao")
        
        if dataValidacao:
            if validada:
                raise forms.ValidationError("Nao pode auto-validar se quiser validar numa data definida!")
            if dataValidacao < datetime.date.today() - timedelta(days=60):
                raise forms.ValidationError("A data de validacao nao pode ser mais de 60 dias no passado!")
            
            try:
                mesQuery = Mes.objects.get(usuario=self.user,num=dataValidacao.month,ano=dataValidacao.year)
            except Mes.DoesNotExist:
                Mes.objects.create(usuario=self.user,num=dataValidacao.month,ano=dataValidacao.year)
            finally:
                self.mes =  Mes.objects.get(usuario=self.user,num=dataValidacao.month,ano=dataValidacao.year)
                    
class BuscaMesForm(forms.Form):
    def __init__(self, user, *args, **kwargs):
        super(BuscaMesForm, self).__init__(*args, **kwargs)
        MES_ESCOLHA = [(mes.id, mes) for mes in Mes.objects.filter(usuario=user).order_by('ano', 'num')]
            
        TIPO_EXIBICAO = [
                         ('1', 'Todos'),
                         ('2', 'Somente validados'),
                         ('3', 'Somente nao validados')]
        
        self.fields['mes'] = forms.ChoiceField(choices=MES_ESCOLHA)
        self.fields['tipo'] = forms.ChoiceField(choices=TIPO_EXIBICAO, widget=forms.RadioSelect)
        self.initial['tipo'] = '1'
        
class DespesaForm(forms.ModelForm):
    class Meta:
        model = Despesa
        fields = ('descricao','valor','validada','dataValidacao',)
    
        widgets = {
            'dataValidacao': forms.DateInput(attrs={'class':'datepicker'}),
        }
        
    def __init__(self, user, *args, **kwargs):
        self.user = user
        self.mes = None
        super(DespesaForm, self).__init__(*args, **kwargs)
        
        categorias = Categoria.objects.filter(usuario=user)
        CAT_ESCOLHA = [(cat.id, str(cat)) for cat in categorias]
        CAT_ESCOLHA.insert(0, (None, 'Sem categoria'))
        
        self.fields['categoria'] = forms.ChoiceField(choices=CAT_ESCOLHA, required=False)
        
    def clean(self):
        cleaned_data = super(DespesaForm, self).clean()
        validada = cleaned_data.get("validada")
        dataValidacao = cleaned_data.get("dataValidacao")
        
        if dataValidacao:
            if validada:
                raise forms.ValidationError("Nao pode auto-validar se quiser validar numa data definida!")
            if dataValidacao < datetime.date.today() - timedelta(days=60):
                raise forms.ValidationError("A data de validacao nao pode ser mais de 60 dias no passado!")
            
            try:
                mesQuery = Mes.objects.get(usuario=self.user,num=dataValidacao.month,ano=dataValidacao.year)
            except Mes.DoesNotExist:
                Mes.objects.create(usuario=self.user,num=dataValidacao.month,ano=dataValidacao.year)
            finally:
                self.mes =  Mes.objects.get(usuario=self.user,num=dataValidacao.month,ano=dataValidacao.year)
                
class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ('descricao',)
        
    def __init__(self, *args, **kwargs):
        super(CategoriaForm, self).__init__(*args, **kwargs)
        
        self.fields['objetivo_mensal'] = forms.FloatField(required=False)
from datetime import date

from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User

MESES = ['-', 'Janeiro', 'Fevereiro', 'Marco', 'Abril', 'Maio', 'Junho',
         'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

class MetaUsuario(models.Model):
    userid = models.OneToOneField(User, primary_key=True)
    dataCriacao = models.DateField("Data de Criacao", auto_now_add=True)

class Mes(models.Model):
    usuario = models.ForeignKey(User, null=True) # A consertar: tirar este null=true
    num = models.IntegerField()
    ano = models.IntegerField()
    balanco = models.FloatField(default=0.0)
    total_gasto = models.FloatField(default=0.0)
        
    def __str__(self):
        return str("{0} de {1}".format(MESES[self.num], self.ano))
    
class Receita(models.Model):
    descricao = models.CharField(max_length=100, blank=True, null=True, default="Sem descricao")
    usuario = models.ForeignKey(User)
    mes = models.ForeignKey('Mes', null=True)
    valor = models.FloatField(validators = [MinValueValidator(0)])
    
    dataCriacao = models.DateField(default=date.today)
    dataValidacao = models.DateField("Validar em (opcional):", blank=True, null=True)
    validada = models.BooleanField("Auto-Validar", default=False)
    
    def validar(self):
        self.validada = True
        self.save()
        
class Despesa(models.Model):
    descricao = models.CharField(max_length=100, blank=True, null=True, default="Sem descricao")
    usuario = models.ForeignKey(User)
    mes = models.ForeignKey('Mes', null=True)
    valor = models.FloatField(validators = [MinValueValidator(0)])
    
    dataCriacao = models.DateField(default=date.today)
    dataValidacao = models.DateField("Validar em (opcional):", blank=True, null=True)
    validada = models.BooleanField("Validar agora", default=False)
    
    categoria = models.ForeignKey('Categoria', blank=True, null=True)
    
    def validar(self):
        self.validada = True
        self.save()
        
class Categoria(models.Model):
    descricao = models.CharField(max_length=100, null=True, blank=False)
    usuario = models.ForeignKey(User, null=True)
    
    def __str__(self):
       return self.descricao
   
class CategoriaMes(models.Model):
    categoria = models.ForeignKey('Categoria')
    mes = models.ForeignKey('Mes')
    objetivo = models.FloatField(null=True, blank=True, default=None)
    gasto = models.FloatField(default=0.0)
    
    class Meta:
        unique_together = (('categoria','mes'),)
        
class Alerta(models.Model):
    usuario = models.ForeignKey(User)
    texto = models.TextField(default="to-do: Adicionar uma descricao!")
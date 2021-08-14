from django.db import models
from rest_framework import serializers
# Create your models here.

class blocks(models.Model):
    blocks_id=models.CharField(max_length=200, primary_key=True,db_column='blocks_id')
    circuit_name=models.TextField(default='circuit1')
    user_id=models.TextField(default='user1')
    #blocks_id = models.PositiveIntegerField(default=-1,primary_key=True, db_column='blocks_id')
    seq=models.TextField() 
    ip_values=models.TextField()
    #formlist=models.TextField(default='') 

class outputplot(models.Model):
    outputplot_id=models.CharField(max_length=200, primary_key=True,db_column='outputplot_id')
    circuit_name=models.TextField(default='circuit1')
    user_id=models.TextField(default='user1')
    #outputplot_id = models.PositiveIntegerField(default=-1,primary_key=True, db_column='id')
    typeOfAnalysis=models.CharField(max_length=200)
    x=models.TextField() 
    y=models.TextField()

class NgspiceCode(models.Model):
    code_id=models.CharField(max_length=200,primary_key=True, db_column='code_id')
    circuit_name=models.TextField(default='circuit1')
    user_id=models.TextField(default='user1')
    #code_id = models.PositiveIntegerField(default=-1,primary_key=True, db_column='code_id')
    code=models.TextField()

class Users(models.Model):
    user_id = models.CharField(max_length=200,primary_key=True,db_column='user_id')
    password=models.TextField() 
    name=models.TextField() 
    email_id=models.TextField() 


from django.contrib.auth.models import User, Group
from rest_framework import serializers
from .models import blocks,outputplot,NgspiceCode,Users

class blocksSerializer(serializers.ModelSerializer):
    class Meta:
        model = blocks
        fields = ['blocks_id','circuit_name','user_id','seq','ip_values']

class outputplotSerializer(serializers.ModelSerializer):
    class Meta:
        model = outputplot
        fields = ['outputplot_id','circuit_name','user_id','typeOfAnalysis','x','y']

class NgspiceCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NgspiceCode
        fields = ['code_id','circuit_name','user_id','code']

class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['user_id','password','name','email_id']
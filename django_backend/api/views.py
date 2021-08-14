from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from .serializers import blocksSerializer,outputplotSerializer,NgspiceCodeSerializer,UsersSerializer
from .models import blocks,outputplot,NgspiceCode,Users
from rest_framework.response import Response
from django.http import HttpResponse
import sys
import json
from subprocess import run,PIPE
from rest_framework import status
from django.core.mail import send_mail
from django_backend.settings import *


class blocksViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = blocks.objects.all()
    serializer_class = blocksSerializer
    def get_queryset(self):
        req = self.request
        #print(req)
        user_id = req.query_params.get('user_id')
        blocks_id=req.query_params.get('blocks_id')
        if user_id:
            self.queryset = blocks.objects.filter(user_id=user_id)
            return self.queryset
        elif blocks_id:
            self.queryset = blocks.objects.filter(blocks_id=blocks_id)
            return self.queryset
        else:
            self.queryset = blocks.objects.all()
            return self.queryset
    '''
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)'''



    def update(self, request,*args, **kwargs):
        try:
            instance = blocks.objects.get(pk=kwargs['pk'])
            serializer = blocksSerializer(instance=instance,data=request.data)
            if serializer.is_valid():
                b=serializer.save()
                return Response(serializer.data,status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except blocks.DoesNotExist:
            serializer = blocksSerializer(data=request.data)
        if serializer.is_valid():
            b=serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class outputplotViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = outputplot.objects.all()
    serializer_class = outputplotSerializer
    def get_queryset(self):
        req = self.request
        #print(req)
        user_id = req.query_params.get('user_id')
        outputplot_id=req.query_params.get('outputplot_id')
        if user_id:
            self.queryset = outputplot.objects.filter(user_id=user_id)
            return self.queryset
        elif outputplot_id:
            self.queryset = outputplot.objects.filter(outputplot_id=outputplot_id)
            return self.queryset
        else:
            return self.queryset

class NgspiceCodeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = NgspiceCode.objects.all()
    serializer_class = NgspiceCodeSerializer
    def get_queryset(self):
        req = self.request
        #print(req)
        user_id = req.query_params.get('user_id')
        code_id=req.query_params.get('code_id')
        if user_id:
            self.queryset = NgspiceCode.objects.filter(user_id=user_id)
            return self.queryset
        elif code_id:
            self.queryset = NgspiceCode.objects.filter(code_id=code_id)
            return self.queryset
        else:
            return self.queryset

class UsersViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Users.objects.all()
    serializer_class = UsersSerializer


    def get_queryset(self):
        req = self.request
        #print(req)
        user_id = req.query_params.get('user_id')
        if user_id:
            self.queryset = Users.objects.filter(user_id=user_id)
            return self.queryset
        else:
            self.queryset = Users.objects.all()
            return self.queryset

def senddata_topython(request,user_id,circuit_name):
    #print(user_id,circuit_name)
    blocks_data=blocks.objects.get(blocks_id=user_id+';'+circuit_name)
    #print(blocks_data.seq,blocks_data.ip_values)
    #Run python script pass input and get the output
    out=run([sys.executable,'C:\\Users\\amey sonje\\Desktop\\django_backend\\circuit_integration.py',blocks_data.seq,blocks_data.ip_values,user_id,circuit_name],shell=False,stdout=PIPE)
    #xa,ya=out.stdout.decode("utf-8").split(';')
    #print(out)
    return HttpResponse()

def delete(request,blocks_id):
    #print("inside delete")
    blocks.objects.filter(blocks_id=blocks_id).delete()
    outputplot.objects.filter(outputplot_id=blocks_id).delete()
    NgspiceCode.objects.filter(code_id=blocks_id).delete()
    return HttpResponse()

#to send email
def mail(request,user_id):

    userData=Users.objects.get(user_id=user_id)
    subject="Login Credentials of "+userData.name
    msg="Dear "+userData.name+","+"\n\nThe details entered while registering with Circuit Scribe are as follows:"+"\n\nUsername/Login-ID - "+user_id+"\nName -"+userData.name+"\nPassword -"+userData.password+"\n\nThank you for using mail service."+"We recommend you to change your password using update profile after logging in."+"\n\nAnd if you face any difficulty feel free to reply to this mail"+"\n\nRegards,"+"\nCircuitScribe Team"
    #print(userData.name,userData.email_id,userData.password)
    to=userData.email_id
    res=send_mail(subject, msg, EMAIL_HOST_USER, [to])
    if(res == 1):
        msg = "Mail Sent Successfully"
    else:
        msg = "Mail could not sent"
    return HttpResponse(json.dumps(msg))




from django.conf import settings
import django_backend.settings as app_settings

settings.configure(INSTALLED_APPS=app_settings.INSTALLED_APPS,DATABASES=app_settings.DATABASES)

import django
django.setup()

import json
from django_backend.api.models import blocks,outputplot
import sys
#print("hello")
print(sys.argv[1],sys.argv[2])
seq=json.loads(sys.argv[1])
ip_values=json.loads(sys.argv[2])
print(type(seq),type(ip_values))
x = [1,2,5,9,8] 
# corresponding y axis values 
y = [1,2,3,4,5]

xa=str(x[0])
for i in range(1,len(x)):
    xa=xa+","+str(x[i])

ya=str(y[0])
for i in range(1,len(y)):
    ya=ya+","+str(y[i])

#print(xa+';'+ya,end='')
xa_new=[1,2,3,4,5]
ya_new=[3,3,5,3,5]
outputplot.objects.all().delete()
outputplot.objects.update_or_create(outputplot_id=1,x=json.dumps(xa_new),y=json.dumps(ya_new))



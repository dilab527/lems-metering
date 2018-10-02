from datetime import datetime
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView

import base64
import copy
import csv
import time
import requests

payload = {'key': settings.API_KEY}
headers = {'authentication': settings.PROJECT_KEY}

class IndexView(ListView):
    context_object_name = 'lems_list'
    template_name = 'lemsquery/index.html'
    def get_queryset(self):
        url = 'https://www.energywatch.kr/api/v2/sites'
        r = requests.get(url, params=payload, headers=headers)
        return  r.json()['_data_']

class DeviceView(ListView):
    context_object_name = 'devices'
    template_name = 'lemsquery/devices.html'

    def get_context_data(self, **kwargs):
        site_id = self.kwargs['site_id']
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['site_id'] = site_id
        return context

    def get_queryset(self):
        site_id = self.kwargs['site_id']
        url = 'https://www.energywatch.kr/api/v2/devices/site/%d'%(site_id)
        r = requests.get(url, params=payload, headers=headers)
        devices = r.json()['_data_']
        return  sorted(devices, key=lambda device: device['serial_id'])

class DownloadView(View):
    fields = [
        'PhaseVoltage',
        'LineVoltage',
        'VoltageCrestFactor',
        'PhaseCurrent',
        'CurrentCrestFactor',
        'ActivePower',
        'ReactivePower',
        'PowerFactor',
        'Frequency',
        'ThdPhaseVoltage',
        'ThdPhaseCurrent',
        'Temperature',
        'VoltageHarmonics',
        'CurrentHarmonics',
        'ApparentPower',
        'InverterConversionEfficiency',
        'ElectricCharge',
        'LineVoltageRS',
        'LineVoltageST',
        'LineVoltageTR',
        'AccumulatePowerConsumption',
    ]

    def dt_to_ns(dt):        
        epoch = datetime.utcfromtimestamp(0)
        dt = datetime.strptime(dt, '%m/%d/%Y')
        delta = dt - epoch
        return int(delta.total_seconds() * 1000 * 1000)

    def get(self, request, site_id, logical_id):
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="%d_%s_%d.csv"'%(site_id, logical_id,int(time.time()))

        url = 'https://www.energywatch.kr/api/v2/metering-ac/group'
        params = copy.deepcopy(payload)
        params['site_id'] = site_id
        params['metering_device_logical_id'] = logical_id
        
        
        start = self.dt_to_ns(request.GET['start'])
        end = self.dt_to_ns(request.GET['end'])
        print(start, end)

        r = requests.get(url, params=payload, headers=headers)
        resp = r.json()['_data_']
        writer = csv.writer(response)

        meterings = list(filter(lambda m: m['GroupId'] == 1, resp[logical_id]))
        meterings = list(map(lambda m: [base64.b64decode(m['CreatedDate']).decode('utf-8')]+[m[d] for d in m if d in self.fields], meterings))
        writer.writerow(['CreatedDate'] + self.fields)
        writer.writerows(meterings)

        return response
        
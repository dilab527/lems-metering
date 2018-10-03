from datetime import datetime, timedelta
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
    fields_for_no = [
        'LogicalId',
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

    fields_for_period = [
        'LogicalId',
        'PhaseVoltageMax',
        'PhaseVoltageAvg',
        'PhaseVoltageFirst',
        'PhaseVoltageLast',
        'LineVoltageMin',
        'LineVoltageMax',
        'LineVoltageAvg',
        'LineVoltageFirst',
        'LineVoltageLast',
        'VoltageCrestFactorMin',
        'VoltageCrestFactorMax',
        'VoltageCrestFactorAvg',
        'VoltageCrestFactorFirst',
        'VoltageCrestFactorLast',
        'PhaseCurrentMin',
        'PhaseCurrentMax',
        'PhaseCurrentAvg',
        'PhaseCurrentFirst',
        'PhaseCurrentLast',
        'CurrentCrestFactorMin',
        'CurrentCrestFactorMax',
        'CurrentCrestFactorAvg',
        'CurrentCrestFactorFirst',
        'CurrentCrestFactorLast',
        'ActivePowerMin',
        'ActivePowerMax',
        'ActivePowerAvg',
        'ActivePowerFirst',
        'ActivePowerLast',
        'ReactivePowerMin',
        'ReactivePowerMax',
        'ReactivePowerAvg',
        'ReactivePowerFirst',
        'ReactivePowerLast',
        'PowerFactorMin',
        'PowerFactorMax',
        'PowerFactorAvg',
        'PowerFactorFirst',
        'PowerFactorLast',
        'FrequencyMin',
        'FrequencyMax',
        'FrequencyAvg',
        'FrequencyLast',
        'ThdPhaseVoltageMin',
        'ThdPhaseVoltageMax',
        'ThdPhaseVoltageAvg',
        'ThdPhaseVoltageFirst',
        'ThdPhaseVoltageLast',
        'ThdPhaseCurrentMin',
        'ThdPhaseCurrentMax',
        'ThdPhaseCurrentAvg',
        'ThdPhaseCurrentFirst',
        'ThdPhaseCurrentLast',
        'TemperatureMin',
        'TemperatureMax',
        'TemperatureAvg',
        'TemperatureFirst',
        'TemperatureLast',
        'VoltageHarmonicsMin',
        'VoltageHarmonicsMax',
        'VoltageHarmonicsAvg',
        'VoltageHarmonicsFirst',
        'VoltageHarmonicsLast',
        'CurrentHarmonicsMin',
        'CurrentHarmonicsMax',
        'CurrentHarmonicsAvg',
        'CurrentHarmonicsFirst',
        'CurrentHarmonicsLast',
        'ApparentPowerMin',
        'ApparentPowerMax',
        'ApparentPowerAvg',
        'ApparentPowerFirst',
        'ApparentPowerLast',
        'InverterConversionEfficiencyMin',
        'InverterConversionEfficiencyMax',
        'InverterConversionEfficiencyAvg',
        'InverterConversionEfficiencyFirst',
        'InverterConversionEfficiencyLast',
        'ElectricChargeMin',
        'ElectricChargeMax',
        'ElectricChargeAvg',
        'ElectricChargeFirst',
        'ElectricChargeLast',
        'LineVoltageRSMin',
        'LineVoltageRSMax',
        'LineVoltageRSAvg',
        'LineVoltageRSFirst',
        'LineVoltageRSLast',
        'LineVoltageSTMin',
        'LineVoltageSTMax',
        'LineVoltageSTAvg',
        'LineVoltageSTFirst',
        'LineVoltageSTLast',
        'LineVoltageTRMin',
        'LineVoltageTRMax',
        'LineVoltageTRAvg',
        'LineVoltageTRFirst',
        'LineVoltageTRLast',
        'AccumulatePowerConsumptionMin',
        'AccumulatePowerConsumptionMax',
        'AccumulatePowerConsumptionAvg',
        'AccumulatePowerConsumptionFirst',
        'AccumulatePowerConsumptionLast',
        'AccumulatePowerConsumptionIncrement',
        'RatePerKWH',
        'TimeStep',
    ]

    periods_dic = {
        'no': '',
        '1m': '-1-min',
        '5m': '-5-min',
        '15m': '-15-min',
        '1h': '-1-hour',
        '1d': '-1-day',
        '1w': '-1-week',
        '1mo': '-1-month',
        '1y': '-1-year',
    }

    def dt_to_ns(self, date_string,offset=0):        
        epoch = datetime.utcfromtimestamp(0)
        dt = timedelta(seconds=offset)
        t0 = datetime.strptime(date_string, '%m/%d/%Y')
        delta = (dt + t0) - epoch
        return int(delta.total_seconds() * 1000 * 1000 * 1000)

    def get(self, request, site_id, logical_id):
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = "attachment; filename='%d_%s_%d.csv'"%(site_id, logical_id,int(time.time()))

        period = request.GET['period']

        url = 'https://www.energywatch.kr/api/v2/metering-ac/group' + self.periods_dic[period]
        params = copy.deepcopy(payload)
        params['site_id'] = site_id
        params['metering_device_logical_id'] = logical_id
        
        start_string = request.GET['start']
        end_string = request.GET['end']
        if(start_string):
            params['start_ts'] = self.dt_to_ns(start_string)
        if(end_string):
            params['end_ts'] = self.dt_to_ns(end_string,86399)

        r = requests.get(url, params=params, headers=headers)
        print(r.url)
        resp = r.json()['_data_']
        writer = csv.writer(response)

        fields = []
        if(period == 'no'):
            fields = self.fields_for_no
        else:
            fields = self.fields_for_period

        meterings = list(filter(lambda m: m['GroupId'] == 1, resp[logical_id]))
        meterings = list(map(lambda m: [base64.b64decode(m['CreatedDate']).decode('utf-8')]+[m[d] for d in m if d in fields], meterings))
        writer.writerow(['CreatedDate'] + fields)
        writer.writerows(meterings)

        return response
        
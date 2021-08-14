from django.conf import settings
import django_backend.settings as app_settings

settings.configure(INSTALLED_APPS=app_settings.INSTALLED_APPS,DATABASES=app_settings.DATABASES)

import django
django.setup()

import json
from django_backend.api.models import blocks,outputplot,NgspiceCode
import sys

import numpy as np
import matplotlib.pyplot as plt
import math
import PySpice.Logging.Logging as Logging
logger = Logging.setup_logging()


from PySpice.Plot.BodeDiagram import bode_diagram
from PySpice.Probe.Plot import plot
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

####################################################################################################

from PySpice.Spice.Netlist import SubCircuitFactory
from PySpice.Unit import *
#to avoid warnings
import warnings
warnings.filterwarnings("ignore")
resolution=0

circuit = Circuit('circuit')

break_frequncy1=0
break_frequency2=0

def decimalToBinary(n):
    return bin(n).replace("0b", "")


def resistance_value(R1_str):
    R1_value=''
    R1_int=0.0
    lst=['1','2','3','4','5','6','7','8','9','0','.']
    for i in range(len(R1_str)-2):
        if R1_str[i] in lst:
            R1_value=R1_value+R1_str[i]
            if R1_str[i+1]=='k':
                R1_int=float(R1_value)*1000
            elif R1_str[i+1]=='M':
                R1_int=float(R1_value)*1000000
            else:
                R1_int=float(R1_value)
    return R1_int

def capacitance_value(C1_str):
    C1_value=''
    C1_int=0.0
    lst=['1','2','3','4','5','6','7','8','9','0','.']
    for i in range(len(C1_str)-2):
        if C1_str[i] in lst:
            C1_value=C1_value+C1_str[i]
            if C1_str[i+1]=='u':
                C1_int=float(C1_value)*0.000001

            elif C1_str[i+1]=='n':
                C1_int=float(C1_value)*0.000000001

            elif C1_str[i+1]=='p':
                C1_int=float(C1_value)*0.000000000001

            elif C1_str[i+1]=='m':
                C1_int=float(C1_value)*0.001

            else:
                C1_int=float(C1_value)
    return C1_int


def voltage_source(n,source_type,amplitude,frequency,initial_value,pulsed_value,pulse_width,period,pwl_string,terminal1):
    if source_type=="sinusoidal":
        source=circuit.SinusoidalVoltageSource2(terminal1, terminal1, circuit.gnd, amplitude=amplitude, frequency=frequency)
    elif source_type=="pulse":
        source=circuit.PulseVoltageSource2(terminal1,terminal1,circuit.gnd,initial_value=initial_value,pulsed_value=pulsed_value,pulse_width=pulse_width,period=period)
    elif source_type=="PWL":
        source=circuit.PieceWiseLinearVoltageSource2(terminal1, terminal1, circuit.gnd, values=pwl_string)
    elif source_type=="dc":
        source=circuit.V(terminal1,terminal1,circuit.gnd,amplitude)

def analysis_type(typ,start,step,stop,node,source):
    if typ=="transient":
        start=float(start)
        stop=float(stop)
        step=float(step)
        simulator = circuit.simulator(temperature=25, nominal_temperature=25)
        analysis = simulator.transient(start_time=start,step_time=step, end_time=stop)
        #plt.title("Cicuit Transient Simulation")
        x_outputplot=[]
        y_outputplot={}
        #total_y_points=0

        ########x_outputplot
        for i in analysis.time:
            x_outputplot.append(float("{:f}".format(float(str(i)[:-1]))))
        #########

        for i in range(len(seq)-1):
            n,name=seq[i].split('_')
            #plt.plot(analysis.time,analysis[node[seq[i]][-1]],label =n+' '+name+' output')
            y_outputplot[n+'_'+name]=[]
            for i in analysis[node[seq[i]][-1]]:
                y_outputplot[n+'_'+name].append(float("{:f}".format(float(str(i)[:-1]))))
            #print(len(y_outputplot[n+'_'+name]))
            #total_y_points=len(y_outputplot[n+'_'+name])

        #for i in y_outputplot.keys():
            #print(i)

        #print(x_outputplot)
        #print(y_outputplot)
        #outputplot.objects.all().delete()

        #print(user_id,circuit_name)
        outputplot.objects.filter(outputplot_id=user_id+';'+circuit_name).filter(circuit_name=circuit_name).delete()
        outputplot.objects.update_or_create(outputplot_id=user_id+';'+circuit_name,circuit_name=circuit_name,user_id=user_id,typeOfAnalysis="transient",x=json.dumps(x_outputplot),y=json.dumps(y_outputplot))
        #plt.grid()
        #plt.legend()
        #plt.show()

    elif typ=="ac":
        
        simulator = circuit.simulator(temperature=25, nominal_temperature=25)
        analysis = simulator.ac(start_frequency=start, stop_frequency=stop, number_of_points=10,  variation='dec')
        x_outputplot=[]
        y_outputplot={}
        for fi in analysis.frequency:
            x_outputplot.append(float("{:f}".format(float(str(fi)[:-2]))))

        for i in range(len(seq)-1):
            n,name=seq[i].split('_')
            y_outputplot[n+'_'+name+'_magnitude']=(20*np.log10(np.absolute(analysis[node[seq[i]][-1]]))).tolist()
            y_outputplot[n+'_'+name+'_phase']=(np.angle(analysis[node[seq[i]][-1]], deg=False)).tolist()
        #print(x_outputplot)
        #print(y_outputplot)
        #outputplot.objects.all().delete()
        outputplot.objects.filter(outputplot_id=user_id+';'+circuit_name).filter(circuit_name=circuit_name).delete()
        outputplot.objects.update_or_create(outputplot_id=user_id+';'+circuit_name,circuit_name=circuit_name,typeOfAnalysis="ac",x=json.dumps(x_outputplot),y=json.dumps(y_outputplot))

    elif typ=="transient_adc":
        start=float(start)
        stop=float(stop)
        step=float(step)
        simulator = circuit.simulator(temperature=25, nominal_temperature=25)
        analysis = simulator.transient(start_time=start, step_time=step, end_time=stop)
        x_outputplot=[]
        y_outputplot={}
        ##############x_outputplot
        for i in analysis.time:
            x_outputplot.append(float("{:f}".format(float(str(i)[:-1]))))
        #############
        #figure, (ax1, ax2) = plt.subplots(2, figsize=(20, 10))
        #ax1.set_xlabel('Time [s]')
        #ax1.set_ylabel('Voltage [V]')
        #ax1.grid()
        for i in range(len(seq)-2):
            n,name=seq[i].split('_')
            #ax1.plot(analysis[node[seq[i]][-1]],label =n+' '+name+' output')
            y_outputplot[n+'_'+name]=[]
            for i in analysis[node[seq[i]][-1]]:
                y_outputplot[n+'_'+name].append(float("{:f}".format(float(str(i)[:-1]))))
            #print(len(y_outputplot[n+'_'+name]))
            #total_y_points=len(y_outputplot[n+'_'+name])
        #ax2.set_xlabel('Time [s]')
        #ax2.set_ylabel('Voltage [V]')
        #ax2.grid()
        dig_out=[]
        for i in range(len(analysis.time)):
            for j in range(resolution,1,-1):
                if float("{:f}".format(float(str(analysis['c'+str(j)][i])[:-1])))> 0:
                    dig_out.append(str(decimalToBinary(j-1)))
                    break
            else:
                dig_out.append('0'*(len(str(decimalToBinary(resolution)))-1))
        #for j in range(resolution,1,-1):
            #print(analysis['r'+str(j)+'_2'][1])

        #plt.plot(analysis.time, analysis['in'])
        #ax2.plot(analysis.time, analysis['r'+str(resolution)+'_1'])
        y_outputplot['r'+str(resolution)+'_1']=[]
        for i in analysis['r'+str(resolution)+'_1']:
            y_outputplot['r'+str(resolution)+'_1'].append(float("{:f}".format(float(str(i)[:-1]))))
        #plt.title("Flash-Adc")
        for j in range(resolution,1,-1):
            y_outputplot['c'+str(j)]=[]
            for i in analysis['c'+str(j)]:
                y_outputplot['c'+str(j)].append(float("{:f}".format(float(str(i)[:-1]))))
            #ax2.plot(analysis.time, analysis['c'+str(j)], label='c'+str(j))
        for k in range(2,resolution+1):
            y_outputplot['r'+str(k)+'_2']=[]
            for i in analysis['r'+str(k)+'_2']:
                y_outputplot['r'+str(k)+'_2'].append(float("{:f}".format(float(str(i)[:-1]))))
            #ax2.plot(analysis.time, analysis['r'+str(k)+'_2'])
            #print(dig_out)
            #print(dig_out)
        #ax2.plot(analysis.time,dig_out)
        y_outputplot['digital_output']=dig_out
        print(dig_out)
        #ax2.legend()
        #print(x_outputplot[:5])
        #print(y_outputplot["0_Input"][:5])
        #print(y_outputplot["1_nonInvOpamp"][:5])
        #print(y_outputplot["r12_1"][:5])
        #print(y_outputplot["r12_1"][:5])
        #print(y_outputplot["c12"][:5])
        #print(y_outputplot["c5"][:5])
        #print(y_outputplot["r4_2"][:5])
        #print(y_outputplot["r12_2"][:5])
        #print(y_outputplot["digital_output"][:5])
        #plt.show()
        outputplot.objects.filter(outputplot_id=user_id+';'+circuit_name).filter(circuit_name=circuit_name).delete()
        outputplot.objects.update_or_create(outputplot_id=user_id+';'+circuit_name,circuit_name=circuit_name,user_id=user_id,typeOfAnalysis="transient_adc",x=json.dumps(x_outputplot),y=json.dumps(y_outputplot))

    elif typ=="dc":
        source=list(source.split(','))
        start=list(map(int,start.split(',')))
        stop=list(map(int,stop.split(',')))
        step=list(map(int,step.split(',')))
        dc_dict={}
        for i in range(len(source)):
            dc_dict["V"+source[i]]=slice(start[i],stop[i],step[i])
        simulator = circuit.simulator(temperature=25, nominal_temperature=25) 
        analysis=simulator.dc(**dc_dict)
        #analysis=simulator.dc(**{"V"+source: slice(start1, stop1, step1),"V"+source2: slice(start2, stop2, step2)})
        #for 2 sources
        if(len(source)==2):
            x_outputplot=[]
            y_outputplot={}
            outp={}
            j=0
            for i in analysis[source[0]][0:stop[0]]:
                x_outputplot.append(float("{:f}".format(float(str(i)[:-1]))))
                
            for k in range(start[1],stop[1]+1,step[1]):
                #plt.plot(analysis[source[0]][j:j+stop[0]],analysis.output[j:j+stop[0]],source[1]+"="+str(i))
                for i in range(len(seq)-1):
                    n,name=seq[i].split('_') 
                    y_outputplot[n+'_'+name+'*'+source[1]+"="+str(k)+"V"]=[]
                    for a in analysis[node[seq[i]][-1]][j:j+stop[0]]:
                        y_outputplot[n+'_'+name+'*'+source[1]+"="+str(k)+"V"].append(float("{:f}".format(float(str(a)[:-1]))))
                    #plt.plot(analysis[source[0]][j:j+stop[0]],analysis[node[seq[i]][-1]][j:j+stop[0]],label =n+'_'+name+'_'+source[1]+"="+str(k)+"V")
                j=j+stop[0]
            #print(x_outputplot)
            #print(y_outputplot)
            
            #print(outp)  
            #plt.plot(analysis['input1'],analysis.output)
            #plt.legend()
            #plt.show()
        
        else:
            #only 1 source
            x_outputplot=[]
            y_outputplot={}
            for i in analysis[source[0]]:
                x_outputplot.append(float("{:f}".format(float(str(i)[:-1]))))
            for i in range(len(seq)-1):
                n,name=seq[i].split('_')
                y_outputplot[n+'_'+name]=[]
        
                for a in analysis[node[seq[i]][-1]]:
                    y_outputplot[n+'_'+name].append(float("{:f}".format(float(str(a)[:-1]))))
                
                #plt.plot(analysis[source[0]],analysis[node[seq[i]][-1]],label =n+' '+name+'dc_output')
            #plt.plot(analysis[source[0]],analysis.output)
            #print(x_outputplot)
            #print(y_outputplot)
            #plt.legend()
            #plt.show()
        outputplot.objects.filter(outputplot_id=user_id+';'+circuit_name).filter(circuit_name=circuit_name).delete()
        outputplot.objects.update_or_create(outputplot_id=user_id+';'+circuit_name,circuit_name=circuit_name,user_id=user_id,typeOfAnalysis="dc",x=json.dumps(x_outputplot),y=json.dumps(y_outputplot))

 


def non_inv_opamp(n,inp,out,R1,RF):
    circuit.R('R1'+n, 'inverting_input'+n, circuit.gnd, R1)
    ##
    circuit.R('input'+n, inp, 'inverting_input'+n, 10@u_MΩ)
    circuit.VCVS('gain'+n, '1'+n, circuit.gnd, inp, 'inverting_input'+n, voltage_gain=kilo(1))
    circuit.R('P1'+n, '1'+n, '2'+n, 1@u_kΩ)
    circuit.VCVS('buffer'+n, '3'+n, circuit.gnd, '2'+n, circuit.gnd, '1'+n)
    circuit.R('out'+n, '3'+n, out, 10@u_Ω)
    ##
    circuit.R('RF'+n, 'inverting_input'+n, out, RF)

def inv_opamp(n,inp,out,R1,RF):
    circuit.R('R1'+n, inp, 'inverting_input'+n, R1)
    ##
    circuit.R('input'+n, circuit.gnd, 'inverting_input'+n, 10@u_MΩ)
    circuit.VCVS('gain'+n, '1'+n, circuit.gnd, circuit.gnd, 'inverting_input'+n, voltage_gain=kilo(1))
    circuit.R('P1'+n, '1'+n, '2'+n, 1@u_kΩ)
    circuit.VCVS('buffer'+n, '3'+n, circuit.gnd, '2'+n, circuit.gnd, '1'+n)
    circuit.R('out'+n, '3'+n, out, 10@u_Ω)
    ##
    circuit.R('RF'+n, 'inverting_input'+n, out, RF)
    #circuit.R('load_inv_opamp'+n, out, circuit.gnd, 10@u_Ω)

def full_wave_rectifier(n,inp,out):
    circuit.include(r"C:\Users\1N4148.lib")
    circuit.R('R1'+n, inp, 'inverting_input'+n, 1000@u_Ω)
    ##opamp
    circuit.R('input'+n, circuit.gnd, 'inverting_input'+n, 10@u_MΩ)
    circuit.VCVS('gain'+n, '1'+n, circuit.gnd, circuit.gnd, 'inverting_input'+n, voltage_gain=kilo(1))
    circuit.R('P1'+n, '1'+n, '2'+n, 1@u_kΩ)
    circuit.VCVS('buffer'+n, '3'+n, circuit.gnd, '2'+n, circuit.gnd, '1'+n)
    circuit.R('out'+n, '3'+n, 'output1'+n, 10@u_Ω)
    ##
    circuit.R('R2'+n, 'inverting_input'+n, 'node1'+n, 1000@u_Ω)
    circuit.X('D1'+n, '1N4148', 'node1'+n, 'output1'+n)
    ##opamp2
    circuit.R('input2'+n, 'non_inverting_input2'+n, 'inverting_input2'+n, 10@u_MΩ)
    circuit.VCVS('gain2'+n, '12'+n, circuit.gnd, 'non_inverting_input2'+n, 'inverting_input2'+n, voltage_gain=kilo(1))
    circuit.R('P12'+n, '12'+n, '22'+n, 1@u_kΩ)
    circuit.VCVS('buffer2'+n, '32'+n, circuit.gnd, '22'+n, circuit.gnd, '12'+n)
    circuit.R('out2'+n, '32'+n, out, 10@u_Ω)
    ##
    circuit.R('R3'+n, 'inverting_input'+n, 'non_inverting_input2'+n, 1000@u_Ω)
    circuit.X('D2'+n, '1N4148', 'output1'+n, 'non_inverting_input2'+n)
    circuit.R('R4'+n, 'node1'+n, 'inverting_input2'+n, 1000@u_Ω)
    circuit.R('R5'+n, 'inverting_input2'+n, out, 1000@u_Ω)


def half_wave_rectifier(n,inp,out):
    circuit.include(r"C:\Users\1N4148.lib")
    circuit.X('D1'+n, '1N4148', inp, out)
    circuit.R('load_half_wave'+n, out, circuit.gnd, 1000@u_kΩ)

def differentiator(n,inp,out,Cin,RF):
    circuit.C('Cin'+n,inp,'inverting_input'+n,Cin)
    ##
    circuit.R('input'+n, circuit.gnd, 'inverting_input'+n, 10@u_MΩ)
    circuit.VCVS('gain'+n, '1'+n, circuit.gnd, circuit.gnd, 'inverting_input'+n, voltage_gain=kilo(1))
    circuit.R('P1'+n, '1'+n, '2'+n, 1@u_kΩ)
    circuit.VCVS('buffer'+n, '3'+n, circuit.gnd, '2'+n, circuit.gnd, '1'+n)
    circuit.R('out'+n, '3'+n, out, 10@u_Ω)
     ##
    circuit.R('Rf'+n,'inverting_input'+n,out,RF)


def integrator(n,inp,out,Rin,RF,CF):
    circuit.R('Rin'+n,inp,'inverting_input'+n,Rin)
    ##
    circuit.R('input'+n, circuit.gnd, 'inverting_input'+n, 10@u_MΩ)
    circuit.VCVS('gain'+n, '1'+n, circuit.gnd, circuit.gnd, 'inverting_input'+n, voltage_gain=kilo(1))
    circuit.R('P1'+n, '1'+n, '2'+n, 1@u_kΩ)
    circuit.VCVS('buffer'+n, '3'+n, circuit.gnd, '2'+n, circuit.gnd, '1'+n)
    circuit.R('out'+n, '3'+n, out, 10@u_Ω)
    ##
    circuit.R('Rf'+n,'inverting_input'+n,out,RF)
    circuit.C('Cf'+n,'inverting_input'+n,out,CF)

def LowPassFilter(n,inp,out,R1_str,C1_str):
    R1 = circuit.R('R1'+n, inp, out, R1_str)
    C1 = circuit.C('C1'+n, out, circuit.gnd, C1_str)
    global break_frequency1
    break_frequency1 = 1 / (2 * math.pi * float(resistance_value(R1_str) * capacitance_value(C1_str)))

def HighPassFilter(n,inp,out,R1_str,C1_str):
    C1 = circuit.C('C1'+n, inp, out, C1_str)
    R1 = circuit.R('R1'+n,out, circuit.gnd , R1_str)

    global break_frequency1
    break_frequency1 = 1 / (2 * math.pi * float(resistance_value(R1_str) * capacitance_value(C1_str)))

def BandPassFilter(n,inp,out,R1_str,C1_str,R2_str,C2_str):
    R1=circuit.R('R1'+n, inp, 'node1'+n, R1_str)
    C1=circuit.C('C1'+n, 'node1'+n, 'inverting_input'+n, C1_str)
    ##
    circuit.R('Rinput'+n, circuit.gnd, 'inverting_input'+n, 10@u_MΩ)
    circuit.VCVS('gain'+n, '1'+n, circuit.gnd, circuit.gnd, 'inverting_input'+n, voltage_gain=kilo(1))
    circuit.R('P1'+n, '1'+n, '2'+n, 1@u_kΩ)
    circuit.VCVS('buffer'+n, '3'+n, circuit.gnd, '2'+n, circuit.gnd, '1'+n)
    circuit.R('out'+n, '3'+n, out, 10@u_Ω)
    ##
    R2=circuit.R('RF'+n, 'inverting_input'+n, out, R2_str)
    C2=circuit.C('CF'+n, 'inverting_input'+n, out, C2_str)
    global break_frequency1
    global break_frequency2
    print(resistance_value(R1_str),capacitance_value(C1_str),resistance_value(R2_str),capacitance_value(C2_str))
    break_frequency1 = 1 / (2 * math.pi * float(resistance_value(R1_str) * capacitance_value(C1_str)))
    break_frequency2 = 1 / (2 * math.pi * float(resistance_value(R2_str) * capacitance_value(C2_str)))

def BandStopFilter(n,inp,out,RLP_str,CLP_str,RHP_str,CHP_str,R1,R2,RF):
    RLP=circuit.R('RLP'+n, inp, 'non_inverting_inputLP'+n, RLP_str)
    CLP=circuit.C('CLP'+n, 'non_inverting_inputLP'+n, circuit.gnd,CLP_str)

    ##opamp1(LowPass Section)
    circuit.R('inputLP'+n, 'non_inverting_inputLP'+n, 'outputLP'+n, 10@u_MΩ)
    circuit.VCVS('gainLP'+n, '1LP'+n, circuit.gnd, 'non_inverting_inputLP'+n, 'outputLP'+n, voltage_gain=kilo(1))
    circuit.R('P1LP'+n, '1LP'+n, '2LP'+n, 1@u_kΩ)
    circuit.VCVS('bufferLP'+n, '3LP'+n, circuit.gnd, '2LP'+n, circuit.gnd, '1LP'+n)
    circuit.R('outLP'+n, '3LP'+n, 'outputLP'+n, 10@u_Ω)
    ##
    circuit.R('R1'+n, 'outputLP'+n, 'inverting_input'+n, R1)

    CHP=circuit.C('CHP'+n, inp, 'non_inverting_inputHP'+n, CHP_str)
    RHP=circuit.R('RHP'+n, 'non_inverting_inputHP'+n, circuit.gnd, RHP_str)


    ##opamp(HighPass Section)
    circuit.R('inputHP'+n, 'non_inverting_inputHP'+n, 'outputHP'+n, 10@u_MΩ)
    circuit.VCVS('gainHP'+n, '1HP'+n, circuit.gnd, 'non_inverting_inputHP'+n, 'outputHP'+n, voltage_gain=kilo(1))
    circuit.R('P1HP'+n, '1HP'+n, '2HP'+n, 1@u_kΩ)
    circuit.VCVS('bufferHP'+n, '3HP'+n, circuit.gnd, '2HP'+n, circuit.gnd, '1HP'+n)
    circuit.R('outHP'+n, '3HP'+n, 'outputHP'+n, 10@u_Ω)
    ##
    circuit.R('R2'+n, 'outputHP'+n, 'inverting_input'+n, R2)

    ##opamp final stage
    circuit.R('input'+n, circuit.gnd, 'inverting_input'+n, 10@u_MΩ)
    circuit.VCVS('gain'+n, '1'+n, circuit.gnd, circuit.gnd, 'inverting_input'+n, voltage_gain=kilo(1))
    circuit.R('P1'+n, '1'+n, '2'+n, 1@u_kΩ)
    circuit.VCVS('buffer'+n, '3'+n, circuit.gnd, '2'+n, circuit.gnd, '1'+n)
    circuit.R('out'+n, '3'+n, out, 10@u_Ω)
    ##
    circuit.R('RF'+n, 'inverting_input'+n, out, RF)

    global break_frequency1
    global break_frequency2
    break_frequency1 = 1 / (2 * math.pi * float(resistance_value(RHP_str)*capacitance_value(CHP_str)))
    break_frequency2 = 1 / (2 * math.pi * float(resistance_value(RLP_str)*capacitance_value(CLP_str)))




def difference_amplifier(n,inp1,inp2,out,R1,R2,R3,R4):
    circuit.R('R1'+n, inp1, 'inverting_input'+n, R1)
    circuit.R('R2'+n, inp2, 'non_inverting_input'+n, R2)
    circuit.R('R4'+n, 'non_inverting_input'+n, circuit.gnd, R4)
    ##
    circuit.R('input'+n, 'non_inverting_input'+n, 'inverting_input'+n, 10@u_MΩ)
    circuit.VCVS('gain'+n, '1'+n, circuit.gnd, 'non_inverting_input'+n, 'inverting_input'+n, voltage_gain=kilo(1))
    circuit.R('P1'+n, '1'+n, '2'+n, 1@u_kΩ)
    circuit.VCVS('buffer'+n, '3'+n, circuit.gnd, '2'+n, circuit.gnd, '1'+n)
    circuit.R('out'+n, '3'+n, out, 10@u_Ω)
    ##
    circuit.R('R3'+n, 'inverting_input'+n, out, R3)

def adder(n,inp1,inp2,out,R1,R2,RF):
    circuit.R('R1'+n, inp1, 'inverting_input'+n, R1)
    circuit.R('R2'+n, inp2, 'inverting_input'+n, R2)
    ##
    circuit.R('input'+n, circuit.gnd, 'inverting_input'+n, 10@u_MΩ)
    circuit.VCVS('gain'+n, '1'+n, circuit.gnd, circuit.gnd, 'inverting_input'+n, voltage_gain=kilo(1))
    circuit.R('P1'+n, '1'+n, '2'+n, 1@u_kΩ)
    circuit.VCVS('buffer'+n, '3'+n, circuit.gnd, '2'+n, circuit.gnd, '1'+n)
    circuit.R('out'+n, '3'+n, out, 10@u_Ω)
    ##
    circuit.R('RF'+n, 'inverting_input'+n, out, RF)

def subtractor(n,inp1,inp2,out,R1,R2,R3,RF):
    circuit.R('R1'+n, inp1, 'inverting_input'+n, R1)
    circuit.R('R2'+n, inp2, 'non_inverting_input'+n, R2)
    circuit.R('R3'+n, 'non_inverting_input'+n,circuit.gnd, R3)
    ##
    circuit.R('input'+n, 'non_inverting_input'+n, 'inverting_input'+n, 10@u_MΩ)
    circuit.VCVS('gain'+n, '1'+n, circuit.gnd, 'non_inverting_input'+n, 'inverting_input'+n, voltage_gain=kilo(1))
    circuit.R('P1'+n, '1'+n, '2'+n, 1@u_kΩ)
    circuit.VCVS('buffer'+n, '3'+n, circuit.gnd, '2'+n, circuit.gnd, '1'+n)
    circuit.R('out'+n, '3'+n, out, 10@u_Ω)
    ##
    circuit.R('RF'+n, 'inverting_input'+n,out, RF)

def inverting_schmitt(n, inp, out, R1, R2):
    circuit.include(r"C:\Users\LMV981.MOD")
    circuit.R('r2' + n, circuit.gnd, 'non_inverting_input' + n, R2)
    # opamp
    circuit.X('X1' + n, 'lmv981', 'non_inverting_input' + n, inp, 'positive_power_supply' + n,'negative_power_supply' + n, out, circuit.gnd)
    circuit.V('Vp' + n, 'positive_power_supply' + n, circuit.gnd, 15 @ u_V)
    circuit.V('Vn' + n, circuit.gnd, 'negative_power_supply' + n, 15 @ u_V)
    circuit.R('r1', 'non_inverting_input' + n, out, R1)

def comparator(n, inp, out, Vref):
   # comparator
   circuit.include(r"C:\Users\LM741.MOD")
   #circuit.V('vref' + n, 'inverting_input' + n, circuit.gnd, Vref)
   circuit.X('X1' + n, 'LM741/NS', inp, Vref, 'positive_power_supply' + n, 'negative_power_supply' + n,out)
   circuit.V('Vp' + n, 'positive_power_supply' + n, circuit.gnd, 15 @ u_V)
   circuit.V('Vn' + n, circuit.gnd, 'negative_power_supply' + n, 15 @ u_V)
   circuit.R('load' + n, out + n, circuit.gnd, 1 @ u_kΩ)

def non_inverting_schmitt(n, inp, out, R1, R2):
  circuit.include(r"C:\Users\LM741.MOD")

  circuit.R('r2' + n, inp, 'non_inverting_input' + n, R2)
  # opamp
  circuit.X('X1' + n, 'LM741/NS', 'non_inverting_input' + n, circuit.gnd, 'positive_power_supply' + n,
            'negative_power_supply' + n, out)
  circuit.V('Vp' + n, 'positive_power_supply' + n, circuit.gnd, 15 @ u_V)
  circuit.V('Vn' + n, circuit.gnd, 'negative_power_supply' + n, 15 @ u_V)
  circuit.R('r1' + n, 'non_inverting_input' + n, out, R1)

def dac(n,bit,r1,r12,rf,vin_names,out):
    circuit.include(r"C:\Users\LM741.MOD")
    circuit.R('r0', 'r0_1', circuit.gnd, r1)
    for i in range(1,bit+1):
        circuit.R('r'+str(i), 'r'+str(i-1)+'_1', 'r'+str(i)+'_2', r1)
        circuit.R('r'+str(i)+'_d','r'+str(i)+'_2',vin_names[bit-i],"1Ohm")
        circuit.R('r'+str(i)+'s','r'+str(i-1)+'_1', 'r'+str(i)+'_1', r12)
    circuit.X('X1', 'LM741/NS', circuit.gnd, 'r'+str(bit)+'_1', 'positive_power_supply', 'negative_power_supply', out)
    circuit.V('Vp', 'positive_power_supply', circuit.gnd, 15@u_V)
    circuit.V('Vn', circuit.gnd, 'negative_power_supply', 15@u_V)
    circuit.R('RF', out, 'r'+str(bit)+'_1', rf)

def comparator_adc(n,inv,non_inv, out):
#comparator
# AC 1 PWL(0US 0V  0.01US 1V)
    circuit.include(r"C:\Users\LM741.MOD")
    circuit.X('X1'+n, 'LM741/NS', non_inv, inv, 'positive_power_supply'+n, 'negative_power_supply'+n, out)
    circuit.V('Vp'+n, 'positive_power_supply'+n, circuit.gnd, 15@u_V)
    circuit.V('Vn'+n, circuit.gnd, 'negative_power_supply'+n, 15@u_V)
    circuit.R('load'+n, out, circuit.gnd, 100@u_kΩ)

def flash_adc(n, inp, bit, vref):
    #source=circuit.SinusoidalVoltageSource('input', 'in', circuit.gnd, amplitude=vin)
    global resolution
    resolution=bit
    #circuit.V('vin'+n, 'in'+n, circuit.gnd, vin)
    circuit.V('vref', 'r'+str(bit)+'_1', circuit.gnd, vref)
    circuit.R('r'+str(bit), 'r'+str(bit)+'_1', 'r'+str(bit)+'_2', 1@u_Ω)
    comparator_adc(str(bit), 'r'+str(bit)+'_2', inp, 'c'+str(bit))
    for i in range(bit-1,1,-1):
        if i==2:
            circuit.R('r'+str(i-1),'r'+str(i)+'_2', circuit.gnd, 1@u_Ω)
        circuit.R('r'+str(i),'r'+str(i+1)+'_2','r'+str(i)+'_2',1@u_Ω)
        comparator_adc(str(i), 'r'+str(i)+'_2', inp, 'c'+str(i))


#Driver code
'''
#test1
seq=["0_input","1_nonInvOpamp","2_nonInvOpamp","3_adder","4_FullWaveRectifier","5_Analysis"]

ip_values={"0_input":{"source_type":"sinusoidal","amplitude":"1V","frequency":"1kHz","terminal1":'1'},
           "1_nonInvOpamp":{"input_from":"0_input","R1":"100Ohm","RF":"300Ohm"},
           "2_nonInvOpamp":{"input_from":"0_input","R1":"100Ohm","RF":"200Ohm"},
           "3_adder":{"input1":"1_nonInvOpamp","input2":"2_nonInvOpamp","R1":"100Ohm","R2":"100Ohm","RF":"100Ohm"},
           "4_FullWaveRectifier":{"input_from":"3_adder"},
           "5_Analysis":{"type":"transient","start":0,"step":0.00001,"stop":0.005}}

#test2
seq=["0_input","1_nonInvOpamp","2_nonInvOpamp","3_Analysis"]

ip_values={"0_input":{"source_type":"sinusoidal","amplitude":"1V","frequency":"1kHz","terminal1":'1'},
           "1_nonInvOpamp":{"input_from":"0_input","R1":"100Ohm","RF":"300Ohm"},
           "2_nonInvOpamp":{"input_from":"0_input","R1":"100Ohm","RF":"200Ohm"},
           "3_Analysis":{"type":"transient","start":0,"step":0.00001,"stop":0.005}}



#test3
seq=["0_input","1_nonInvOpamp","2_nonInvOpamp","3_subtractor","4_HalfWaveRectifier","5_Analysis"]

ip_values={"0_input":{"source_type":"sinusoidal","amplitude":"1V","frequency":"1kHz","terminal1":'1'},
           "1_nonInvOpamp":{"input_from":"0_input","R1":"100Ohm","RF":"300Ohm"},
           "2_nonInvOpamp":{"input_from":"0_input","R1":"100Ohm","RF":"200Ohm"},
           "3_subtractor":{"input1":"1_nonInvOpamp","input2":"2_nonInvOpamp","R1":"100Ohm","R2":"100Ohm","R3":"100Ohm","RF":"100Ohm"},
           "4_HalfWaveRectifier":{"input_from":"3_subtractor"},
           "5_Analysis":{"type":"transient","start":0,"step":0.00001,"stop":0.005}}

#test4
seq=["0_Input","1_NonInvertingOpamp","2_HighPassFilter","3_Analysis"]

ip_values={"0_Input":{"source_type":"sinusoidal","amplitude":"1V","frequency":"1kHz","terminal1":'1'},
           "1_NonInvertingOpamp":{"input_from":"0_Input","R1":"100Ohm","RF":"200Ohm"},
           "2_HighPassFilter":{"input_from":"1_NonInvertingOpamp","R1":"1kOhm","C1":"1uF"},
           "3_Analysis":{"type":"ac","start":1,"step":0.00001,"stop":1000000}}


#test5
seq=["0_input","1_nonInvOpamp","2_BandStopFilter","3_Analysis"]

ip_values={"0_input":{"source_type":"sinusoidal","amplitude":"1V","frequency":"1kHz","terminal1":'1'},
           "1_nonInvOpamp":{"input_from":"0_input","R1":"100Ohm","RF":"200Ohm"},
           "2_BandStopFilter":{"input_from":"1_nonInvOpamp","RLP":"8kOhm","CLP":"0.1uF","RHP":"2kOhm","CHP":"0.1uF","R1":"10kOhm","R2":"10kOhm","RF":"20kOhm"},
           "3_Analysis":{"type":"ac","start":1,"step":0.00001,"stop":1000000}}

#test6
seq=["0_input","1_nonInvOpamp","2_integrator","3_Analysis"]

ip_values={"0_input":{"source_type":"sinusoidal","amplitude":"1V","frequency":"50Hz","terminal1":'1'},
           "1_nonInvOpamp":{"input_from":"0_input","R1":"100Ohm","RF":"200Ohm"},
           "2_integrator":{"input_from":"1_nonInvOpamp","Rin":"1kOhm","CF":"5uF"},
           "3_Analysis":{"type":"transient","start":0,"step":0.00001,"stop":0.05}}


#test7
seq=["0_input","1_nonInvOpamp","2_nonInvOpamp","3_differenceAmplifier","4_HalfWaveRectifier","5_Analysis"]

ip_values={"0_input":{"source_type":"sinusoidal","amplitude":"1V","frequency":"1kHz","terminal1":'1'},
           "1_nonInvOpamp":{"input_from":"0_input","R1":"100Ohm","RF":"300Ohm"},
           "2_nonInvOpamp":{"input_from":"0_input","R1":"100Ohm","RF":"200Ohm"},
           "3_differenceAmplifier":{"input1":"1_nonInvOpamp","input2":"2_nonInvOpamp","R1":"100Ohm","R2":"100Ohm","R3":"100Ohm","R4":"100Ohm"},
           "4_HalfWaveRectifier":{"input_from":"3_differenceAmplifier"},
           "5_Analysis":{"type":"transient","start":1,"step":0.0001,"stop":0.002}}
#test10
seq=["0_Input","1_NonInvertingOpamp","2_NonInvertingOpamp","3_Adder","4_FullWaveRectifier","5_Analysis"]
ip_values={"0_Input":{"source_type":"PWL","amplitude":"0","frequency":"0","initial_value":"0","pulsed_value":"0","pulse_width":"0","period":"0","pwl_string":"0.0s 0.0V 0.1s 0.09983341664682815V 0.2s 0.19866933079506122V 0.30000000000000004s 0.2955202066613396V 0.4s 0.3894183423086505V 0.5s 0.479425538604203V 0.6000000000000001s 0.5646424733950355V 0.7000000000000001s 0.6442176872376911V 0.8s 0.7173560908995228V 0.9s 0.7833269096274834V 1.0s 0.8414709848078965V 1.1s 0.8912073600614354V 1.2000000000000002s 0.9320390859672264V 1.3s 0.963558185417193V 1.4000000000000001s 0.9854497299884603V 1.5s 0.9974949866040544V 1.6s 0.9995736030415051V 1.7000000000000002s 0.9916648104524686V 1.8s 0.9738476308781951V 1.9000000000000001s 0.9463000876874145V 2.0s 0.9092974268256817V 2.1s 0.8632093666488737V 2.2s 0.8084964038195901V 2.3000000000000003s 0.74570521217672V 2.4000000000000004s 0.6754631805511506V 2.5s 0.5984721441039564V 2.6s 0.5155013718214642V 2.7s 0.4273798802338298V 2.8000000000000003s 0.33498815015590466V 2.9000000000000004s 0.23924932921398198V 3.0s 0.1411200080598672V 3.1s 0.04158066243329049V 3.2s -0.058374143427580086V 3.3000000000000003s -0.15774569414324865V 3.4000000000000004s -0.25554110202683167V 3.5s -0.35078322768961984V 3.6s -0.44252044329485246V 3.7s -0.5298361409084934V 3.8000000000000003s -0.6118578909427193V 3.9000000000000004s -0.6877661591839741V 4.0s -0.7568024953079282V 4.1000000000000005s -0.8182771110644108V 4.2s -0.8715757724135882V 4.3s -0.9161659367494549V 4.4s -0.9516020738895161V 4.5s -0.977530117665097V 4.6000000000000005s -0.9936910036334645V 4.7s -0.9999232575641008V 4.800000000000001s -0.9961646088358406V 4.9s -0.9824526126243325V 5.0s -0.9589242746631385V 5.1000000000000005s -0.9258146823277321V 5.2s -0.8834546557201531V 5.300000000000001s -0.8322674422239008V 5.4s -0.7727644875559871V 5.5s -0.7055403255703919V 5.6000000000000005s -0.6312666378723208V 5.7s -0.5506855425976376V 5.800000000000001s -0.4646021794137566V 5.9s -0.373876664830236V 6.0s -0.27941549819892586V 6.1000000000000005s -0.18216250427209502V 6.2s -0.0830894028174964V 6.300000000000001s 0.0168139004843506V 6.4s 0.11654920485049364V 6.5s 0.21511998808781552V 6.6000000000000005s 0.3115413635133787V 6.7s 0.4048499206165983V 6.800000000000001s 0.49411335113860894V 6.9s 0.5784397643882001V 7.0s 0.6569865987187891V 7.1000000000000005s 0.7289690401258765V 7.2s 0.7936678638491531V 7.300000000000001s 0.8504366206285648V 7.4s 0.8987080958116269V 7.5s 0.9379999767747389V 7.6000000000000005s 0.9679196720314865V 7.7s 0.9881682338770004V 7.800000000000001s 0.998543345374605V 7.9s 0.998941341839772V 8.0s 0.9893582466233818V 8.1s 0.9698898108450863V 8.200000000000001s 0.9407305566797726V 8.3s 0.9021718337562933V 8.4s 0.8545989080882805V 8.5s 0.7984871126234903V 8.6s 0.7343970978741133V 8.700000000000001s 0.662969230082182V 8.8s 0.5849171928917617V 8.9s 0.5010208564578846V 9.0s 0.4121184852417566V 9.1s 0.3190983623493521V 9.200000000000001s 0.22288991410024592V 9.3s 0.1244544235070617V 9.4s 0.024775425453357765V 9.5s -0.0751511204618093V 9.600000000000001s -0.1743267812229814V 9.700000000000001s -0.2717606264109442V 9.8s -0.3664791292519284V 9.9s -0.45753589377532133V ","terminal1":"in"},
            "1_NonInvertingOpamp":{"input_from":"0_Input","R1":"100Ohm","RF":"300Ohm"},
           "2_NonInvertingOpamp":{"input_from":"0_Input","R1":"100Ohm","RF":"200Ohm"},
           "3_Adder":{"input1":"1_NonInvertingOpamp","input2":"2_NonInvertingOpamp","R1":"100Ohm","R2":"100Ohm","RF":"100Ohm"},
           "4_FullWaveRectifier":{"input_from":"3_Adder"},
           "5_Analysis":{"type":"transient","start":0,"step":0.001,"stop":8}}

'''
seq=json.loads(sys.argv[1])
ip_values=json.loads(sys.argv[2])
user_id=sys.argv[3]
circuit_name=sys.argv[4]
#print(type(seq),type(ip_values))
node={}
c=1
for i in range(len(seq)):

    n,name=seq[i].split('_')

    if name=="Input":
        ##"0_input":{"source_type":"sinusoidal","amplitude":"1V","frequency":"1kHz","initial_value":"0","pulsed_value"="0","pulse_width"="0","period":"0","terminal1":'1'}
        ##"0_input":{"source_type":"pulse","amplitude":"0","frequency":"0","initial_value":"-1V","pulsed_value"="1V","pulse_width"="0.002s","period":"0.004s","terminal1":'1'}
        voltage_source('_'+seq[i],ip_values[seq[i]]["source_type"],ip_values[seq[i]]["amplitude"],ip_values[seq[i]]["frequency"],ip_values[seq[i]]["initial_value"],
                       ip_values[seq[i]]["pulsed_value"],ip_values[seq[i]]["pulse_width"],ip_values[seq[i]]["period"],ip_values[seq[i]]["pwl_string"],ip_values[seq[i]]["terminal1"])
        node[seq[i]]=[]
        node[seq[i]].append(ip_values[seq[i]]["terminal1"])

    elif name=="NonInvertingOpamp":
        ##"1_nonInvOpamp":{"input_from":"0_input","R1":"100Ohm","RF":"300Ohm"}
        inp=node[ip_values[seq[i]]["input_from"]][-1]
        #print(seq[i],inp,str(c+1),ip_values[seq[i]]["R1"],ip_values[seq[i]]["RF"])
        non_inv_opamp('_'+seq[i],inp,str(c+1),ip_values[seq[i]]["R1"],ip_values[seq[i]]["RF"])
        node[seq[i]]=[]
        node[seq[i]].append(inp)
        node[seq[i]].append(str(c+1))
        c=c+1

    elif name=="InvertingOpamp":
        ##"1_InvOpamp":{"input_from":"0_input","R1":"100Ohm","RF":"300Ohm"}
        inp=node[ip_values[seq[i]]["input_from"]][-1]
        #print(seq[i],inp,str(c+1),ip_values[seq[i]]["R1"],ip_values[seq[i]]["RF"])
        inv_opamp('_'+seq[i],inp,str(c+1),ip_values[seq[i]]["R1"],ip_values[seq[i]]["RF"])
        node[seq[i]]=[]
        node[seq[i]].append(inp)
        node[seq[i]].append(str(c+1))
        c=c+1

    elif name=="Adder":
        ##"3_adder":{"input1":"1_nonInvOpamp","input2":"2_nonInvOpamp","R1":"100Ohm","R2":"100Ohm","RF":"100Ohm"}
        inp1=node[ip_values[seq[i]]["input1"]][-1]
        inp2=node[ip_values[seq[i]]["input2"]][-1]
        adder('_'+seq[i],inp1,inp2,str(c+1),ip_values[seq[i]]["R1"],ip_values[seq[i]]["R2"],ip_values[seq[i]]["RF"])
        node[seq[i]]=[]
        node[seq[i]].append(inp1)
        node[seq[i]].append(inp2)
        node[seq[i]].append(str(c+1))
        c=c+1

    elif name=="Subtractor":
        ##"3_subtractor":{"input1":"1_nonInvOpamp","input2":"2_nonInvOpamp","R1":"100Ohm","R2":"100Ohm","R3":"100Ohm","RF":"100Ohm"}
        inp1=node[ip_values[seq[i]]["input1"]][-1]
        inp2=node[ip_values[seq[i]]["input2"]][-1]
        subtractor('_'+seq[i],inp1,inp2,str(c+1),ip_values[seq[i]]["R1"],ip_values[seq[i]]["R2"],ip_values[seq[i]]["R3"],ip_values[seq[i]]["RF"])
        node[seq[i]]=[]
        node[seq[i]].append(inp1)
        node[seq[i]].append(inp2)
        node[seq[i]].append(str(c+1))
        c=c+1

    elif name=="FullWaveRectifier":
        ##"4_FullWaveRectifier":{"input_from":"3_adder"}
        inp=node[ip_values[seq[i]]["input_from"]][-1]
        full_wave_rectifier('_'+seq[i],inp,c+1)
        node[seq[i]]=[]
        node[seq[i]].append(inp)
        node[seq[i]].append(str(c+1))
        c=c+1


    elif name=="HalfWaveRectifier":
        ##"4_HalfWaveRectifier":{"input_from":"3_adder"}
        inp=node[ip_values[seq[i]]["input_from"]][-1]
        half_wave_rectifier('_'+seq[i],inp,c+1)
        node[seq[i]]=[]
        node[seq[i]].append(inp)
        node[seq[i]].append(str(c+1))
        c=c+1

    elif name=="LowPassFilter":
        ##"1_LowPassFilter":{"input_from":"0_input","R1":"100Ohm","C1":"5uF"}
        inp=node[ip_values[seq[i]]["input_from"]][-1]
        LowPassFilter('_'+seq[i],inp,str(c+1),ip_values[seq[i]]["R1"],ip_values[seq[i]]["C1"])
        node[seq[i]]=[]
        node[seq[i]].append(inp)
        node[seq[i]].append(str(c+1))
        c=c+1

    elif name=="HighPassFilter":
        ##"1_HighPassFilter":{"input_from":"0_input","R1":"100Ohm","C1":"5uF"}
        inp=node[ip_values[seq[i]]["input_from"]][-1]
        HighPassFilter('_'+seq[i],inp,str(c+1),ip_values[seq[i]]["R1"],ip_values[seq[i]]["C1"])
        node[seq[i]]=[]
        node[seq[i]].append(inp)
        node[seq[i]].append(str(c+1))
        c=c+1

    elif name=="BandPassFilter":
        ##"1_BandPassFilter":{"input_from":"0_input","R1":"100Ohm","C1":"5uF","R2":"200Ohm","C2":"8uF"}
        inp=node[ip_values[seq[i]]["input_from"]][-1]
        BandPassFilter('_'+seq[i],inp,str(c+1),ip_values[seq[i]]["R1"],ip_values[seq[i]]["C1"],ip_values[seq[i]]["R2"],ip_values[seq[i]]["C2"])
        node[seq[i]]=[]
        node[seq[i]].append(inp)
        node[seq[i]].append(str(c+1))
        c=c+1

    elif name=="BandStopFilter":
        ##"1_BandStopFilter":{"input_from":"0_input","RLP":"100Ohm","CLP":"5uF","RHP":"200Ohm","CHP":"8uF","R1":"100Ohm","R2":"100Ohm","RF":"200Ohm"}
        inp=node[ip_values[seq[i]]["input_from"]][-1]
        BandStopFilter('_'+seq[i],inp,str(c+1),ip_values[seq[i]]["RLP"],ip_values[seq[i]]["CLP"],ip_values[seq[i]]["RHP"],ip_values[seq[i]]["CHP"],
                       ip_values[seq[i]]["R1"], ip_values[seq[i]]["R2"], ip_values[seq[i]]["RF"])
        node[seq[i]]=[]
        node[seq[i]].append(inp)
        node[seq[i]].append(str(c+1))
        c=c+1


    elif name=="Differentiator":
        ##"1_differentiator":{"input_from":"0_input","Cin":"5uF","RF":"300Ohm"}
        inp=node[ip_values[seq[i]]["input_from"]][-1]
        differentiator('_'+seq[i],inp,str(c+1),ip_values[seq[i]]["Cin"],ip_values[seq[i]]["RF"])
        node[seq[i]]=[]
        node[seq[i]].append(inp)
        node[seq[i]].append(str(c+1))
        c=c+1

    elif name=="Integrator":
        ##"1_integrator":{"input_from":"0_input","Rin":"100Ohm","CF":"5uF"}
        inp=node[ip_values[seq[i]]["input_from"]][-1]
        integrator('_'+seq[i],inp,str(c+1),ip_values[seq[i]]["Rin"],ip_values[seq[i]]["RF"],ip_values[seq[i]]["CF"])
        node[seq[i]]=[]
        node[seq[i]].append(inp)
        node[seq[i]].append(str(c+1))
        c=c+1

    elif name=="DifferenceAmplifier":
        ##"1_differenceAmplifier":{"input1":"0_input","input2":"0_nonInvOpamp","R1":"100Ohm","R2":"100Ohm","R3":"100Ohm","R4":"100Ohm"}
        inp1=node[ip_values[seq[i]]["input1"]][-1]
        inp2=node[ip_values[seq[i]]["input2"]][-1]
        subtractor('_'+seq[i],inp1,inp2,str(c+1),ip_values[seq[i]]["R1"],ip_values[seq[i]]["R2"],ip_values[seq[i]]["R3"],ip_values[seq[i]]["R4"])
        node[seq[i]]=[]
        node[seq[i]].append(inp1)
        node[seq[i]].append(inp2)
        node[seq[i]].append(str(c+1))
        c=c+1

    elif name == "InvertingSchmittTrigger":
        inp = node[ip_values[seq[i]]["input_from"]][-1]
        inverting_schmitt('_' + seq[i], inp, str(c + 1), ip_values[seq[i]]["R1"], ip_values[seq[i]]["R2"])
        node[seq[i]] = []
        node[seq[i]].append(inp)
        node[seq[i]].append(str(c+1))
        c=c+1

    elif name == "NonInvertingSchmittTrigger":
        inp = node[ip_values[seq[i]]["input_from"]][-1]
        inverting_schmitt('_' + seq[i], inp, str(c + 1), ip_values[seq[i]]["R1"], ip_values[seq[i]]["R2"])
        node[seq[i]] = []
        node[seq[i]].append(inp)
        node[seq[i]].append(str(c+1))
        c=c+1

    elif name == "Comparator":
        inp = node[ip_values[seq[i]]["input_from"]][-1]
        Vref= node[ip_values[seq[i]]["Vref"]][-1]
        comparator('_' + seq[i], inp, str(c + 1), Vref)
        node[seq[i]] = []
        node[seq[i]].append(inp)
        node[seq[i]].append(Vref)
        node[seq[i]].append(str(c+1))
        c=c+1

    elif name == "DAC":
        dac('_'+seq[i], ip_values[seq[i]]["bit"], ip_values[seq[i]]["R1"], ip_values[seq[i]]["R12"],ip_values[seq[i]]["RF"],ip_values[seq[i]]["vin_names"].split(','), str(c+1))
        node[seq[i]]=[]
        node[seq[i]].append(ip_values[seq[i]]["vin_names"])
        node[seq[i]].append(str(c+1))
        c+=1

    elif name == "FlashADC":
        inp = node[ip_values[seq[i]]["input_from"]][-1]
        flash_adc('_'+seq[i], inp, ip_values[seq[i]]["bit"], ip_values[seq[i]]["vref"])

##        node[seq[i]]=[]
##        node[seq[i]].append(inp)
##        node[seq[i]].append(str(c+1))
##        c+=1

    elif name=="Analysis":
        analysis_type(ip_values[seq[i]]["type"],ip_values[seq[i]]["start"],ip_values[seq[i]]["step"],ip_values[seq[i]]["stop"],node,ip_values[seq[i]]["source"])



'''
voltage_source("input1","sinusoidal","1V","1kHz",'1')

non_inv_opamp('_non_inv_opamp_1','1','2','100Ohm','300Ohm')
non_inv_opamp('_inv_opamp_2','1','3','100Ohm','200Ohm')
adder('_adder_1','2','3','4','100Ohm','100Ohm','100Ohm')
full_wave_rectifier('_full_wave_1','4','5')

analysis_type('transient',0,0.00001,0.005,node)
'''
#print(type(resistance_value('100Ohm')))
#print(capacitance_value('1nF'))
#print(circuit)
#save ngspice code to django model
#NgspiceCode.objects.all().delete()
NgspiceCode.objects.filter(code_id=user_id+';'+circuit_name).filter(circuit_name=circuit_name).delete()
NgspiceCode.objects.update_or_create(code_id=user_id+';'+circuit_name,circuit_name=circuit_name,user_id=user_id,code=str(circuit))
#print(node)



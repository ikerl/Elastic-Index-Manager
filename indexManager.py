#!/usr/bin/python
import requests
import json
import os
import re
import datetime
import sys

OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

print("""                         
.___            .___                 _____                                             
|   | ____    __| _/____ ___  ___   /     \ _____    ____ _____     ____   ___________ 
|   |/    \  / __ |/ __ \\\\  \/  /  /  \ /  \\\\__  \  /    \\\\__  \   / ___\_/ __ \_  __ \\
|   |   |  \/ /_/ \  ___/ >    <  /    Y    \/ __ \|   |  \/ __ \_/ /_/  >  ___/|  | \/
|___|___|  /\____ |\___  >__/\_ \ \____|__  (____  /___|  (____  /\___  / \___  >__|   
         \/      \/    \/      \/         \/     \/     \/     \//_____/      \/       
    
                                                               @ Iker Loidi""")
def isCompatible(index):
    if re.search('\d{4}-\d{2}', index) is not None or re.search('\d{2}-\d{4}', index) is not None:
        return True
    else:
        return False

def getPattern(index):
    try:
        if re.search('\d{4}-\d{2}', index) is not None:
            return index.replace(re.search('\d{4}-\d{2}', index).group(0),"#")
            #print("[+] Es del mes {} del ano {}".format(re.search('\d{4}-\d{2}', index).group(0).split("-")[1],re.search('\d{4}-\d{2}', index).group(0).split("-")[0]))
        if re.search('\d{2}-\d{4}', index) is not None:
            #print("[+] Es del mes {} del ano {}".format(re.search('\d{2}-\d{4}', index).group(0).split("-")[0],re.search('\d{2}-\d{4}', index).group(0).split("-")[1]))
            return str(index.replace(re.search('\d{2}-\d{4}', index).group(0),"#"))

    except:
            print("[-] Error al intentar identificar la fecha de {}".format(index))
    return None

def listIndices():
    n = 0
    array = list()
    print("[+] Buscando indices...\n")
    lista_json = json.loads(requests.get("http://localhost:9200/_cat/indices?format=json&pretty=true").text)
    for i,indice_linea in enumerate(lista_json):
        # Mirar si el indice contiene un patron de fecha-mes o mes-fecha
        if isCompatible(indice_linea['index']):
            compatible = "      [COMPATIBLE]     "
                    # Mirar si actualmente tiene un fichero de conf
            pattern = getPattern(indice_linea['index'])
            if os.path.exists("./config/{}".format(pattern)):
                            existe = "        ** Con conf **"
                            color = OKGREEN
            else:
                            existe = "        ** Sin conf **"
                            color = WARNING
            n += 1
            #print(color+str(n)+": "+str(pattern)+" -> "+indice_linea['index']+existe+ENDC)
            array.append(color+str(pattern)+existe+ENDC)
        else:
            compatible = "      [NO COMPATIBLE]    "
            color = FAIL
        #print(color+str(i)+": "+str(indice_linea['index']+existe+compatible+ENDC))

    for element in list(set(array)):
        print(element)
    print("")

def createConfig(index,tsClose,tsRem):
    data = {}
    data['index'] = index
    data['tsClose'] = tsClose
    data['tsRem'] = tsRem
    # Generando fichero
    f = open("./config/"+index, "w")
    f.write(json.dumps(data))
    f.close()
    print("[+] Fichero generado para el indice "+index)

def showConfig(index):
    try:
        f = open("./config/"+index,"r")
        json_data = json.loads(f.read())
        print("[+] Indice: {}\n[+] Se cerrara a los {} meses\n[+] Se borrara a los {} meses".format(json_data['index'],json_data['tsClose'],json_data['tsRem']))
    except:
        print("[-] Error al leer el fichero de configuracion")

def deleteConfig(index):
    try:
        os.remove("./config/"+index)
        print("[+] Configuracion del indice {} borrado".format(index))
    except:
        print("[-] Error al eliminar la configuracion del indice {}".format(index))	

def help():
    print("""
[+] Comandos:
    - list
    - show [nombre_indice]
        [Muestra la configuracion de este indice]
    - execute [nombre_indice]
        [Ejecuta la configuracion para este indice]
    - create [nombre_indice] [meses_cerrar] [meses_borrar]
        [Crea un fichero de configuracion para este indice (Si existe lo sobrescribe)]
    - delete [nombre_indice]
        [Elimina la configuracion de un indice]
    - exit
""")

def getMes(year,month):
    return int(year)*12+int(month)

def executeAll():
    try:
        for file in os.listdir("./config"):
            executeConfig(file)	
            print("[+] Ejecutando configuracion para {}".format(file))
    except:
        print("[-] Error al ejecutar ficheros de configuracion")
        
def executeConfig(index):
    try:
        f = open("./config/"+index,"r")
        json_data = json.loads(f.read())
        print("[+] Indice: {}\n[+] Se cerrara a los {} meses\n[+] Se borrara a los {} meses".format(json_data['index'],json_data['tsClose'],json_data['tsRem']))
        tsClose=int(json_data['tsClose'])
        tsRem=int(json_data['tsRem'])
        print("[+] Ejecutando la configuracion del indice patron {}".format(index))
        lista_json = json.loads(requests.get("http://localhost:9200/_cat/indices?format=json&pretty=true").text)
        for i,indice_linea in enumerate(lista_json):
            if isCompatible(indice_linea['index']) and getPattern(indice_linea['index']) == index: 
                print("[+] Encontrado el indice: {}".format(indice_linea['index']))
                try:
                    if re.search('\d{4}-\d{2}', indice_linea['index']) is not None:
                        print("[+] Es del mes {} del ano {}".format(re.search('\d{4}-\d{2}', indice_linea['index']).group(0).split("-")[1],re.search('\d{4}-\d{2}', indice_linea['index']).group(0).split("-")[0]))
                        indexMes = getMes(re.search('\d{4}-\d{2}', indice_linea['index']).group(0).split("-")[0],re.search('\d{4}-\d{2}', indice_linea['index']).group(0).split("-")[1])
                        today = datetime.datetime.today()
                        nowMes = getMes(today.year,today.month)
                        print("[*] Hoy es  el mes {} y el indice es del mes {}. Hay {} meses de diferencia".format(nowMes,indexMes,nowMes-indexMes))
                        if int(nowMes-indexMes) > int(json_data['tsClose']):
                            print(WARNING+"[+] Cerrando indice "+indice_linea['index']+ENDC)
                            print(requests.post("http://localhost:9200/{}/_close".format(str(indice_linea['index']))))
                        if int(nowMes-indexMes) > int(json_data['tsRem']):
                            print(FAIL+"[+] Borrando indice "+indice_linea['index']+ENDC)
                        
                        
                    if re.search('\d{2}-\d{4}', indice_linea['index']) is not None:
                        print("[+] Es del mes {} del ano {}".format(re.search('\d{2}-\d{4}', indice_linea['index']).group(0).split("-")[0],re.search('\d{2}-\d{4}', indice_linea['index']).group(0).split("-")[1]))
                        indexMes = getMes(re.search('\d{2}-\d{4}', indice_linea['index']).group(0).split("-")[1],re.search('\d{2}-\d{4}', indice_linea['index']).group(0).split("-")[0])
                        today = datetime.datetime.today()
                        nowMes = getMes(int(today.year),int(today.month))
                        print("[*] Hoy es  el mes {} y el indice es del mes {}. Hay {} meses de diferencia".format(nowMes,indexMes,nowMes-indexMes))
                        if int(nowMes-indexMes) > int(json_data['tsClose']):
                            print(WARNING+"[+] Cerrando indice "+indice_linea['index']+ENDC)
                            print(requests.post("http://localhost:9200/{}/_close".format(str(indice_linea['index']))))
                        if int(nowMes-indexMes) > int(json_data['tsRem']):
                            print(FAIL+"[+] Borrando indice "+indice_linea['index']+ENDC)

                except Exception as p:
                    print(p)
                    print("[-] Error al intentar identificar la fecha de {}".format(indice_linea['index']))
    except:
        print("[-] Error al abrir el fichero de configuracion {}".format(index))

def checkConfigDir():
    if not os.path.exists("config/"):
        try:
            os.mkdir("config")
        except:
            print("[-] No se ha podido crear el directorio de configuraciones")
            sys.exit(-1)


if len(sys.argv) > 1:
    if sys.argv[1] == "execute":
        executeAll()
        sys.exit(0)
    else:
        print("\n[-] Usar \"{} execute\" para ejecutar todos las configuraciones".format(sys.argv[0]))
        sys.exit(-1)

listIndices()

while(True):
    option = raw_input("> ")
    if "LIST" in option.upper():
        listIndices()
    if "EXIT" in option.upper():
        exit(0)
    if "HELP" in option.upper():
                help()
    if "CREATE" in option.upper():
        if len(option.split(" ")) != 4:
            print("[-] Usar: create [nombre_indice] [meses_cerrar] [meses_borrar]")
        else:
            createConfig(option.split(" ")[1],option.split(" ")[2],option.split(" ")[3])
    if "SHOW" in option.upper():
                if len(option.split(" ")) != 2:
                        print("[-] Usar: show [nombre_indice]")
                else:
                        showConfig(option.split(" ")[1])
    if "DELETE" in option.upper():
                if len(option.split(" ")) != 2:
                        print("[-] Usar: delete [nombre_indice]")
                else:
                        deleteConfig(option.split(" ")[1])
    if "EXECUTE" in option.upper():
                if len(option.split(" ")) != 2:
                        print("[-] Usar: execute [nombre_indice]")
                else:
                        executeConfig(option.split(" ")[1])

        


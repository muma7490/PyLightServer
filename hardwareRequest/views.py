from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect,HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist

import sys
import logging

from manageTools.models import ConnectedSystem,UsedIO,IO,IOType
from PyLightSupport.Commandos import *
from PyLightServer.tcpserver import sendDataToTCPServer

logger = logging.getLogger(__name__)

@csrf_exempt
def handleRequests(request):
    logger.info(f"Incoming request from tcp server. POST Data: {request.POST}")
    cmd = request.POST['cmd']
    logger.debug(f"Incoming command: {cmd}")
    data = cmd.split('||')

    cmdword = ""

    if data[0] == cmd_signup[0]:
        logger.info(f"Processing {cmd_signup[0]} with serial number {data[3]}")
        if len(ConnectedSystem.objects.filter(serialNumber=data[3])) == 0:
            logger.info(f"System with serial number {data[3]} not in database, adding new one")
            system = ConnectedSystem(name="Change me",lastIP=data[1],lastMacAddress=data[2]
                                ,serialNumber=data[3],connected=True,active=True)
            system.save()
            io = IO.objects.get(ioNr=0)
            ioType = IOType.objects.get(id=0)
            usedIO = UsedIO(name="",pin=io,type=ioType,connectedSystem=system)
            logger.info(f"Added system with {usedIO}")
            usedIO.save()
        else:
            logger.info(f"Changing system with serial number {data[3]} to IP {data[1]} and Mac {data[2]}")
            system = ConnectedSystem.objects.get(serialNumber=data[3])
            system.lastIP = data[1]
            system.lastMacAddress = data[2]
            system.connected = True
            system.save()

        cmdword = f"{system.lastIP}##{cmd_welcome[0]}||{system.name}"

    elif data[0] == cmd_client_disconnected[0]:
        logger.info(f"Client with ip {data[1]} disconnected")
        try:
            system = ConnectedSystem.objects.get(lastIP=data[1])
            system.connected = False
            system.save()
        except ObjectDoesNotExist:
            logger.error(f"object with ip {data[1]} does not exist. Existing ips: {ConnectedSystem.objects.values_list('lastIP')}")
            return HttpResponse()

    else:
        logger.error(f"Command {data[0]} not known by server, returning")
        return HttpResponse()


    if cmdword != "":
        logger.info(f"Sending returnWord {cmdword}")
        sendDataToTCPServer(cmdword)
    return HttpResponse()

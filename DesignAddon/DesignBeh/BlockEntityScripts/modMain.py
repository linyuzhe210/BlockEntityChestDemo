# -*- coding: UTF-8 -*-
from mod.common.mod import Mod
import mod.server.extraServerApi as serverApi
import mod.client.extraClientApi as clientApi


@Mod.Binding(name="LostWorld", version="0.2")
class TileEntityChest(object):

    def __init__(self):
        pass

    @Mod.InitClient()
    def initClient(self):
        clientApi.RegisterSystem('Design', 'BlockEntityClient',
                                 'BlockEntityScripts.ClientSystem.Main')

    @Mod.InitServer()
    def initServer(self):
        serverApi.RegisterSystem('Design', 'BlockEntityServer',
                                 'BlockEntityScripts.ServerSystem.Main')

    @Mod.DestroyClient()
    def destroyClient(self):
        pass

    @Mod.DestroyServer()
    def destroyServer(self):
        pass

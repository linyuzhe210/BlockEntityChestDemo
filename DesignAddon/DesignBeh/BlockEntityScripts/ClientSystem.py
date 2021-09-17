# -*- coding: UTF-8 -*-
from mod.client.system.clientSystem import ClientSystem
import mod.client.extraClientApi as clientApi
import time


class Main(ClientSystem):

    def __init__(self, namespace, system_name):
        ClientSystem.__init__(self, namespace, system_name)
        namespace = clientApi.GetEngineNamespace()
        system_name = clientApi.GetEngineSystemName()
        self.ListenForEvent(namespace, system_name, 'ClientBlockUseEvent', self, self.block_used)
        self.ListenForEvent(namespace, system_name, 'ChunkLoadedClientEvent', self, self.chunk_first_loaded)
        self.ListenForEvent(namespace, system_name, 'UiInitFinished', self, self.chunk_first_loaded)
        self.ListenForEvent('Design', 'BlockEntityServer', 'OpenChestFinished', self, self.chest_opened)
        self.ListenForEvent('Design', 'BlockEntityServer', 'InitChestRotation', self, self.chest_rotation)
        self.block_interact_cooldown = {}
        self.rotation_queue = []

    def block_used(self, event):
        player_id = event['playerId']
        block_name = event['blockName']
        x = event['x']
        y = event['y']
        z = event['z']
        if block_name == 'design:tileentity_chest':
            if player_id not in self.block_interact_cooldown:
                self.block_interact_cooldown[player_id] = time.time()
            elif time.time() - self.block_interact_cooldown[player_id] < 0.15:
                return
            else:
                self.block_interact_cooldown[player_id] = time.time()
            game_comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
            dimension_id = game_comp.GetCurrentDimension()
            self.NotifyToServer('TryOpenChest', {'dimensionId': dimension_id, 'pos': [x, y, z]})

    def chest_opened(self, event):
        data = event['data']
        block_comp = clientApi.GetEngineCompFactory().CreateBlockInfo(clientApi.GetLevelId())
        for block_data in data:
            block_pos = tuple(block_data['pos'])
            block_comp.SetBlockEntityMolangValue(block_pos, "variable.mod_states", float(block_data['states']))

    '''
    [踩过的一些坑]
    1、设置自定义方块实体渲染的Molang值时，该方块必须在玩家客户端已加载区块里才能设置
    2、因此出现两种情况：①玩家第一次登陆时，若在客户端上已加载的区块存在方块实体，需要向服务端请求数据后回传并设置Molang值。
    ②若第一次登陆时，所加载的区块外存在需要设置Molang的自定义方块实体模型，则需要后续游戏时，在方块所在区块加载后才能设置。
    3、若服务端回应慢，则会出现灾难现象（eg. 客户端已加载区块，但没有获得服务端的方块实体数据，无法正常渲染方块实体动画）。
    4、会导致服务端传输数据量非常大。
    5、优化方案暂时不写。
    '''
    def chunk_first_loaded(self, event):
        self.NotifyToServer('GetChestInit', {'playerId': clientApi.GetLocalPlayerId()})

    '''
    [灾难级别消耗]
    这样子写没有好果汁吃，非常卡
    '''
    # def chunk_loaded(self, event):
    #     chunk_pos_x = event['chunkPosX']
    #     chunk_pos_z = event['chunkPosZ']
    #     block_info_comp = clientApi.GetEngineCompFactory().CreateBlockInfo(clientApi.GetLevelId())
    #     data = []
    #     for x in xrange(chunk_pos_x, chunk_pos_x + 16):
    #         for z in xrange(chunk_pos_z, chunk_pos_z + 16):
    #             for y in xrange(0, 256):
    #                 block_data = block_info_comp.GetBlock((x, y, z))
    #                 if block_data[0] == 'design:tileentity_chest':
    #                     data.append('{},{},{}'.format(x, y, z))
    #     if data:
    #         self.NotifyToServer('GetChestInit', {'playerId': clientApi.GetLocalPlayerId(), 'data': data})

    def chest_rotation(self, event):
        print event
        new_event = {tuple(map(int, k.split(','))): v for k, v in event.items()}
        block_comp = clientApi.GetEngineCompFactory().CreateBlockInfo(clientApi.GetLevelId())

        def rotate_chest():
            index = 0
            count = len(new_event.items())
            for pos, data in new_event.items():
                block_data = block_comp.GetBlock(pos)
                if block_data[0] == 'design:tileentity_chest':
                    block_comp.SetBlockEntityMolangValue(pos, "variable.mod_rotation", data['rotation'])
                    block_comp.SetBlockEntityMolangValue(pos, "variable.mod_invert", float(data['invert']) if data['invert'] != 0 else 0.0)
                    index += 1
                    if index == count:
                        return True
            else:
                return False
        if new_event:
            # 事件触发时，可能会出现此时方块在客户端渲染完成，但无法设置方块的Molang的情况。
            # 因此我们在这边加入函数调用的计数，当满足至少设置两次朝向Molang的条件后，再弹出函数地址
            self.rotation_queue.append([rotate_chest, 0])
            # self.rotation_queue.append(rotate_chest)

    def Update(self):
        # 记录即将完成设置朝向任务的函数所处在列表的下标值
        _die = []
        for index, value in enumerate(self.rotation_queue):
            if value[0]():
                value[1] += 1
                if value[1] == 2:
                    _die.append(index)
        # for index, value in enumerate(self.rotation_queue):
        #     if value():
        #         _die.append(index)
        # 将完成任务的函数所在的元素设置为None
        for i in _die:
            self.rotation_queue[i] = None
        # 过滤掉用None占位的列表元素
        if self.rotation_queue:
            self.rotation_queue = filter(None, self.rotation_queue)
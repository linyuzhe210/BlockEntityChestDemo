# -*- coding: UTF-8 -*-
from mod.server.system.serverSystem import ServerSystem
from mod.common.minecraftEnum import Facing
import mod.server.extraServerApi as serverApi


class Main(ServerSystem):

    def __init__(self, namespace, system_name):
        ServerSystem.__init__(self, namespace, system_name)
        namespace = serverApi.GetEngineNamespace()
        system_name = serverApi.GetEngineSystemName()
        self.ListenForEvent(namespace, system_name, 'EntityPlaceBlockAfterServerEvent', self, self.on_placed)
        self.ListenForEvent(namespace, system_name, 'ServerEntityTryPlaceBlockEvent', self, self.on_try_placed)
        self.ListenForEvent(namespace, system_name, 'BlockRemoveServerEvent', self, self.block_removed)
        self.ListenForEvent('Design', 'BlockEntityClient', 'TryOpenChest', self, self.try_open_chest)
        self.ListenForEvent('Design', 'BlockEntityClient', 'GetChestInit', self, self.init_chest_rotation)

    def on_try_placed(self, event):
        x = event['x']
        y = event['y']
        z = event['z']
        block_name = event['fullName']
        dimension_id = event['dimensionId']
        face = event['face']
        if face == Facing.Up and block_name == 'design:tileentity_chest':
            block_data = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId()).GetBlockNew((x, y - 1, z), dimension_id)
            if block_data['name'] == block_name:
                event['cancel'] = True

    def on_placed(self, event):
        dimension_id = event['dimensionId']
        x = event['x']
        y = event['y']
        z = event['z']
        block_name = event['fullName']
        player_id = event['entityId']
        if block_name == 'design:tileentity_chest':
            player_rot = serverApi.GetEngineCompFactory().CreateRot(player_id).GetRot()
            block_data_comp = serverApi.GetEngineCompFactory().CreateBlockEntityData(serverApi.GetLevelId())
            block_data = block_data_comp.GetBlockEntityData(dimension_id, (x, y, z))
            if block_data:
                block_data['rotation'] = self.get_block_facing(player_rot)
                block_data['states'] = 0
                block_data['invert'] = 0
                # TODO 搭配自定义箱子UI时，只允许一个玩家操作箱子
                block_data['opener'] = ''
                block_info_comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId())
                post_data = {}
                if block_data['rotation'] % 2 == 0.0:
                    for i in range(-1, 2, 2):
                        block_info_data = block_info_comp.GetBlockNew(
                            (x + i, y, z),
                            dimension_id
                        )
                        if block_info_data['name'] == 'design:tileentity_chest':
                            connect_block_data = block_data_comp.GetBlockEntityData(dimension_id, (x + i, y, z))
                            if connect_block_data['invert'] == 0 and connect_block_data['rotation'] == block_data['rotation']:
                                block_data['invert'] = i * int(block_data['rotation'] - 1)
                                connect_block_data['invert'] = -i * int(block_data['rotation'] - 1)
                                post_data['{0},{1},{2}'.format(x + i, y, z)] = {'rotation': connect_block_data['rotation'], 'invert': connect_block_data['invert']}
                                break
                if block_data['rotation'] % 2 == 1.0:
                    for i in range(-1, 2, 2):
                        block_info_data = block_info_comp.GetBlockNew(
                            (x, y, z + i),
                            dimension_id
                        )
                        if block_info_data['name'] == 'design:tileentity_chest':
                            connect_block_data = block_data_comp.GetBlockEntityData(dimension_id, (x, y, z + i))
                            if connect_block_data['invert'] == 0 and connect_block_data['rotation'] == block_data['rotation']:
                                block_data['invert'] = i * int(block_data['rotation'] - 2)
                                connect_block_data['invert'] = -i * int(block_data['rotation'] - 2)
                                post_data['{0},{1},{2}'.format(x, y, z + i)] = {'rotation': connect_block_data['rotation'], 'invert': connect_block_data['invert']}
                                break
                level_data_comp = serverApi.GetEngineCompFactory().CreateExtraData(serverApi.GetLevelId())
                data = level_data_comp.GetExtraData(block_name)
                if not data:
                    data = {}
                post_data['{0},{1},{2}'.format(x, y, z)] = {'rotation': block_data['rotation'], 'invert': block_data['invert']}
                data['{0},{1},{2}'.format(x, y, z)] = {'rotation': block_data['rotation'], 'invert': block_data['invert']}
                data.update(post_data)
                level_data_comp.SetExtraData(block_name, data)
                self.BroadcastToAllClient('InitChestRotation', post_data)

    def block_removed(self, event):
        block_name = event['fullName']
        x = event['x']
        y = event['y']
        z = event['z']
        dimension_id = event['dimension']
        if block_name == 'design:tileentity_chest':
            block_data_comp = serverApi.GetEngineCompFactory().CreateBlockEntityData(serverApi.GetLevelId())
            block_entity_data = block_data_comp.GetBlockEntityData(0, (x, y, z))
            level_data_comp = serverApi.GetEngineCompFactory().CreateExtraData(serverApi.GetLevelId())
            data = level_data_comp.GetExtraData(block_name)
            post_data = {}
            if block_entity_data['invert'] != 0:
                block_info_comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId())
                if block_entity_data['rotation'] % 2 == 0.0:
                    for i in range(-1, 2, 2):
                        block_info_data = block_info_comp.GetBlockNew(
                            (x + i, y, z),
                            dimension_id
                        )
                        if block_info_data['name'] == 'design:tileentity_chest':
                            connect_block_data = block_data_comp.GetBlockEntityData(dimension_id, (x + i, y, z))
                            if connect_block_data['invert'] != 0 and connect_block_data['rotation'] == block_entity_data['rotation']:
                                connect_block_data['invert'] = 0
                                data['{0},{1},{2}'.format(x + i, y, z)] = {'rotation': connect_block_data['rotation'], 'invert': connect_block_data['invert']}
                                post_data['{0},{1},{2}'.format(x + i, y, z)] = {'rotation': connect_block_data['rotation'], 'invert': connect_block_data['invert']}
                if block_entity_data['rotation'] % 2 == 1.0:
                    for i in range(-1, 2, 2):
                        block_info_data = block_info_comp.GetBlockNew(
                            (x, y, z + i),
                            dimension_id
                        )
                        if block_info_data['name'] == 'design:tileentity_chest':
                            connect_block_data = block_data_comp.GetBlockEntityData(dimension_id, (x, y, z + i))
                            if connect_block_data['invert'] != 0 and connect_block_data['rotation'] == block_entity_data['rotation']:
                                connect_block_data['invert'] = 0
                                data['{0},{1},{2}'.format(x, y, z + i)] = {'rotation': connect_block_data['rotation'], 'invert': connect_block_data['invert']}
                                post_data['{0},{1},{2}'.format(x, y, z + i)] = {'rotation': connect_block_data['rotation'], 'invert': connect_block_data['invert']}
            data = data.pop('{0},{1},{2}'.format(x, y, z), data)
            level_data_comp.SetExtraData(block_name, data)
            self.BroadcastToAllClient('InitChestRotation', post_data)

    def init_chest_rotation(self, event):
        player_id = event['playerId']
        level_data_comp = serverApi.GetEngineCompFactory().CreateExtraData(serverApi.GetLevelId())
        data = level_data_comp.GetExtraData('design:tileentity_chest')
        if data:
            '''不要这样子写'''
            # if 'data' in event:
            #     client_data = event['data']
            #     data = {i: data[i] for i in client_data if i in data}
            self.NotifyToClient(player_id, 'InitChestRotation', data)

    def try_open_chest(self, event):
        pos = tuple(event['pos'])
        dimension_id = event['dimensionId']
        block_data_comp = serverApi.GetEngineCompFactory().CreateBlockEntityData(serverApi.GetLevelId())
        block_info_comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId())
        up_pos = (pos[0], pos[1] + 1, pos[2])
        up_block_data = block_info_comp.GetBlockNew(up_pos, dimension_id)
        if up_block_data['name'] != 'minecraft:air':
            return
        block_data = block_data_comp.GetBlockEntityData(dimension_id, pos)
        post_data = []
        if not block_data['states']:
            block_data['states'] = 1
        else:
            block_data['states'] = 0
        post_data.append({'pos': list(pos), 'dimensionId': dimension_id, 'states': block_data['states']})
        if block_data['invert'] != 0:
            connect_pos = list(pos)
            if block_data['rotation'] % 2 == 0.0:
                connect_pos[0] += block_data['invert'] * int(block_data['rotation'] - 1)
            if block_data['rotation'] % 2 == 1.0:
                connect_pos[2] += block_data['invert'] * int(block_data['rotation'] - 2)
            block_data_comp.GetBlockEntityData(dimension_id, tuple(connect_pos))['states'] = block_data['states']
            post_data.append({'pos': connect_pos, 'dimensionId': dimension_id, 'states': block_data['states']})
        self.BroadcastToAllClient('OpenChestFinished', {'data': post_data})

    def get_block_facing(self, rot):
        if 135.0 < rot[1] <= 180.0:
            return 2.0
        elif 45.0 < rot[1] <= 135.0:
            return 1.0
        elif -45.0 < rot[1] <= 45.0:
            return 0.0
        elif -135.0 < rot[1] <= -45.0:
            return 3.0
        elif -180.0 < rot[1] <= -135.0:
            return 2.0
        else:
            return 0.0

import re

helpmsg = '''------MCR 坐标点插件------
命令帮助如下:
!!warp help -显示帮助消息
!!warp add [名称] -添加当前位置为坐标点
!!warp list -获取挂机玩家名单以及显示注释
--------------------------------'''
exist = '''------ 温馨提示 ------
当前坐标点已存在
请选择其它名称
--------------------------------'''
success = '''------ 添加成功 ------
坐标点添加成功
可以通过输入!!warp list
读取所有坐标点
--------------------------------'''


def on_info(server, info):
    warp_in_list = 0
    PlayerInfoAPI = server.get_plugin_instance('PlayerInfoAPI')
    if info.is_player == 1:
        if info.content.startswith('!!warp'):
            args = info.content.split(' ')
            if len(args) == 1:
                for line in helpmsg.splitlines():
                    server.tell(info.player, line)
            elif args[1] == 'help':
                for line in helpmsg.splitlines():
                    server.tell(info.player, line)
            elif args[1] == 'add':
                warp_name = args[2]
                for data in open("config/data.txt"):
                    if warp_name in data:
                        warp_in_list = 1
                    else:
                        warp_in_list = 0
                if warp_in_list == 1:
                    for line2 in exist.splitlines():
                        server.tell(info.player, line2)
                else:
                    result = PlayerInfoAPI.getPlayerInfo(server, info.player, path='Pos')
                    pos1 = int(result[0])
                    pos2 = int(result[1])
                    pos3 = int(result[2])
                    with open("config/data.txt", 'a+') as f:
                        f.writelines('\n' + warp_name + " Pos: " + str(pos1) + ', ' + str(pos2) + ', ' + str(pos3))
                    f.close()
                    for line3 in success.splitlines():
                        server.tell(info.player, line3)
            elif args[1] == 'list':
                for list_warp in open("config/data.txt"):
                    server.tell(info.player, list_warp)

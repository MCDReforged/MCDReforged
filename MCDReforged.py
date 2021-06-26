mima='Fallen'
c=input('TIS的腐竹是：')
if c == mima:
#大佬的启动命令
    time.sleep(1.5)
    import sys

    from mcdreforged.__main__ import main

    if __name__ == '__main__':
	    sys.exit(main())
#密码错误的后果
else:
    b= ['              _                               ',
        '             /#\                              ',
        '             | |                              ',
        '             | |                              ',
        '           __|#|__ __                         ',
        '          |  | |  |  |                        ',
        '          |  | |  |  |                        ',]
    a=-1
    for _ in range(7):
        a+=1
        time.sleep(0.06)
        print(b[a])

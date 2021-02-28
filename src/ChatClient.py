import socket
import threading
import tkinter
import tkinter.font as ft
import tkinter.messagebox
from tkinter.scrolledtext import ScrolledText
import json
import time
import os
import re

from package.TkDnD import TkDnD


IP = '' # 服务器IP
PORT = ''   # 服务器Port
user = ''   # 用户名
chatWith = '#@[GROUP]@#'  # 聊天对象, 默认为群聊
users = []  # 在线用户列表


''' 登录窗口 '''
# 图形界面
loginWin = tkinter.Tk()
loginWin.title('Mini Chatroom')
loginWin.geometry('380x500')
loginWin.resizable(0, 0)  # 限制窗口大小
BgColor = '#E0FFFF'
textColor = '#4169E1'
loginWin['bg'] = BgColor

# 字体设置
titleFont = ft.Font(family='Times', size=30, weight=ft.BOLD, slant=ft.ITALIC)
textFont = ft.Font(family='Microsoft YaHei', size=12, weight=ft.BOLD, slant=ft.ROMAN)
inputFont = ft.Font(family='Microsoft YaHei', size=10, weight=ft.NORMAL, slant=ft.ROMAN)

# 标题标签
labelTitle = tkinter.Label(loginWin, text='Mini Chatroom', bg=BgColor, fg=textColor, font=titleFont)
labelTitle.place(x=50, y=40)

# 服务器IP标签
serverIP = tkinter.StringVar()
serverIP.set('139.196.201.152') # 默认显示的服务器IP
labelIP = tkinter.Label(loginWin, text='Server  IP', bg=BgColor, fg=textColor, font=textFont)
labelIP.place(x=140, y=130)
entryIP = tkinter.Entry(loginWin, width=80, textvariable=serverIP, font=inputFont)
entryIP.place(x=120, y=170, width=150, height=30)

# 服务器Port标签
serverPort = tkinter.StringVar()
serverPort.set('6666')  # 默认显示的服务器Port
labelPort = tkinter.Label(loginWin, text='Server  Port', bg=BgColor, fg=textColor, font=textFont)
labelPort.place(x=130, y=210)
entryPort = tkinter.Entry(loginWin, width=80, textvariable=serverPort, font=inputFont)
entryPort.place(x=120, y=250, width=150, height=30)

# 用户名标签
userName = tkinter.StringVar()
userName.set('')    # 默认显示的用户名为空
labelUserName = tkinter.Label(loginWin, text='Username', bg=BgColor, fg=textColor, font=textFont)
labelUserName.place(x=140, y=290)
entryUserName = tkinter.Entry(loginWin, width=80, textvariable=userName, font=inputFont)
entryUserName.place(x=120, y=330, width=150, height=30)


# 登录按钮
def login(*args):
    global IP, PORT, user

    IP = entryIP.get()
    PORT = int(entryPort.get())
    user = entryUserName.get()
    if not user:
        tkinter.messagebox.showerror('ERROR', message='Empty Username!')
    else:
        loginWin.destroy()  # 关闭窗口


loginWin.bind('<Return>', login)    # 回车绑定login函数
loginButton = tkinter.Button(loginWin, text='Log in', command=login, bg=textColor, fg='white', \
                             font=textFont, activebackground='#191970', activeforeground='white')    # 按钮绑定login函数
loginButton.place(x=150, y=400, width=80, height=40)

loginWin.mainloop()


''' 进行TCP连接 '''
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((IP, PORT))
addr = sock.getsockname()  # 获取客户端(IP,port)

if user:
    sock.send(user.encode())   # 发送用户名
else:
    sock.send('default'.encode())  # 没有输入用户名则标记default
    user = addr[0] + ':' + str(addr[1]) # 用户没有输入用户名，默认IP:port作为用户名


''' 聊天窗口 '''
# 图形界面
mainWin = tkinter.Tk()
mainWin.title('Mini Chatroom [ Group Chat ]')
mainWin.geometry('900x720')
mainWin.resizable(0, 0)    # 限制窗口大小
mainWin['bg'] = BgColor

# 创建多行文本框
chatbox = ScrolledText(mainWin)
chatbox.place(x=20, y=20, width=860, height=460)

chatFont = ft.Font(family='Microsoft YaHei', size=12, weight=ft.NORMAL, slant=ft.ROMAN)
chatbox.configure(font=chatFont)
# 文本框使用的字体颜色
sysFont = ft.Font(family='Microsoft YaHei', size=12, weight=ft.NORMAL, slant=ft.ITALIC)
chatbox.tag_config('sys', foreground='black', font=sysFont) # 系统输出
chatbox.insert(tkinter.END, 'Welcome to Mini Chatroom!\n', 'sys')

chatbox.tag_config('mg', foreground='#4169E1')  # 自己@所有人
chatbox.tag_config('og', foreground='#9400D3') # 别人@所有人
chatbox.tag_config('mo', foreground='#008B45')    # 自己@别人
chatbox.tag_config('om', foreground='#FF3030') # 别人@自己


''' *** 功能实现 *** '''
# 当前功能 0:text(default) / 1:emoji / 2:file
status = 0

# 输入文本框（默认place）
iptText = tkinter.Text(mainWin, width=120)
iptText.place(x=20, y=560, width=750, height=140)
iptFont = ft.Font(family='Microsoft YaHei', size=12, weight=ft.NORMAL, slant=ft.ROMAN)
iptText.configure(font=iptFont)

# 表情包选择按钮列表
selectButs = []

# 文件列表
filebox = tkinter.Listbox(mainWin, font=iptFont)

# 文件删除按钮
textFont = ft.Font(family='Microsoft YaHei', size=12, weight=ft.BOLD, slant=ft.ROMAN)
deleteBut = tkinter.Button(mainWin, text='Delete', command=lambda x=filebox: x.delete(tkinter.ACTIVE), \
                           bg='#FF3030', fg='white', font=textFont, activebackground='#8B1A1A', activeforeground='white')

# 拖动标志
textFont = ft.Font(family='Microsoft YaHei', size=12, weight=ft.BOLD, slant=ft.ITALIC)
dragLabel = tkinter.Label(mainWin, text='<<<   Drag your files here', bg=BgColor, fg=textColor, font=textFont)


# 发送文件函数
def sendFile():
    global filebox

    for i in range(filebox.size()):
        filename = filebox.get(i)
        with open(filename, 'rb') as f:
            while True:
                data = f.read(1024)
                if not data:
                    break
                info = '$;$' + user + '$;$' + chatWith
                data = '#@[FILE]@#'.encode() + data + info.encode()
                sock.send(data)
                time.sleep(0.1)

        msg = '<EOF>' + '$;$' + user + '$;$' + chatWith
        sock.send(msg.encode())
        time.sleep(0.1)

        msg = '#@[ENDFILE]@#' + filename.split('/')[-1] + '$;$' + user + '$;$' + chatWith
        sock.send(msg.encode())
        time.sleep(0.1)


    filebox.delete(0, tkinter.END)    # 发送后清空filebox


# 发送文件按钮
textFont = ft.Font(family='Microsoft YaHei', size=12, weight=ft.BOLD, slant=ft.ROMAN)
sendFileBut = tkinter.Button(mainWin, text='Send Files', command=sendFile, bg='#00CD00', fg='white', \
                         font=textFont, activebackground='#008B00', activeforeground='white')


# 发送文本函数
def send(*args):
    global iptText

    users.append('#@[GROUP]@#')
    if chatWith not in users:
        tkinter.messagebox.showerror('ERROR', message='Cannot chat with nobody!')
        return
    if chatWith == user:
        tkinter.messagebox.showerror('ERROR', message='Cannot chat with yourself in private!')
        return

    msg = iptText.get(1.0, tkinter.END)
    if not msg.strip():
        tkinter.messagebox.showerror('ERROR', message='Cannot send nothing!')
        return

    msg = msg + '$;$' + user + '$;$' + chatWith
    sock.send(msg.encode())
    iptText.delete(1.0, tkinter.END)    # 发送后清空文本框


# 发送按钮（默认place）
textFont = ft.Font(family='Microsoft YaHei', size=12, weight=ft.BOLD, slant=ft.ROMAN)
sendBut = tkinter.Button(mainWin, text='Send', command=send, bg='#00CD00', fg='white', \
                         font=textFont, activebackground='#008B00', activeforeground='white')
sendBut.place(x=795, y=605, width=80, height=40)
mainWin.bind('<Return>', send)  # 绑定回车发送信息


# 选择输入文本功能
def inputText():
    global iptText, selectButs, filebox, deleteBut, status

    if status == 0:
        return
    elif status == 1:
        for i in range(10):
            selectButs.pop().destroy()
    elif status == 2:
        filebox.place_forget()
        deleteBut.place_forget()
        dragLabel.place_forget()
        sendFileBut.place_forget()

    iptText.place(x=20, y=560, width=750, height=140)
    sendBut.place(x=795, y=605, width=80, height=40)
    status = 0

# 文本按钮（默认place）
textFont = ft.Font(family='Microsoft YaHei', size=12, weight=ft.BOLD, slant=ft.ROMAN)
textBut = tkinter.Button(mainWin, text='Text', command=inputText, bg=textColor, fg='white', \
                         font=textFont, activebackground='#191970', activeforeground='white')
textBut.place(x=30, y=500, width=80, height=40)


# 表情包图片列表
emojis = [tkinter.PhotoImage(file='./emoji/'+f) for f in os.listdir('./emoji')] # 打开表情包图片，存入emojis列表中


# 发送表情包函数, 由选择按钮selectButs[i]触发
def sendEmoji(i):
    msg = '#@[EMOJI]@#' + str(i) + '$;$' + user + '$;$' + chatWith
    sock.send(msg.encode())


# 选择表情包函数，由表情包按钮emojiBut触发
def selectEmoji():
    global selectButs, iptText, sendBut, filebox, deleteBut, status

    if status == 1:
        return
    elif status == 0:
        iptText.place_forget()
        sendBut.place_forget()
    elif status == 2:
        filebox.place_forget()
        deleteBut.place_forget()
        dragLabel.place_forget()
        sendFileBut.place_forget()

    # 不能用循环变量生成button，command传参有误！
    selectButs.append(tkinter.Button(mainWin, command=lambda:sendEmoji(0), image=emojis[0], relief=tkinter.FLAT, bd=0, bg=BgColor))
    selectButs.append(tkinter.Button(mainWin, command=lambda:sendEmoji(1), image=emojis[1], relief=tkinter.FLAT, bd=0, bg=BgColor))
    selectButs.append(tkinter.Button(mainWin, command=lambda:sendEmoji(2), image=emojis[2], relief=tkinter.FLAT, bd=0, bg=BgColor))
    selectButs.append(tkinter.Button(mainWin, command=lambda:sendEmoji(3), image=emojis[3], relief=tkinter.FLAT, bd=0, bg=BgColor))
    selectButs.append(tkinter.Button(mainWin, command=lambda:sendEmoji(4), image=emojis[4], relief=tkinter.FLAT, bd=0, bg=BgColor))
    selectButs.append(tkinter.Button(mainWin, command=lambda:sendEmoji(5), image=emojis[5], relief=tkinter.FLAT, bd=0, bg=BgColor))
    selectButs.append(tkinter.Button(mainWin, command=lambda:sendEmoji(6), image=emojis[6], relief=tkinter.FLAT, bd=0, bg=BgColor))
    selectButs.append(tkinter.Button(mainWin, command=lambda:sendEmoji(7), image=emojis[7], relief=tkinter.FLAT, bd=0, bg=BgColor))
    selectButs.append(tkinter.Button(mainWin, command=lambda:sendEmoji(8), image=emojis[8], relief=tkinter.FLAT, bd=0, bg=BgColor))
    selectButs.append(tkinter.Button(mainWin, command=lambda:sendEmoji(9), image=emojis[9], relief=tkinter.FLAT, bd=0, bg=BgColor))

    for i in range(10):
        selectButs[i].place(x=30+85*i, y=590)
    status = 1


# 表情包按钮（默认place）
textFont = ft.Font(family='Microsoft YaHei', size=12, weight=ft.BOLD, slant=ft.ROMAN)
emojiBut = tkinter.Button(mainWin, text='Emoji', command=selectEmoji, bg=textColor, fg='white', \
                          font=textFont, activebackground='#191970', activeforeground='white')
emojiBut.place(x=130, y=500, width=80, height=40)


# 拖动文件函数
def DragFile():
    global filebox, status

    if status == 2:
        return
    elif status == 0:
        iptText.place_forget()
        sendBut.place_forget()
    elif status == 1:
        for i in range(10):
            selectButs.pop().destroy()

    filebox.place(x=20, y=560, width=500, height=140)
    dragLabel.place(x=520, y=580)
    deleteBut.place(x=560, y=650, width=80, height=40)
    sendFileBut.place(x=720, y=650, width=120, height=40)
    status = 2


# 文件按钮（默认place）
textFont = ft.Font(family='Microsoft YaHei', size=12, weight=ft.BOLD, slant=ft.ROMAN)
fileBut = tkinter.Button(mainWin, text='File', command=DragFile, bg=textColor, fg='white', \
                          font=textFont, activebackground='#191970', activeforeground='white')
fileBut.place(x=230, y=500, width=80, height=40)


# 拖动组件及绑定
dnd = TkDnD(mainWin)

def drop(files):
    global dnd

    if isinstance(files, str):
        files = re.sub(u"{.*?}", "", files).split() # 通过空格切分多文件，所以文件名中不能有空格

    for file in files:
        filebox.insert(tkinter.END, (file))

dnd.bindtarget(filebox, 'text/uri-list', '<Drop>', drop, ('%D',))


''' 在线用户列表 '''
# 创建多行文本框, 显示在线用户
userbox = tkinter.Listbox(mainWin)

textFont = ft.Font(family='Microsoft YaHei', size=12, weight=ft.BOLD, slant=ft.ROMAN)
userbox.configure(font=textFont, bg=BgColor)
userbox.place(x=650, y=20, width=270, height=460)
isUserPanel = 0    # 判断在线用户列表面板开关的标志，0为关

def UserBox():
    global userbox, isUserPanel
    if isUserPanel == 1:
        userbox.place(x=650, y=20, width=270, height=460)
        isUserPanel = 0
    else:
        userbox.place_forget()  # 隐藏控件
        isUserPanel = 1


# 查看在线用户按钮
textFont = ft.Font(family='Microsoft YaHei', size=12, weight=ft.BOLD, slant=ft.ROMAN)
userBut = tkinter.Button(mainWin, text='Users', command=UserBox, bg=textColor, fg='white', \
                         font=textFont, activebackground='#191970', activeforeground='white')
userBut.place(x=795, y=500, width=80, height=40)


''' 私聊功能 '''
def private(*args):
    global chatWith

    # 获取点击的索引，得到用户名
    indexs = userbox.curselection()
    index = indexs[0]
    if index > 1:
        # 修改客户端名称
        if userbox.get(index) == '[ Group Chat ]':
            chatWith = '#@[GROUP]@#'
            mainWin.title('Mini Chatroom [ Group Chat ]')
        else:
            chatWith = userbox.get(index).rstrip(' [ user ]')
            mainWin.title('Mini Chatroom [ Private Chat with ' + chatWith + ']')


# 在显示用户列表框上设置绑定事件
userbox.bind('<ButtonRelease-1>', private)

# 文件数据（二进制），设为全局变量，用于数据拼接
fileData = b''

''' 接收信息并打印 '''
def recv():
    global users, fileData, fileMemory, ddl
    while True:
        data = sock.recv(1024)

        if data.startswith(b'#@[FILE]@#'):  # 文件
            fileData += data.split(b'$;$')[0].replace(b'#@[FILE]@#', b'')

            while True:
                data = sock.recv(1024)

                if b'<EOF>' in data:
                    fileData += data[:data.find(b'<EOF>')]
                    break
                else:
                    fileData += data.split(b'$;$')[0].replace(b'#@[FILE]@#', b'')
            continue


        try:    # 在线用户列表，若为消息则有异常捕获过程
            data = data.decode()
            users = json.loads(data)
            userbox.delete(0, tkinter.END)  # 清空列表框
            userbox.insert(tkinter.END, ('        Users online:  ' + str(len(users))))
            userbox.insert(tkinter.END, (user + ' [ myself ]'))
            userbox.insert(tkinter.END, '[ Group Chat ]')
            userbox.itemconfig(tkinter.END, fg='green')
            for i in range(len(users)):
                if users[i] != user:
                    userbox.insert(tkinter.END, (users[i] + ' [ user ]'))
                    userbox.itemconfig(tkinter.END, fg='green')

        except: # 消息
            try:
                data = data.split('$;$')
                msg = data[0].strip() # 消息
                sender = data[1]    # 发送者
                receiver = data[2]  # 接收者（群聊为'#@[GROUP]@#'，否则为user）
            except:
                tkinter.messagebox.showerror('ERROR', message='This program CANNOT receive message like $;$!')
                return

            color = ''
            if receiver == '#@[GROUP]@#':   # 群聊
                if sender == user:  # 自己->所有人
                    color = 'mg'
                    chatbox.insert(tkinter.END, '[myself] @ [all] :\n', color)
                else:   # 别人->所有人
                    color = 'og'
                    chatbox.insert(tkinter.END, sender + ' @ [all] :\n', color)
            else:   # 私聊
                if sender == user:  # 自己->别人
                    color = 'mo'
                    chatbox.insert(tkinter.END, '[myself] @ ' + receiver + ' :\n', color)
                elif receiver == user:   # 别人->自己
                    color = 'om'
                    chatbox.insert(tkinter.END, sender + ' @ [myself] :\n', color)
                else:   # 别人->别人（不显示）
                    continue


            if msg.startswith('#@[EMOJI]@#'):   # 表情
                chatbox.image_create(tkinter.END, image=emojis[int(msg[-1])])
                chatbox.insert(tkinter.END, '\n', color)

            elif msg.startswith('#@[ENDFILE]@#'):   # 文件结束
                chatbox.insert(tkinter.END, '[File] ' + msg[13:] + '\n', color)
                if not os.path.isdir('./download'):
                    os.mkdir('./download')
                with open('./download/' + msg[13:], 'wb') as f:
                    f.write(fileData)
                fileData = b''

            else:   # 一般消息
                chatbox.insert(tkinter.END, msg + '\n', color)

            chatbox.see(tkinter.END)  # 显示在最后


# 创建线程用于实时接收信息
r = threading.Thread(target=recv)
r.start()

mainWin.mainloop()
sock.close()  # 关闭图形界面后断开TCP连接

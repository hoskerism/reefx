#!/user/bin/python

import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('raspberrypi', 58394))
# Remember to escape special characters (<, >, &)
s.sendall('<SOCKETREQUEST><CODE>STATUS_REQUEST</CODE><CALLER>Web</CALLER><IP_ADDRESS>192.168.xxx.xxx</IP_ADDRESS>')
s.sendall("</SOCKETREQUEST>")
buf = s.recv(1024)
print buf
s.close()

"""
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('raspberrypi', 58394))
# Should be able to split the request and still receive it all at the other end
# Remember to escape special characters (<, >, &)
s.sendall('<SOCKETREQUEST><CODE>PROGRAM_REQUEST</CODE><CALLER>Web</CALLER><IP_ADDRESS>192.168.xxx.xxx</IP_ADDRESS><WORKER>DisplayLightingController</WORKER>')
s.sendall("<VALUE>ON_ONE_HOUR</VALUE></SOCKETREQUEST>")
buf = s.recv(1024)
print buf
s.close()
"""
"""
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('raspberrypi', 58394))
# Should be able to split the request and still receive it all at the other end
# Remember to escape special characters (<, >, &)
s.sendall('<SOCKETREQUEST><CODE>PROGRAM_REQUEST</CODE><CALLER>Web</CALLER><IP_ADDRESS>192.168.xxx.xxx</IP_ADDRESS><WORKER>Wavemaker</WORKER>')
s.sendall("<VALUE>FEEDING_10_MINUTES</VALUE></SOCKETREQUEST>")
buf = s.recv(1024)
print buf
s.close()
"""

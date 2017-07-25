from __future__ import print_function
import time
from msvcrt import kbhit, getch
import sys
import os
import datetime

project_dir = os.getcwd()
if project_dir[-1] in ['\\', '/']: project_dir = project_dir[:-1]
program_dir = os.path.abspath(__file__+'/..')
if program_dir[-1] in ['\\', '/']: program_dir = program_dir[:-1]
project_name = os.path.split(project_dir)[-1]

#print(project_dir)
#print(program_dir)
#print(project_name)

def semicol_to_sec(str_in):
    return sum([int(st)*([60*60,60,1][i]) for i,st in enumerate(str_in.strip().split(":"))])
    
def sec_to_semicol(seconds):
    return str(datetime.timedelta(seconds=seconds))
    


def kbfunc():
    #this is boolean for whether the keyboard has bene hit
    x = kbhit()
    if x:
        #getch acquires the character encoded in binary ASCII
        ret = getch()
        return ret.decode()
    else:
        return False

        
# coding: utf-8
"""
    VLCClient
    ~~~~~~~~~
    This module allows to control a VLC instance through a python interface.
    You need to enable the telnet interface, e.g. start
    VLC like this:
    $ vlc --intf telnet --telnet-password admin
    To start VLC with allowed remote admin:
    $ vlc --intf telnet --telnet-password admin \
      --lua-config "telnet={host='0.0.0.0:4212'}"
    Replace --intf with --extraintf to start telnet and the regular GUI
    More information about the telnet interface:
    http://wiki.videolan.org/Documentation:Streaming_HowTo/VLM
    :author: Michael Mayr <michael@dermitch.de>
    :licence: MIT License
    :version: 0.2.0
"""

import sys
import inspect
import telnetlib

DEFAULT_PORT = 4212


class VLCClient(object):
    """
    Connection to a running VLC instance with telnet interface.
    """

    def __init__(self, server, port=DEFAULT_PORT, password="admin", timeout=5):
        self.server = server
        self.port = port
        self.password = password
        self.timeout = timeout

        self.telnet = None
        self.server_version = None
        self.server_version_tuple = ()

    def connect(self):
        """
        Connect to VLC and login
        """
        assert self.telnet is None, "connect() called twice"

        self.telnet = telnetlib.Telnet()
        self.telnet.open(self.server, self.port, self.timeout)

        # Parse version
        result = self.telnet.expect([
            r"VLC media player ([\d.]+)".encode("utf-8"),
        ])
        self.server_version = result[1].group(1)
        self.server_version_tuple = self.server_version.decode("utf-8").split('.')

        # Login
        self.telnet.read_until("Password: ".encode("utf-8"))
        self.telnet.write(self.password.encode("utf-8"))
        self.telnet.write("\n".encode("utf-8"))

        # Password correct?
        result = self.telnet.expect([
            "Password: ".encode("utf-8"),
            ">".encode("utf-8")
        ])
        if "Password".encode("utf-8") in result[2]:
            raise WrongPasswordError()

    def disconnect(self):
        """
        Disconnect and close connection
        """
        self.telnet.close()
        self.telnet = None

    def _send_command(self, line):
        """
        Sends a command to VLC and returns the text reply.
        This command may block.
        """
        self.telnet.write((line + "\n").encode("utf-8"))
        return self.telnet.read_until(">".encode("utf-8"))[1:-3]

    def _require_version(self, command, version):
        """
        Check if the server runs at least at a specific version
        or raise an error.
        """
        if isinstance(version, basestring):
            version = version.split('.')
        if version > self.server_version_tuple:
            raise OldServerVersion(
                "Command '{0} requires at least VLC {1}".format(
                    command, ".".join(version)
            ))

    #
    # Commands
    #
    def help(self):
        """Returns the full command reference"""
        return self._send_command("help")

    def status(self):
        """current playlist status"""
        self._require_version("status", "2.0.0")
        return self._send_command("status")

    def get_time(self):
        """current playlist status"""
        #self._require_version("status", "2.0.0")
        return self._send_command("get_time")
    
    def stats(self):
        """current playlist status"""
        #self._require_version("status", "2.0.0")
        return self._send_command("stats")
    
    def info(self):
        """information about the current stream"""
        return self._send_command("info")
    
    def longhelp(self):
        return self._send_command("longhelp")
    
    
    def set_fullscreen(self, value):
        """set fullscreen on or off"""
        assert type(value) is bool
        return self._send_command("fullscreen {}".format("on" if value else "off"))

    def raw(self, *args):
        """
        Send a raw telnet command
        """
        return self._send_command(" ".join(args))

    #
    # Playlist
    #
    def add(self, filename):
        """
        Add a file to the playlist and play it.
        This command always succeeds.
        """
        return self._send_command('add {0}'.format(filename))

    def enqueue(self, filename):
        """
        Add a file to the playlist. This command always succeeds.
        """
        return self._send_command("enqueue {0}".format(filename))

    def seek(self, second):
        """
        Jump to a position at the current stream if supported.
        """
        return self._send_command("seek {0}".format(second))

    def play(self):
        """Start/Continue the current stream"""
        return self._send_command("play")

    def pause(self):
        """Pause playing"""
        self.play()
        return self._send_command("pause")

    def stop(self):
        """Stop stream"""
        return self._send_command("stop")

    def rewind(self):
        """Rewind stream"""
        return self._send_command("rewind")

    def next(self):
        """Play next item in playlist"""
        return self._send_command("next")

    def prev(self):
        """Play previous item in playlist"""
        return self._send_command("prev")

    def clear(self):
        """Clear all items in playlist"""
        return self._send_command("clear")

    #
    # Volume
    #
    def volume(self, vol=None):
        """Get the current volume or set it"""
        if vol:
            return self._send_command("volume {0}".format(vol))
        else:
            return self._send_command("volume").strip()

    def volup(self, steps=1):
        """Increase the volume"""
        return self._send_command("volup {0}".format(steps))

    def voldown(self, steps=1):
        """Decrease the volume"""
        return self._send_command("voldown {0}".format(steps))


class WrongPasswordError(Exception):
    """Invalid password sent to the server."""
    pass


class OldServerVersion(Exception):
    """VLC version is too old for the requested commmand."""
    pass

if __name__ == "__main__":
    import subprocess
    subprocess.Popen(program_dir+r'\VLCPortable\vlcPortable --extraintf telnet --telnet-password admin --sub-filter=logo@recording:logo@slides', shell=True)
    #time.sleep(14)
    while(1):
        time.sleep(1)
        print("Trying to connect to vlc...")
        try:
            vlc = VLCClient("::1")
            vlc.connect()
            break
        except ConnectionRefusedError:
            pass
    viddir , _ ,files = next(os.walk(project_dir+r'\video'))
    files = [f for f in files if f[-4:].lower() in ['.mp4', '.mkv', '.avi']]
    vlc.add(os.path.join(viddir, files[0]))

    class timingFile:
        def __init__(self, txtfilename):
            try:
                with open(txtfilename, 'r') as f: pass
            except:
                with open(txtfilename, 'w') as f: f.write('0:0:0->000.png')
            subprocess.Popen(program_dir+r'\sublime\subl %s'%txtfilename, shell=True)
            
            self.txtfilename = txtfilename
            self.cur_filestr = ""
            self.cur_filename = ""
            self.times = []
        def update(self):
            with open(self.txtfilename, 'r') as f: filestr =  f.read()
            if self.cur_filestr!=filestr:
                self.cur_filestr=filestr
                self.times=[[semicol_to_sec(i.split('->')[0]), i.split('->')[1]] 
                           for i in filestr.split('\n') if i.strip()!='']
                return True
            else:
                return False
        def write_new_timestamp(self, time, filename):
            self.update()
            self.times.append([time, filename])
            self.times.sort()
            with open(self.txtfilename, 'w') as f:
                
                f.write('\n'.join([sec_to_semicol(tim[0])+'->'+tim[1]
                                                      for tim in self.times]))
            
        def slide_seeker(self):
            vlctime = int(vlc.get_time())
            if len(self.times) > 0:
                filename = self.times[0][1]
                for tim, filn in self.times:
                    if tim <= vlctime:
                        filename = filn
                    else: break
                #vlc._send_command(r"@slides logo-file slides_files\%s"%filename)
                if self.cur_filename!=filename or vlctime<2:
                    vlc._send_command(r"@slides logo-file "+project_dir+r"\slides\%s"%filename)
                    vlc._send_command(r"@slides logo-y 15")
                    vlc._send_command(r"@slides logo-x 0")
                    self.cur_filename=filename
                else: pass
                    
    class streamSelector:
        def __init__(self, txtfilename):
            try:
                with open(txtfilename, 'r') as f: pass
            except:
                with open(txtfilename, 'w') as f: f.write('0:0:0->1')
            subprocess.Popen(program_dir+r'\sublime\subl %s'%txtfilename, shell=True)
            
            self.txtfilename = txtfilename
            self.cur_filestr = ""
            self.cur_channel = 1
            self.times = []
        def update(self):
            with open(self.txtfilename, 'r') as f: filestr =  f.read()
            if self.cur_filestr!=filestr:
                self.cur_filestr=filestr
                self.times=[[semicol_to_sec(i.split('->')[0]), i.split('->')[1]] 
                           for i in filestr.split('\n') if i.strip()!='']
                return True
            else:
                return False
        def write_new_timestamp(self, time, channel):
            self.update()
            self.times.append([time, str(channel)])
            self.times.sort()
            with open(self.txtfilename, 'w') as f:
                
                f.write('\n'.join([sec_to_semicol(tim[0])+'->'+tim[1]
                                                      for tim in self.times]))
            
        def stream_seeker(self):
            vlctime = int(vlc.get_time())
            if len(self.times) > 0:
                channel = int(self.times[0][1])
                for tim, filn in self.times:
                    if tim <= vlctime:
                        channel = int(filn)
                    else: break
                
                if self.cur_channel!=channel or vlctime<2:
                    vlc._send_command(r'@recording logo-file '+program_dir+r'\indicators\recording.png')
                    if channel==1:
                        vlc._send_command(r"@recording logo-x 200")
                    elif channel==2:
                        vlc._send_command(r"@recording logo-x 950")

                    self.cur_channel=channel
                    
                else: pass
    
    do_stream = False
    if     len(sys.argv) > 1:
        if sys.argv[1] == "stream":
            do_stream = True
            
    if do_stream:
        print('\n***********************************************************')
        print(  '* Ratio Christi video selector                            *')
        print(  '* Select left/right by pressing 1 or 2 in this black box  *')
        print(  '*                                                         *')
        print(  '***********************************************************')
    else:
        print('\n*****************************************************************')
        print(  '* Ratio Christi slides syncing                                  *')
        print(  '* Start selecting a slide by pressing any key in this black box *')
        print(  '*                                                               *')
        print(  '*****************************************************************')
    

    timings = timingFile(project_dir+r'\slide_timings--%s.txt'%project_name)
    streams = streamSelector(project_dir+r'\streams_timings--%s.txt'%project_name)

    while(1):
        time.sleep(0.05)
        vlctime = int(vlc.get_time())
        timings.update()
        streams.update()
        
        keypress = kbfunc()
        if keypress:
            try:
                int(keypress)
            except: 
                print('Error... you need to press a number.')
            else:
                if do_stream:
                    if int(keypress) in [1,2]:
                        streams.write_new_timestamp(vlctime, keypress)
                        print('Time '+sec_to_semicol(vlctime)+' channel: '+keypress)
                else:
                    vlc.pause()
                    vlctime = int(vlc.get_time())
                    print('For time '+sec_to_semicol(vlctime)+' the slide number is?: '+keypress, end='')
                    keypress = keypress+input('')
                    
                    try:
                        int(keypress)
                    except:
                        print('Error... you need to press a number.')
                    else:
                        timings.write_new_timestamp(vlctime,'%03d.png'%int(keypress))
                    vlc.play()
            
        timings.update()
        streams.update()
        timings.slide_seeker()
        if do_stream:
            streams.stream_seeker()
    

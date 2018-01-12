# coding: utf-8 # Maya is using Python 2.7.x so we need to specify the encoding in either the first or the second line of the source file.
"""
<MIT License>
Copyright © 2017-2018 by Moka Studio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

The Software is provided “as is”, without warranty of any kind,
express or implied, including but not limited to the warranties of merchantability,
fitness for a particular purpose and noninfringement.
In no event shall the authors or copyright holders be liable for any claim,
damages or other liability, whether in an action of contract, tort or otherwise,
arising from, out of or in connection with the software or
the use or other dealings in the Software.
</MIT License>
"""

from __future__ import unicode_literals
"""
Mosketch for maya.
See https://github.com/MokaStudio/MosketchForMaya for more informations.
For developers you can check the following link:
https://support.mokastudio.com/support/solutions/articles/6000198416-streaming-developer-documentation
"""

import os, sys, locale

import json

import pymel.core as pmc
import maya.OpenMayaUI as OpenMayaUI
import maya.mel as mel
import socket

# Support for Qt4 and Qt5 depending on Maya version
from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets
from Qt import __version__
from Qt import QtNetwork

from Qt import __binding__
if __binding__ in ('PySide2', 'PyQt5'):
    from shiboken2 import wrapInstance
elif __binding__ in ('PySide', 'PyQt4'):
    from shiboken import wrapInstance
else:
    _print_error("cannot find Qt bindings")


################################################################################
##########          GLOBAL VARIABLES
################################################################################
SCRIPT_VER = "0.6"
MAIN_WINDOW = None
CONNECTION = None
IP = "127.0.0.1"
MOSKETCH_PORT = 16094

# Keys for Json packets
JSON_KEY_TYPE = "Type"
JSON_KEY_NAME = "Name"
JSON_KEY_ANATOMIC = "Anatom"
JSON_KEY_ROTATION = "R"
JSON_KEY_TRANSLATION = "T"
JSON_KEY_JOINTS = "Joints"
JSON_KEY_OBJECT = "object"
JSON_KEY_COMMAND = "command"
JSON_KEY_PARAMETERS = "parameters"

# Packet Type
PACKET_TYPE_COMMAND = "MosketchCommand"

# MAYA JOINTS BUFFERS
JOINTS_BUFFER = {}
JOINTS_INIT_ORIENT_INV_BUFFER = {}
JOINTS_ROTATE_AXIS_INV_BUFFER = {}
INTER_JOINTS_BUFFER = {}
JOINTS_UUIDS = {}

# Utils
PI = 3.1415926535897932384626433832795
RAD_2_DEG = 180.0 / PI

# Verbose level (1 for critical informations, 3 to output all packets)
VERBOSE = 1


################################################################################
##########          MAIN FUNCTIONS
################################################################################
def install():
    """
    Call this function to install Mosketch for Maya
        mosketch_for_maya.install()
    """
    shelf_name = "MosketchForMaya"

    # First get maya "official" shelves layout
    top_level_shelf_layout = mel.eval("global string $gShelfTopLevel; $temp = $gShelfTopLevel;")
    # Get all shelves
    shelf_layout = pmc.shelfLayout(shelf_name, parent=top_level_shelf_layout)
    start_icon_name = os.path.dirname(os.path.abspath(__file__)) + "/start.png"
    stop_icon_name = os.path.dirname(os.path.abspath(__file__)) + "/stop.png"
    pmc.shelfButton(label='Start',
                    parent=shelf_layout, 
                    image1=start_icon_name, 
                    command='import mosketch_for_maya;reload(mosketch_for_maya);mosketch_for_maya.start()')
    pmc.shelfButton(label='Stop',
                    parent=shelf_layout,
                    image1=stop_icon_name,
                    command='mosketch_for_maya.stop()')


def start():
    """
    Call this function from Maya (in a shelf button or in script editor for example):
        import mosketch_for_maya
        mosketch_for_maya.start()
    """
    _create_gui()


def stop():
    """
    Call this function from Maya (in a shelf button or in script editor for example):
        mosketch_for_maya.stop()
    """
    if CONNECTION is not None:
        _close_connection()

    _destroy_gui()


################################################################################
##########          UI CLASS DEFINITION 
################################################################################
class UI_MosketchWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        maya_window = _get_maya_main_window()
        super(UI_MosketchWindow, self).__init__(maya_window)

    def init_mosketch_ui(self):
        self.setWindowTitle("Mosketch for Maya " + SCRIPT_VER)

        content = QtWidgets.QWidget(MAIN_WINDOW)
        main_layout = QtWidgets.QVBoxLayout(content)

        help_text = QtWidgets.QLabel(content)
        help_text.setWordWrap(True)

        help_text.setText("""<br>
        <b>Please read <a href='https://github.com/MokaStudio/MosketchForMaya' style=\"color: #F16521;\"> documentation</a> first.</b>
        <br>""")
        help_text.setOpenExternalLinks(True)

        ip_label = QtWidgets.QLabel("IP", content)
        ip_lineedit = QtWidgets.QLineEdit(content)
        ip_lineedit.setText(IP)
        ip_lineedit.textChanged.connect(_ip_text_changed)
        ip_layout = QtWidgets.QHBoxLayout()
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(ip_lineedit)

        buttons_layout = QtWidgets.QHBoxLayout()
        connect_button = QtWidgets.QToolButton(content)
        connect_button.setText("CONNECT")
        connect_button.setAutoRaise(True)
        connect_button.clicked.connect(_open_connection)
        buttons_layout.addWidget(connect_button)
        disconnect_button = QtWidgets.QToolButton(content)
        disconnect_button.setText("DISCONNECT")
        disconnect_button.setAutoRaise(True)
        disconnect_button.clicked.connect(_close_connection)
        buttons_layout.addWidget(disconnect_button)
        update_mosketch_button = QtWidgets.QToolButton(content)
        update_mosketch_button.setText("UPDATE MOSKETCH")
        update_mosketch_button.setAutoRaise(True)
        update_mosketch_button.clicked.connect(_update_mosketch)
        buttons_layout.addWidget(update_mosketch_button)

        spacer = QtWidgets.QSpacerItem(10, 20)

        self.status_text = QtWidgets.QLabel(content)
        self.status_text.setWordWrap(True)
        self.status_text.setText("Not connected yet")

        content.setLayout(main_layout)
        main_layout.addWidget(help_text)
        main_layout.addLayout(ip_layout)
        main_layout.addLayout(buttons_layout)
        self.setCentralWidget(content)
        main_layout.addSpacerItem(spacer)
        main_layout.addWidget(self.status_text)

    def closeEvent(self, event):
        if CONNECTION is not None:
          _close_connection()


################################################################################
##########          GUI
################################################################################
def _create_gui():
    global MAIN_WINDOW
    
    MAIN_WINDOW = UI_MosketchWindow()
    MAIN_WINDOW.init_mosketch_ui()
    MAIN_WINDOW.show()    

    _print_verbose(sys.version, 1)
    _print_verbose(sys.getdefaultencoding(), 2)
    _print_verbose(sys.getfilesystemencoding(), 2)
    _print_verbose(sys.prefix, 2)
    _print_verbose(locale.getdefaultlocale(), 2)
    

def _destroy_gui():
    MAIN_WINDOW.close()


def _get_maya_main_window():
    OpenMayaUI.MQtUtil.mainWindow()
    ptr = OpenMayaUI.MQtUtil.mainWindow()
    if ptr is None:
        raise RuntimeError('No Maya window found.')

    window = wrapInstance(long(ptr), QtWidgets.QMainWindow)
    assert isinstance(window, QtWidgets.QMainWindow)
    return window


def _ip_text_changed(text):
    global IP
    IP = text


################################################################################
##########          HELPERS
################################################################################
def _print_error(error):
    error_msg = "ERROR: " + error
    print error_msg
    MAIN_WINDOW.status_text.setText(error_msg)


def _print_success(success):
    success_msg = "SUCCESS: " + success
    print success_msg
    MAIN_WINDOW.status_text.setText(success_msg)


def _print_encoding(string):
    if isinstance(string, str):
        print "ordinary string"
    elif isinstance(string, unicode):
        print "unicode string"
    else:
        print "not a recognized string encoding"

def _print_verbose(msg, verbose_level):
    global VERBOSE
    if verbose_level <= VERBOSE:
        print(msg)


def _quat_as_euler_angles(quat):
    """
    Take a quaternion and return the corresponding Euler angles in degrees
    """
    vec = quat.asEulerRotation()
    vec = vec * RAD_2_DEG
    return vec


def _print_quat_as_euler_angles(name, quat):
    vec = _quat_as_euler_angles(quat)
    print name + '= ' + str(vec[0]) + ' ' + str(vec[1]) + ' ' + str(vec[2])


def _is_valid_ipv4_address(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # not a valid address
        return False
    return True


################################################################################
##########          CONNECTION
################################################################################
def _get_connection_name():
    return IP + ":" + str(MOSKETCH_PORT)


def _open_connection():
    global CONNECTION

    if CONNECTION is not None:
        _print_error("connection is already opened.")
        return

    # Test IP format
    if _is_valid_ipv4_address(IP) == False:
        _print_error('IP address looks wrong, please enter a valid IP address')
        return
    else:
        _print_success('Connecting to ' + IP)

    # Try to connect
    CONNECTION = QtNetwork.QTcpSocket(MAIN_WINDOW)
    CONNECTION.readyRead.connect(_got_data)
    CONNECTION.error.connect(_got_error)
    CONNECTION.connected.connect(_connected)
    CONNECTION.disconnected.connect(_disconnected)

    CONNECTION.connectToHost(IP, MOSKETCH_PORT)


def _close_connection():
    global CONNECTION
    global JOINTS_BUFFER
    global JOINTS_INIT_ORIENT_INV_BUFFER
    global JOINTS_ROTATE_AXIS_INV_BUFFER

    if CONNECTION is None:
        _print_error("connection is already closed.")
        return

    CONNECTION.close()
    CONNECTION = None
    JOINTS_BUFFER = {}
    JOINTS_INIT_ORIENT_INV_BUFFER = {}
    JOINTS_ROTATE_AXIS_INV_BUFFER = {}


def _connected():
    _print_success("connection opened on " + _get_connection_name())


def _disconnected():
    global CONNECTION

    _print_success("connection closed on " + _get_connection_name())

    if CONNECTION is not None:
        CONNECTION.close() # Just in case
        CONNECTION = None


def _got_error(socket_error):
    global CONNECTION

    try:
        err_msg = CONNECTION.errorString()
        _print_error(err_msg)
    except Exception, e:
        _print_error("connection is not opened yet.")

    if socket_error == QtNetwork.QTcpSocket.ConnectionRefusedError:
        CONNECTION = None


################################################################################
##########          SEND
################################################################################
def _update_mosketch():
    '''
    We send "full" local rotations and local translations.
    So we need to add rotate axis and joint orient.
    '''
    # Useless to prepare the data if we have no connection
    if CONNECTION is None:
        _print_error("Mosketch is not connected!")
        return

    # For every joint, pack data, then send packet
    try:
        quat = pmc.datatypes.Quaternion()
        joints_buffer_values = JOINTS_BUFFER.values()
        joints_stream = {}
        joints_stream[JSON_KEY_TYPE] = "JointsStream"
        joints_stream[JSON_KEY_JOINTS] = []
        for maya_joint in joints_buffer_values:
            joint_data = {} # Reinit it
            joint_name = maya_joint.name()

            joint_data[JSON_KEY_NAME] = joint_name # Fill the Json key for the name

            # W = [S] * [RO] * [R] * [JO] * [IS] * [T]
            rotate_axis = JOINTS_ROTATE_AXIS_INV_BUFFER[joint_name].inverse()
            joint_orient = JOINTS_INIT_ORIENT_INV_BUFFER[joint_name].inverse()
            quat = maya_joint.getRotation(space='transform', quaternion=True)
            quat = rotate_axis * quat * joint_orient
            joint_data[JSON_KEY_ROTATION] = [quat[0], quat[1], quat[2], quat[3]]

            translation = maya_joint.getTranslation(space='transform')
            translation *= 0.01 # Mosketch uses meters. Maya uses centimeters
            joint_data[JSON_KEY_TRANSLATION] = [translation[0], translation[1], translation[2]]
            joints_stream[JSON_KEY_JOINTS].append(joint_data)
        json_data = json.dumps(joints_stream)
        CONNECTION.write(json_data)
    except Exception, e:
        _print_error("cannot send joint value (" + str(e) + ")")


def _send_ack_hierarchy_initialized():
    '''
    We send an acknowlegment to let Mosketch know that from now, it can send the JointsStream.
    '''
    # Useless to prepare the data if we have no connection
    if CONNECTION is None:
        _print_error("Mosketch is not connected!")
        return
    try:
        ack_packet = {}
        ack_packet[JSON_KEY_TYPE] = "AckHierarchyInitialized"
        json_data = json.dumps([ack_packet])
        CONNECTION.write(json_data)
        CONNECTION.flush()
        _print_verbose("AckHierarchyInitialized sent", 1)

    except Exception, e:
        _print_error("cannot send AckHierarchyInitialized (" + str(e) + ")")


def _send_ack_uuids_received():
    '''
    We send an acknowlegment to let Mosketch know we received all joint's Uuids.
    '''
    # Useless to prepare the data if we have no connection
    if CONNECTION is None:
        _print_error("Mosketch is not connected!")
        return
    try:
        ack_packet = {}
        ack_packet[JSON_KEY_TYPE] = "JointsUuidsAck"
        json_data = json.dumps([ack_packet])
        CONNECTION.write(json_data)
        CONNECTION.flush()
        _print_verbose("_send_ack_uuids_received sent", 1)

    except Exception, e:
        _print_error("cannot send Uuids ack (" + str(e) + ")")


def _send_ack_jointstream_received():
    '''
    We send an acknowlegment to let Mosketch know that we received JointsStream.
    '''
    # Useless to prepare the data if we have no connection
    if CONNECTION is None:
        _print_error("Mosketch is not connected!")
        return
    try:
        ack_packet = {}
        ack_packet[JSON_KEY_TYPE] = "JointsStreamAck"
        json_data = json.dumps(ack_packet)
        CONNECTION.write(json_data)

    except Exception, e:
        _print_error("cannot send JointsStreamAck (" + str(e) + ")")

################################################################################
##########          RECEIVE
################################################################################
def _got_data():
    """
    A packet is ready to read in the socket.
    Read it and process it.
    """
    try:
        raw_data = CONNECTION.readLine()
        
        if raw_data.isEmpty() is True:
            _print_verbose("Raw data from CONNECTION is empty", 1)
            return

        json_data = str(raw_data)
        _process_data(json_data)

    except Exception as e:
        _print_error("cannot read received data (" + type(e).__name__ + ": " + str(e) +")")


def _process_data(arg):
    """
    We received a Json object. It may be a JointsStream, a Hierarchy or a JointsUuids
    """
    size = str(sys.getsizeof(arg))
    _print_verbose("Paquet size:" + size, 2)
    _print_verbose(arg, 2)
    
    try:
        data = json.loads(arg)

        if data[JSON_KEY_TYPE] == "Hierarchy":
            _process_hierarchy(data)
        elif data[JSON_KEY_TYPE] == "JointsStream":
            _process_joints_stream(data)
        elif data[JSON_KEY_TYPE] == "JointsUuids":
            _process_joints_uuids(data)
        else:
            _print_error("Unknown data type received: " + data[JSON_KEY_TYPE])
    except ValueError:
        _print_verbose("Received a non-Json object." + sys.exc_info()[0] + sys.exc_info()[1], 1)
        return
    except Exception as e:
        _print_error("cannot process data (" + type(e).__name__ + ": " + str(e) +")")


def _process_hierarchy(hierarchy_data):
    global JOINTS_BUFFER
    global JOINTS_INIT_ORIENT_INV_BUFFER
    global JOINTS_ROTATE_AXIS_INV_BUFFER

    try:
        # First empty JOINTS_BUFFER
        JOINTS_BUFFER = {}
        JOINTS_INIT_ORIENT_INV_BUFFER = {}
        JOINTS_ROTATE_AXIS_INV_BUFFER = {}

        # Retrieve all joints from Maya and Transforms (we may be streaming to controllers too)
        all_maya_joints = pmc.ls(type="joint")
        all_maya_transform = pmc.ls(type="transform")

        # Then from all joints in the hierarchy, lookup in maya joints
        joints_name = hierarchy_data[JSON_KEY_JOINTS]

        for joint_name in joints_name:
            # We store joints by mapping them in our buffers
            maya_real_joints = [maya_joint for maya_joint in all_maya_joints if maya_joint.name() == joint_name]
            if maya_real_joints:
                # We should have one Maya joint mapped anyways
                if len(maya_real_joints) != 1:
                    _print_error("We should have 1 Maya joint mapped only. Taking the first one only.")                
                _map_joint(joint_name, maya_real_joints[0])

        # If no mapping close connection
        if (len(JOINTS_BUFFER) == 0):
            _close_connection()
            _print_error("Couldn't map joints. Check Maya's namespaces maybe.")
            return

        # Now tell Mosketch the mapping has gone well
        _send_ack_hierarchy_initialized()

        # Print nb joints in Maya and nb joints in BUFFER for information purposes
        _print_success("mapped " + str(len(JOINTS_BUFFER)) + " maya joints out of " + str(len(all_maya_transform)))
        _print_success("Buffers size: " + str(len(JOINTS_BUFFER)) + " / " + str(len(JOINTS_ROTATE_AXIS_INV_BUFFER)) + " / " + str(len(JOINTS_INIT_ORIENT_INV_BUFFER)))

    except Exception as e:
        _print_error("cannot process hierarchy data (" + type(e).__name__ + ": " + str(e) +")")


def _map_joint(mosketch_name, maya_joint):
    global JOINTS_BUFFER
    global JOINTS_INIT_ORIENT_INV_BUFFER
    global JOINTS_ROTATE_AXIS_INV_BUFFER

    JOINTS_BUFFER[mosketch_name] = maya_joint
    vRO = maya_joint.getRotateAxis()
    rotate_axis = pmc.datatypes.EulerRotation(vRO[0], vRO[1], vRO[2]).asQuaternion()
    JOINTS_ROTATE_AXIS_INV_BUFFER[mosketch_name] = rotate_axis.inverse()
    try:
        # We have a Joint => Get joint_orient into account
        joint_orient = maya_joint.getOrientation()
        JOINTS_INIT_ORIENT_INV_BUFFER[mosketch_name] = joint_orient.inverse()
    except Exception:
        # We have a Transform => Do NOT get joint_orient into account but the initial transform instead
        joint_rotation = maya_joint.getRotation(space='transform', quaternion=True)
        JOINTS_INIT_ORIENT_INV_BUFFER[mosketch_name] = joint_rotation.inverse()
        _print_verbose("WARNING: we have a controller while we should have a joint: " + mosketch_name + " - " + maya_joint.name(), 1)


def _process_joints_uuids(data):
    _print_verbose("_process_joints_uuids", 1)
    global JOINTS_UUIDS

    try:
        joints_data = data[JSON_KEY_JOINTS]
        _print_verbose(joints_data, 3)

        for joint_data in joints_data:
            for name in joint_data:
                JOINTS_UUIDS[name] = joint_data[name]
    except Exception as e:
        _print_error("cannot process joints uuids (" + type(e).__name__ + ": " + str(e) +")")

    _print_verbose("Total uuids: " + str(len(JOINTS_UUIDS)), 1)
    if (len(JOINTS_UUIDS) > 0):
        _send_ack_uuids_received()


def _process_joints_stream(joints_stream_data):
    '''
    We receive "full" local rotations and local translations.
    So we need to substract rotate axis and joint orient.
    '''
    try:
        joints_data = joints_stream_data[JSON_KEY_JOINTS]
        _print_verbose(joints_data, 3)

        for joint_data in joints_data:
            # We select all joints having the given name
            joint_name = joint_data[JSON_KEY_NAME]
            try:
                maya_joint = JOINTS_BUFFER[joint_name]
            except KeyError:
                continue

            if maya_joint:
                # W = [S] * [RO] * [R] * [JO] * [IS] * [T]
                quat = pmc.datatypes.Quaternion(joint_data[JSON_KEY_ROTATION])
                rotate_axis_inv = JOINTS_ROTATE_AXIS_INV_BUFFER[joint_name]
                joint_orient_inv = JOINTS_INIT_ORIENT_INV_BUFFER[joint_name]
                quat = rotate_axis_inv * quat * joint_orient_inv
                maya_joint.setRotation(quat, space='transform')
                
                joint_type = joint_data[JSON_KEY_ANATOMIC]                
                if joint_type == 7: # This is a 6 DoFs joint so consider translation part too
                    trans = pmc.datatypes.Vector(joint_data[JSON_KEY_TRANSLATION])
                    trans = trans.rotateBy(rotate_axis_inv)
                    # Mosketch uses meters. Maya uses centimeters
                    trans *= 100
                    maya_joint.setTranslation(trans, space='transform')

        _send_ack_jointstream_received()
    except KeyError as e:
        _print_error("cannot find " + joint_name + " in maya")
        return
    except Exception as e:
        _print_error("cannot process joints stream (" + type(e).__name__ + ": " + str(e) +")")


################################################################################
##########          MOSKETCH COMMANDS
################################################################################
"""
  For developers you can check the following link:
  https://support.mokastudio.com/support/solutions/articles/6000198416-streaming-developer-documentation
"""

def _send_command_joint_orientation(orient_mode):
    packet = {}
    packet[JSON_KEY_TYPE] = PACKET_TYPE_COMMAND
    packet[JSON_KEY_OBJECT] = 'scene'
    packet[JSON_KEY_COMMAND] = 'setStreamingJointOrientMode'

    jsonObj = {}
    jsonObj['jointOrientMode'] = str(orient_mode)
    packet[JSON_KEY_PARAMETERS] = jsonObj

    json_data = json.dumps([packet])
    CONNECTION.write(json_data)
    CONNECTION.flush()
    _print_verbose("_send_command_joint_orientation", 1)


def _send_command_joint_space(space_mode):
    packet = {}
    packet[JSON_KEY_TYPE] = PACKET_TYPE_COMMAND
    packet['object'] = 'scene'
    packet['command'] = 'setStreamingJointSpace'

    jsonObj = {}
    jsonObj['jointSpace'] = space_mode
    packet[JSON_KEY_PARAMETERS] = jsonObj

    json_data = json.dumps([packet])
    CONNECTION.write(json_data)
    CONNECTION.flush()
    _print_verbose("_send_command_joint_space", 1)


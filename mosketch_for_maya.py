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
import platform
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
SCRIPT_VER = "0.18"
MAIN_WINDOW = None
CONNECTION = None
IP = "127.0.0.1"
PORT = 16094

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

# Maya joints buffers
JOINTS_BUFFER = {}
JOINTS_INIT_ORIENT_INV_BUFFER = {}
JOINTS_ROTATE_AXIS_INV_BUFFER = {}

# Maya FK controllers buffers
CONTROLLERS_BUFFER = {}
CONTROLLERS_INIT_ORIENT_INV_BUFFER = {}
CONTROLLERS_ROTATE_AXIS_INV_BUFFER = {}

# We get joints name from Mosketch, we need to associate them to Maya HIK FK controllers
JOINTS_NAME_TO_CONTROLLERS = {}
CONTROLLERS_TO_JOINTS_NAME = {}

# Mosketch joints uuids
JOINTS_UUIDS = {}

# Utils
PI = 3.1415926535897932384626433832795
RAD_2_DEG = 180.0 / PI

# Verbose level (1 for critical informations, 3 to output all packets)
VERBOSE = 1

STREAMING_MODE = "Joints"

# Large packets sent over the LAN may be split. So use a buffer to reconstruct them
SOCKET_DATA_BUFFER = ""

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
    load_mosko_icon_name = os.path.dirname(os.path.abspath(__file__)) + "/load_mosko.png"
    load_mosko_humanik_icon_name = os.path.dirname(os.path.abspath(__file__)) + "/load_mosko_humanik.png"
    load_okto_icon_name = os.path.dirname(os.path.abspath(__file__)) + "/load_okto.png"
    pmc.shelfButton(label='Start',
                    parent=shelf_layout, 
                    image1=start_icon_name, 
                    command='import mosketch_for_maya;reload(mosketch_for_maya);mosketch_for_maya.start()')
    pmc.shelfButton(label='Stop',
                    parent=shelf_layout,
                    image1=stop_icon_name,
                    command='mosketch_for_maya.stop()')
    pmc.shelfButton(label='Load Mosko',
                    parent=shelf_layout,
                    image1=load_mosko_icon_name,
                    command='import mosketch_for_maya;reload(mosketch_for_maya);mosketch_for_maya.load_mosko()')
    pmc.shelfButton(label='Load Okto',
                    parent=shelf_layout,
                    image1=load_okto_icon_name,
                    command='import mosketch_for_maya;reload(mosketch_for_maya);mosketch_for_maya.load_okto()')
    pmc.shelfButton(label='Load Mosko',
                    parent=shelf_layout,
                    image1=load_mosko_humanik_icon_name,
                    command='import mosketch_for_maya;reload(mosketch_for_maya);mosketch_for_maya.load_mosko_humanik()')

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


def load_mosko():
    """
    Load Mosko FBX file
    """
    characters_base_dir = _get_characters_base_dir()
    mosko_absolute_file_path = characters_base_dir + "003_Mosko.fbx"
    pmc.system.importFile(mosko_absolute_file_path)


def load_okto():
    """
    Load Okto FBX file
    """
    characters_base_dir = _get_characters_base_dir()
    okto_absolute_file_path = characters_base_dir + "004_Okto.fbx"
    pmc.system.importFile(okto_absolute_file_path)

def load_mosko_humanik():
    """
    Load Mosko FBX file
    """
    characters_base_dir = _get_characters_base_dir()
    mosko_absolute_file_path = characters_base_dir + "003_Mosko_HumanIK.ma"
    pmc.system.importFile(mosko_absolute_file_path)


################################################################################
##########          UI CLASS DEFINITION 
################################################################################
class UI_MosketchWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        maya_window = _get_maya_main_window()
        super(UI_MosketchWindow, self).__init__(maya_window, QtCore.Qt.WindowStaysOnTopHint)

    def init_mosketch_ui(self):
        self.setWindowTitle("Mosketch for Maya " + SCRIPT_VER)

        content = QtWidgets.QWidget(MAIN_WINDOW)
        main_layout = QtWidgets.QVBoxLayout(content)
        minWidth = 320
        minHeight = 200
        self.setMinimumSize(minWidth, minHeight)
        self.resize(minWidth, minHeight)

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
        ip_lineedit.returnPressed.connect(_open_connection)
        ip_layout = QtWidgets.QHBoxLayout()
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(ip_lineedit)

        streaming_mode_label = QtWidgets.QLabel()
        streaming_mode_label.setText("Streaming onto:")
        streaming_mode_combo = QtWidgets.QComboBox(self)
        streaming_mode_combo.setMinimumWidth(200)
        streaming_mode_combo.addItems(["Joints", "Controllers"])
        streaming_mode_combo.currentTextChanged.connect(_streaming_mode_current_text_changed)
        
        streaming_mode_layout = QtWidgets.QHBoxLayout()
        streaming_mode_layout.addWidget(streaming_mode_label)
        streaming_mode_layout.addWidget(streaming_mode_combo)

        connect_button = QtWidgets.QToolButton(content)
        connect_button.setText("CONNECT")
        connect_button.setAutoRaise(True)
        connect_button.clicked.connect(_open_connection)
        disconnect_button = QtWidgets.QToolButton(content)
        disconnect_button.setText("DISCONNECT")
        disconnect_button.setAutoRaise(True)
        disconnect_button.clicked.connect(_close_connection)
        update_mosketch_button = QtWidgets.QToolButton(content)
        update_mosketch_button.setText("UPDATE MOSKETCH")
        update_mosketch_button.setAutoRaise(True)
        update_mosketch_button.setCheckable(False)
        update_mosketch_button.clicked.connect(_update_mosketch)
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(connect_button)
        buttons_layout.addWidget(disconnect_button)
        buttons_layout.addWidget(update_mosketch_button)

        spacer = QtWidgets.QSpacerItem(10, 20)

        self.status_text = QtWidgets.QLabel(content)
        self.status_text.setWordWrap(True)
        self.status_text.setAlignment(QtCore.Qt.AlignCenter);
        self.status_text.setText("NOT CONNECTED")
        self.status_text.setStyleSheet("QLabel { background-color : red;color:white;font-weight: bold;}");

        self.log_text = QtWidgets.QLabel(content)
        self.log_text.setWordWrap(True)
        self.log_text.setText("")

        content.setLayout(main_layout)
        main_layout.addWidget(help_text)
        main_layout.addLayout(ip_layout)
        main_layout.addLayout(streaming_mode_layout)
        main_layout.addLayout(buttons_layout)
        main_layout.addSpacerItem(spacer)
        main_layout.addWidget(self.status_text)
        main_layout.addWidget(self.log_text)

    def closeEvent(self, event):
        # Close connection if any is still opened
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


def _streaming_mode_current_text_changed(text):
    global STREAMING_MODE
    STREAMING_MODE = text


################################################################################
##########          CONNECTION
################################################################################
def _get_connection_name():
    global IP
    global PORT

    return IP + ":" + str(PORT)


def _open_connection():
    global CONNECTION
    global IP
    global PORT
    global STREAMING_MODE

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

    MAIN_WINDOW.status_text.setText("CONNECTING...")
    MAIN_WINDOW.status_text.setStyleSheet("QLabel { background-color : orange;;color:white;font-weight: bold;}")

    print "Trying to connect to " + _get_connection_name()
    CONNECTION.connectToHost(IP, PORT)


def _close_connection():
    global CONNECTION
    global SOCKET_DATA_BUFFER
    global JOINTS_BUFFER
    global JOINTS_INIT_ORIENT_INV_BUFFER
    global JOINTS_ROTATE_AXIS_INV_BUFFER
    global CONTROLLERS_BUFFER
    global CONTROLLERS_INIT_ORIENT_INV_BUFFER
    global CONTROLLERS_ROTATE_AXIS_INV_BUFFER

    if CONNECTION is None:
        _print_error("connection is already closed.")
        return

    SOCKET_DATA_BUFFER = ""
    CONNECTION.flush()
    CONNECTION.close()
    CONNECTION = None

    JOINTS_BUFFER = {}
    JOINTS_INIT_ORIENT_INV_BUFFER = {}
    JOINTS_ROTATE_AXIS_INV_BUFFER = {}

    CONTROLLERS_BUFFER = {}
    CONTROLLERS_INIT_ORIENT_INV_BUFFER = {}
    CONTROLLERS_ROTATE_AXIS_INV_BUFFER = {}


def _connected():
    _print_success("connection opened on " + _get_connection_name())
    MAIN_WINDOW.status_text.setText("CONNECTED")
    MAIN_WINDOW.status_text.setStyleSheet("QLabel { background-color : green;color:white;font-weight: bold;}")

def _disconnected():
    global CONNECTION
    global SOCKET_DATA_BUFFER

    _print_success("connection closed on " + _get_connection_name())
    MAIN_WINDOW.status_text.setText("NOT CONNECTED")
    MAIN_WINDOW.status_text.setStyleSheet("QLabel { background-color : red;color:white;font-weight: bold;}")


# FIXME: should we put that in _close_connection instead???
    if CONNECTION is not None:
        SOCKET_DATA_BUFFER = ""
        CONNECTION.flush()
        CONNECTION.close() # Just in case
        CONNECTION = None


def _got_error(socket_error):
    global CONNECTION

    MAIN_WINDOW.status_text.setText("NOT CONNECTED")
    MAIN_WINDOW.status_text.setStyleSheet("QLabel { background-color : red;color:white;font-weight: bold;}");

    try:
        err_msg = CONNECTION.errorString()
        _print_error(err_msg)
    except Exception:
        _print_error("connection is not opened yet.")

    CONNECTION = None


################################################################################
##########          RECEIVE
################################################################################
def _got_data():
    """
    A packet is ready to read in the socket.
    Read it and process it.
    """
    global SOCKET_DATA_BUFFER
    try:
        raw_data = CONNECTION.readLine()
        
        if raw_data.isEmpty() is True:
            _print_verbose("Raw data from CONNECTION is empty", 1)
            return
        SOCKET_DATA_BUFFER += raw_data
        json_data = str(SOCKET_DATA_BUFFER)
        _process_data(json_data)

        # Processing went fine, clear socket buffer
        SOCKET_DATA_BUFFER = ""

    except Exception as e:
        pass
        # Packet is just split. Ignore and go on
        #_print_error("cannot read received data (" + type(e).__name__ + ": " + str(e) +")")

def _process_data(arg):
    """
    We received a Json object. It may be:
        - a JointsStream
        - a Hierarchy
        - a JointsUuids
    """
    size = str(sys.getsizeof(arg))
    _print_verbose("Paquet size:" + size, 2)
    _print_verbose(arg, 2)
    
    try:
        data = json.loads(arg)

        if data[JSON_KEY_TYPE] == "Hierarchy":
            # Always map joints as we need them when sending values back to Mosketch
            _process_hierarchy(data)

            if STREAMING_MODE == "Controllers":
                _process_hierarchy_HIK(data)
                # Controllers are zeroed at the beginning => discard initial rotation in bind pose
                _send_command_orientMode(0) #discard
                # We cannot tell for sure what is the initial orientation of the controllers
                # So we ask Mosketch to send delta rotation wrt to parent, expressed in world.
                # Then we do the maths to compute orientation in correct Maya's controllers frame
                _send_command_jointSpace("ParentInWorld")
            else: # set streaming parameters for joints
                # Send orientation mode
                _send_command_orientMode(1)
                # Specify in which space we want to work. Default is in Parent space
                _send_command_jointSpace("Parent")

            # We are done, send acknowledgement
            _send_hierarchy_initialized_ack()

        elif data[JSON_KEY_TYPE] == "JointsStream":
            if (STREAMING_MODE ==  "Controllers"):
                _process_joints_stream_HIK(data)
            else:
                _process_joints_stream(data)

            _send_ack_jointstream_received()

        elif data[JSON_KEY_TYPE] == "JointsUuids":
            _process_joints_uuids(data)
            _send_joint_uuids_received_ack()
        else:
            _print_error("Unknown data type received: " + data[JSON_KEY_TYPE])
    except ValueError:
        _print_verbose("Received a non-Json object." + sys.exc_info()[0] + sys.exc_info()[1], 1)
        return
    except Exception as e:
        _print_error("cannot process data (" + type(e).__name__ + ": " + str(e) +")")


def _process_hierarchy_HIK(data):
    '''
    We suppose that joints name in Mosketch and Maya are the same name.
    Find the associated controllers.
    NOTE: data is not used for the moment
    '''
    global CONTROLLERS_BUFFER
    global CONTROLLERS_TO_JOINTS_NAME
    global CONTROLLERS_ROTATE_AXIS_INV_BUFFER
    global CONTROLLERS_INIT_ORIENT_INV_BUFFER

    try:
        # Retrieve HIKCharacterNodes in the scene: it gives HIK => joints mapping
        hik_characters = pmc.ls(type="HIKCharacterNode")
        if len(hik_characters) != 1:
            _print_verbose("We should exactly ONE HIKCharacterNode in the scene", 1)

        # Retrieve HIKControlSetNodes in the scene: it gives HIK => FK Controllers mapping
        hik_control_sets = pmc.ls(type="HIKControlSetNode")
        if len(hik_control_sets) != 1:
            _print_verbose("We should exactly ONE HIKControlSetNode in the scene", 1)

        hik_character = hik_characters[0]
        hik_control_set = hik_control_sets[0]
        hik_character_attributes = hik_character.listAttr()

        for self_att in hik_character_attributes:
            # Get inbound (connected) attribute first
            inbound_att = self_att.get(silent=True)
            # Then check type
            if type(inbound_att) == pmc.nodetypes.Joint:
                joint_name = inbound_att.name() # Name of the joint
                self_att_name = self_att.attrName()
                # getattr() is a Python function that returns the object attribute based on its (string) name.
                # Not to be confused with Maya's attributes
                fk_controller = getattr(hik_control_set, self_att_name).get()

                _map_controller(joint_name, fk_controller)
        
        # Print nb joints in Maya and nb joints in BUFFER for information purposes
        _print_success("Buffers size: " + str(len(CONTROLLERS_BUFFER)) + " / " + str(len(CONTROLLERS_ROTATE_AXIS_INV_BUFFER)) + " / " + str(len(CONTROLLERS_INIT_ORIENT_INV_BUFFER)))
        _print_verbose('Joints buffer = ' + str(len(CONTROLLERS_BUFFER)) + ', controllers buffer = ' + str(len(CONTROLLERS_BUFFER)), 1)
    except Exception as e:
        _print_error("cannot process hierarchy data (" + type(e).__name__ + ": " + str(e) +")")


def _map_controller(mosketch_name, maya_controller):
    global CONTROLLERS_BUFFER
    global CONTROLLERS_TO_JOINTS_NAME
    global CONTROLLERS_ROTATE_AXIS_INV_BUFFER
    global CONTROLLERS_INIT_ORIENT_INV_BUFFER

    CONTROLLERS_BUFFER[mosketch_name] = maya_controller
    CONTROLLERS_TO_JOINTS_NAME[maya_controller] = mosketch_name

    vRO = maya_controller.getRotateAxis()
    RO = pmc.datatypes.EulerRotation(vRO[0], vRO[1], vRO[2]).asQuaternion()
    CONTROLLERS_ROTATE_AXIS_INV_BUFFER[mosketch_name] = RO.inverse()

    JO = maya_controller.getOrientation()
    CONTROLLERS_INIT_ORIENT_INV_BUFFER[mosketch_name] = JO.inverse()


def _process_hierarchy(hierarchy_data):
    global JOINTS_BUFFER
    global JOINTS_INIT_ORIENT_INV_BUFFER
    global JOINTS_ROTATE_AXIS_INV_BUFFER

    try:
        JOINTS_BUFFER = {}
        JOINTS_INIT_ORIENT_INV_BUFFER = {}
        JOINTS_ROTATE_AXIS_INV_BUFFER = {}

        # Retrieve all joints from Maya and Transforms (we may be streaming to controllers too)
        all_maya_joints = pmc.ls(type="joint")
        all_maya_transform = pmc.ls(type="transform")

        # Then from all joints in the hierarchy, lookup in maya joints
        joints_name = hierarchy_data[JSON_KEY_JOINTS]

        for joint_name in joints_name:
            # We store joints in any cases
            maya_joints = [maya_joint for maya_joint in all_maya_joints if maya_joint.name() == joint_name]
            if maya_joints:
                # We should have one Maya joint mapped anyways
                if len(maya_joints) != 1:
                    _print_error("We should have 1 Maya joint mapped only. Taking the first one only.")

                _map_joint(joint_name, maya_joints[0])

        # If no mapping close connection
        if (len(JOINTS_BUFFER) == 0):
            _close_connection()
            _print_error("Couldn't map joints. Check Maya's namespaces maybe.")
            return

        # Print nb joints in Maya and nb joints in BUFFER for information purposes
        _print_success("mapped " + str(len(JOINTS_BUFFER)) + " maya joints out of " + str(len(all_maya_transform)))
        _print_success("Buffers size: " + str(len(JOINTS_BUFFER)) + " / " + str(len(JOINTS_ROTATE_AXIS_INV_BUFFER)) + " / " + str(len(JOINTS_INIT_ORIENT_INV_BUFFER)))
        _print_verbose('Joints buffer = ' + str(len(JOINTS_BUFFER)) + ', controllers buffer = ' + str(len(JOINTS_BUFFER)), 1)

    except Exception as e:
        _print_error("cannot process hierarchy data (" + type(e).__name__ + ": " + str(e) +")")
    

def _map_joint(mosketch_name, maya_joint):
    global JOINTS_BUFFER
    global JOINTS_ROTATE_AXIS_INV_BUFFER
    global JOINTS_INIT_ORIENT_INV_BUFFER

    JOINTS_BUFFER[mosketch_name] = maya_joint
    vRO = maya_joint.getRotateAxis()
    RO = pmc.datatypes.EulerRotation(vRO[0], vRO[1], vRO[2]).asQuaternion()
    JOINTS_ROTATE_AXIS_INV_BUFFER[mosketch_name] = RO.inverse()
    try:
        # We have a Joint => Get joint_orient into account
        JO = maya_joint.getOrientation().inverse()
        JOINTS_INIT_ORIENT_INV_BUFFER[mosketch_name] = JO
    except Exception:
        # We have a Transform => Do NOT get joint_orient into account but the initial transform instead
        JO = maya_joint.getRotation(space='transform', quaternion=True).inverse()
        JOINTS_INIT_ORIENT_INV_BUFFER[mosketch_name] = JO


def _send_hierarchy_initialized_ack():
    '''
    We send an acknowlegment to let Mosketch know that hierarchy is correctly initialized on our side.
    '''
    if CONNECTION is None:
        _print_error("Mosketch is not connected!")
        return
    try:
        ack_packet = {}
        ack_packet[JSON_KEY_TYPE] = "HierarchyInitializedAck"
        json_data = json.dumps([ack_packet])
        CONNECTION.write(json_data)
        CONNECTION.flush()
        _print_verbose("HierarchyInitializedAck sent", 1)

    except Exception, e:
        _print_error("cannot send HierarchyInitializedAck (" + str(e) + ")")


def _send_joint_uuids_received_ack():
    '''
    We send an acknowlegment to let Mosketch know that from that joint uuids are stored and that it can send the JointsStream.
    '''
    if CONNECTION is None:
        _print_error("Mosketch is not connected!")
        return
    try:
        ack_packet = {}
        ack_packet[JSON_KEY_TYPE] = "JointsUuidsAck"
        json_data = json.dumps([ack_packet])
        CONNECTION.write(json_data)
        CONNECTION.flush()
        _print_verbose("JointsUuidsAck sent", 1)

    except Exception, e:
        _print_error("cannot send JointsUuidsAck (" + str(e) + ")")


def _send_ack_jointstream_received():
    '''
    We send an acknowlegment to let Mosketch know that we received JointsStream.
    '''
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


def _process_joints_stream_HIK(joints_stream_data):
    '''
    We receive "full" local rotations and local translations.
    So we need to substract rotate axis and joint orient.
    '''
    try:
        joints_data = joints_stream_data[JSON_KEY_JOINTS]

        for joint_data in joints_data:
            joint_name = joint_data[JSON_KEY_NAME]
            try:
                maya_controller = CONTROLLERS_BUFFER[joint_name]
            except KeyError:
                continue

            # W = [S] * [RO] * [R] * [JO] * [IS] * [T]
            quat = pmc.datatypes.Quaternion(joint_data[JSON_KEY_ROTATION])
            rotate_axis_inv = CONTROLLERS_ROTATE_AXIS_INV_BUFFER[joint_name]
            joint_orient_inv = CONTROLLERS_INIT_ORIENT_INV_BUFFER[joint_name]
            quat = rotate_axis_inv * quat * joint_orient_inv
            maya_controller.setRotation(quat, space='transform')

            joint_type = joint_data[JSON_KEY_ANATOMIC]
            if joint_type == 7: # This is a 6 DoFs joint so consider translation part too
                trans = pmc.datatypes.Vector(joint_data[JSON_KEY_TRANSLATION])
                # Mosketch uses meters. Maya uses centimeters
                trans *= 100
                maya_controller.setTranslation(trans, space='transform')

    except KeyError as e:
        _print_error("cannot find " + joint_name + " in maya")
        return
    except Exception as e:
        _print_error("cannot process joints stream (" + type(e).__name__ + ": " + str(e) +")")


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

    except KeyError as e:
        _print_error("cannot find " + joint_name + " in maya")
        return
    except Exception as e:
        _print_error("cannot process joints stream (" + type(e).__name__ + ": " + str(e) +")")


def _process_joints_uuids(data):
    _print_verbose("_process_joints_uuids", 2)
    global JOINTS_UUIDS

    try:
        joints_data = data[JSON_KEY_JOINTS]
        _print_verbose(joints_data, 3)

        for joint_data in joints_data:
            for name in joint_data:
                JOINTS_UUIDS[name] = joint_data[name]

    except Exception as e:
        _print_error("cannot process joints uuids (" + type(e).__name__ + ": " + str(e) +")")


################################################################################
##########          SEND
################################################################################
def _update_mosketch():
    '''
    Either we stream onto joints or controllers, we always send "final" joints orientation to Mosketch.
    So we use the same function independently of the streaming mode.
    '''
    if CONNECTION is None:
        _print_error("Mosketch is not connected!")
        return

    # Still split it into a function to make it explicit that we actually update Mosketch from actual Maya joints (and not cotnrollers)
    _update_mosketch_from_joints()


def _update_mosketch_from_joints():
    try:
        quat = pmc.datatypes.Quaternion()
        joints_buffer_values = JOINTS_BUFFER.values()
        joints_stream = {}
        joints_stream[JSON_KEY_TYPE] = "JointsStream"
        joints_stream[JSON_KEY_JOINTS] = []
        for maya_joint in joints_buffer_values:
            joint_data = {}
            joint_name = maya_joint.name()

            joint_data[JSON_KEY_NAME] = joint_name

            # W = [S] * [RO] * [R] * [JO] * [IS] * [T]
            RO = JOINTS_ROTATE_AXIS_INV_BUFFER[joint_name].inverse()
            JO = JOINTS_INIT_ORIENT_INV_BUFFER[joint_name].inverse()
            quat = maya_joint.getRotation(space='transform', quaternion=True)
            quat = RO * quat * JO
            joint_data[JSON_KEY_ROTATION] = [quat[0], quat[1], quat[2], quat[3]]

            translation = maya_joint.getTranslation(space='transform')
             # Mosketch uses meters. Maya uses centimeters
            translation *= 0.01
            joint_data[JSON_KEY_TRANSLATION] = [translation[0], translation[1], translation[2]]
            joints_stream[JSON_KEY_JOINTS].append(joint_data)
        json_data = json.dumps(joints_stream)
        CONNECTION.write(json_data)
    except Exception, e:
        _print_error("cannot send joint value (" + str(e) + ")")


def _send_command_orientMode(orient_mode):
    global CONNECTION
    packet = {}
    packet[JSON_KEY_TYPE] = PACKET_TYPE_COMMAND
    packet[JSON_KEY_OBJECT] = 'scene'
    packet[JSON_KEY_COMMAND] = 'setStreamingJointOrientMode'

    jsonObj = {}
    jsonObj['jointOrientMode'] = str(orient_mode)
    packet[JSON_KEY_PARAMETERS] = jsonObj # we need parameters to be a json object

    json_data = json.dumps([packet]) # [] specific for commands that could be buffered
    CONNECTION.write(json_data)
    CONNECTION.flush()
    _print_verbose("_send_command_orientMode", 1)
      

def _send_command_jointSpace(space_mode):
    global CONNECTION

    packet = {}
    packet[JSON_KEY_TYPE] = PACKET_TYPE_COMMAND
    packet['object'] = 'scene'
    packet['command'] = 'setStreamingJointSpace'

    jsonObj = {}
    jsonObj['jointSpace'] = str(space_mode)
    packet[JSON_KEY_PARAMETERS] = jsonObj # we need parameters to be a json object

    json_data = json.dumps([packet]) # [] specific for commands that could be buffered
    CONNECTION.write(json_data)
    CONNECTION.flush()
    _print_verbose("_send_command_jointSpace", 1)


################################################################################
##########          HELPERS
################################################################################
def _print_error(error):
    error_msg = "ERROR: " + error
    print error_msg
    MAIN_WINDOW.log_text.setText(error_msg)


def _print_success(success):
    success_msg = "SUCCESS: " + success
    print success_msg
    MAIN_WINDOW.log_text.setText(success_msg)


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
    Returns Euler angles in degrees
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


def _get_characters_base_dir():
    characters_base_dir = ""
    current_platform = platform.system()

    if current_platform == "Windows":
        characters_base_dir = os.environ['MOKA_DIR']
    elif current_platform == "Darwin": # This will anyway not going to work because of translocation done by MacOSX by default
        characters_base_dir = "/Applications/"

    characters_base_dir = characters_base_dir + "Mosketch/Data/Characters/"

    return characters_base_dir
    

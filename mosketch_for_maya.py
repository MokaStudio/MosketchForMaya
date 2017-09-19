"""
Mosketch for maya.
See https://github.com/MokaStudio/MosketchForMaya for more informations.
"""
import os

import json

import pymel.core as pmc
import maya.OpenMayaUI as OpenMayaUI
import maya.mel as mel

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

# Global variables
MAIN_WINDOW = None
STATUS_TEXT = None
CONNECTION = None
IP = "127.0.0.1"
MOSKETCH_PORT = 16094
JOINTS_BUFFER = {}

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
                    command='import mosketch_for_maya;mosketch_for_maya.start()')
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
    # Close connection if any is still opened
    if CONNECTION is not None:
        _close_connection()

    _destroy_gui()

################################################################################
##########          GUI
################################################################################
def _create_gui():
    global MAIN_WINDOW
    global STATUS_TEXT

    maya_window = _get_maya_main_window()
    MAIN_WINDOW = QtWidgets.QMainWindow(maya_window)
    MAIN_WINDOW.setWindowTitle("Mosketch for Maya")

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
    connect_button.clicked.connect(_open_connection)
    buttons_layout.addWidget(connect_button)
    disconnect_button = QtWidgets.QToolButton(content)
    disconnect_button.setText("DISCONNECT")
    disconnect_button.clicked.connect(_close_connection)
    buttons_layout.addWidget(disconnect_button)
    update_mosketch_button = QtWidgets.QToolButton(content)
    update_mosketch_button.setText("UPDATE MOSKETCH")
    update_mosketch_button.setCheckable(False)
    update_mosketch_button.clicked.connect(_update_mosketch)
    buttons_layout.addWidget(update_mosketch_button)

    spacer = QtWidgets.QSpacerItem(10, 20)

    STATUS_TEXT = QtWidgets.QLabel(content)
    STATUS_TEXT.setWordWrap(True)
    STATUS_TEXT.setText("Not connected yet")

    content.setLayout(main_layout)
    main_layout.addWidget(help_text)
    main_layout.addLayout(ip_layout)
    main_layout.addLayout(buttons_layout)
    MAIN_WINDOW.setCentralWidget(content)
    main_layout.addSpacerItem(spacer)
    main_layout.addWidget(STATUS_TEXT)

    MAIN_WINDOW.show()

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

# Helpers
def _print_error(error):
    global STATUS_TEXT

    error_msg = "ERROR: " + error
    print error_msg
    STATUS_TEXT.setText(error_msg)

def _print_success(success):
    global STATUS_TEXT

    success_msg = "SUCCESS: " + success
    print success_msg
    STATUS_TEXT.setText(success_msg)

################################################################################
##########          CONNECTION
################################################################################
def _get_connection_name():
    global IP
    global MOSKETCH_PORT

    return IP + ":" + str(MOSKETCH_PORT)

def _open_connection():
    global CONNECTION
    global IP
    global MOSKETCH_PORT

    if CONNECTION is not None:
        _print_error("connection is already opened.")
        return

    # Try to connect
    CONNECTION = QtNetwork.QTcpSocket(MAIN_WINDOW)
    CONNECTION.readyRead.connect(_got_data)
    CONNECTION.error.connect(_got_error)
    CONNECTION.connected.connect(_connected)
    CONNECTION.disconnected.connect(_disconnected)

    print "Trying to connect to " + _get_connection_name()
    CONNECTION.connectToHost(IP, MOSKETCH_PORT)

def _close_connection():
    global CONNECTION

    if CONNECTION is None:
        _print_error("connection is already closed.")
        return

    CONNECTION.close()
    CONNECTION = None
    JOINTS_BUFFER = {}

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
        joints_stream['Type'] = "JointsStream"
        joints_stream['Joints'] = []
        for maya_joints in joints_buffer_values:
            for maya_joint in maya_joints:
                joint_data = {} # Reinit it
                joint_data['Name'] = maya_joint.name()

                # W = [S] * [RO] * [R] * [JO] * [IS] * [T]
                quat = maya_joint.getRotation(space='transform', quaternion=True)
                vRO = maya_joint.getRotateAxis()
                RO = pmc.datatypes.EulerRotation(vRO[0], vRO[1], vRO[2]).asQuaternion()
                joint_orient = maya_joint.getOrientation()
                quat = RO * quat * joint_orient
                joint_data['LocalRotation'] = [quat[0], quat[1], quat[2], quat[3]]

                translation = maya_joint.getTranslation(space='transform')
                translation *= 0.01
                joint_data['LocalTranslation'] = [translation[0], translation[1], translation[2]]
                joints_stream['Joints'].append(joint_data)

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
        ack_packet['Type'] = "AckHierarchyInitialized"
        json_data = json.dumps(ack_packet)
        CONNECTION.write(json_data)

    except Exception, e:
        _print_error("cannot send AckHierarchyInitialized (" + str(e) + ")")

################################################################################
##########          RECEIVE
################################################################################
def _got_data():
    """
    We may receive different types of data:
        - Type == "Hierarchy" => Initialize skeleton
        - Type == "JointsStream" => Copy paste received values on Maya's joints
    """
    try:
        raw_data = CONNECTION.readAll()
        if raw_data.isEmpty() is True:
            return

        json_data = str(raw_data)
        _process_data(json_data)

    except Exception as e:
        _print_error("cannot read received data (" + type(e).__name__ + ": " + str(e) +")")

def _process_data(arg):
    """
    We received a Json object. It may be a JointsStream or a Hierarchy
    """
    try:
        data = json.loads(arg)

        if data['Type'] == "Hierarchy":
            _process_hierarchy(data)
        elif data['Type'] == "JointsStream":
            _process_joints_stream(data)
        else:
            _print_error("Unknown data type received: " + data['Type'])
    except ValueError:
        # _print_error("received a non-Json object.")
        return
    except Exception as e:
        _print_error("cannot process data (" + type(e).__name__ + ": " + str(e) +")")

def _process_hierarchy(hierarchy_data):
    global JOINTS_BUFFER

    try:
        # First empty JOINT_BUFFER
        JOINTS_BUFFER = {}

        # Retrieve all joints from Maya
        all_maya_joints = pmc.ls(type="joint")

        # Then from all joints in the hierarchy, lookup in maya joints
        joints_name = hierarchy_data["Joints"]

        for joint_name in joints_name:
            maya_joints = [maya_joint for maya_joint in all_maya_joints if maya_joint.name() == joint_name]
            if maya_joints:
                JOINTS_BUFFER[joint_name] = maya_joints

        _send_ack_hierarchy_initialized()

        # Print nb joints in Maya and nb joints in BUFFER for information purposes
        _print_success("mapped " + str(len(JOINTS_BUFFER)) + " maya joints out of " + str(len(all_maya_joints)))

    except Exception as e:
        _print_error("cannot process hierarchy data (" + type(e).__name__ + ": " + str(e) +")")

def _process_joints_stream(joints_stream_data):
    '''
    We receive "full" local rotations and local translations.
    So we need to substract rotate axis and joint orient.
    '''
    global JOINTS_BUFFER

    try:
        joints_data = joints_stream_data["Joints"]

        for joint_data in joints_data:
            # We select all joints having the given name
            joint_name = joint_data['Name']
            maya_joints = JOINTS_BUFFER[joint_name]

            if maya_joints:
                for maya_joint in maya_joints:
                    # W = [S] * [RO] * [R] * [JO] * [IS] * [T]
                    quat = pmc.datatypes.Quaternion(joint_data['LocalRotation'])                
                    vRO = maya_joint.getRotateAxis()
                    RO = pmc.datatypes.EulerRotation(vRO[0], vRO[1], vRO[2]).asQuaternion()
                    joint_orient = maya_joint.getOrientation()
                    quat = RO.inverse() * quat * joint_orient.inverse()
                    maya_joint.setRotation(quat, space='transform')

                    joint_type = joint_data["AnatomicalType"]
                    if joint_type == 7: # This is a 6 DoFs joint so consider translation part too
                        translation = pmc.datatypes.Vector(joint_data["LocalTranslation"])
                        # Mosketch uses meters. Maya uses centimeters
                        translation *= 100
                        maya_joint.setTranslation(translation, space='transform')
    except KeyError:
        #_print_error("cannot find " + joint_name + " in maya")
        pass
    except Exception as e:
        _print_error("cannot process joints stream (" + type(e).__name__ + ": " + str(e) +")")

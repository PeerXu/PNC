#!/usr/bin/env python
# -*- coding: utf-8 -*-

#LIBVIRT_CONNECTION = "qemu:///system"
LIBVIRT_CONNECTION = "test:///default"
#STD_XML_CHAR = "abcdefghijklmnopqrstuvwxyz\
#                ABCDEFGHIJKLMNOPQRSTUVWXYZ\
#                0123456789\
#                _"

STANDARD_XML = """<domain type='kvm'>
    <name>{{ NAME }}</name>
  <uuid>{{ UUID }}</uuid>
  <memory>{{ MEMORY }}</memory>
  <currentMemory>{{ CURRENTMEMORY }}</currentMemory>
  <vcpu>{{ VCPU }}</vcpu>
  <os>
    <type arch="i686">hvm</type>
  </os>
  <clock sync="localtime"/>
  <devices>
    <emulator>/usr/bin/qemu-kvm</emulator>
    <disk type='file' device='disk'>
      <source file='{{ DISK_SOURCE_FILE }}'/>
      <target dev='{{ DISK_TARGET_DEV }}'/>
    </disk>
    <interface type='network'>
      <source network='default'/>
      <mac address='{{ MAC_ADDRESS }}'/>
    </interface>
    <graphics type='vnc' port='-1' keymap='de'/>
  </devices>
</domain>"""

#
# PATH
#

#HOME_PATH = "/home/cloud/PNC/"
HOME_PATH = "/home/peer/workspace/PNC/"

TOOLS_PATH = HOME_PATH + "tools/"

LOG_PATH = HOME_PATH + "log/"

#
#  LOG
#

# NOTEST 0
# DEBUG 10
# INFO 20
# WARNING 30
# ERROR 40
# CRITICAL 50
LOG_LEVEL = 10

CLC_LOG = LOG_PATH + "clc.log"

CLUSTER_LOG = LOG_PATH + "cluster.log"

NODE_LOG = LOG_PATH + "node.log"

#
# CLC
#

#
# CLUSTER
#

CLUSTER_ADDR = ('localhost', 18002)

#
# NODE
#

NODE_ADDR = ('localhost', 18003)

NODE_RESERVE_MEM = 256

NODE_WEIGHT = 4

NODE_MONITOR_INTERVAL = 5

TEARDOWN_STATE_DURATION = 10 #180
BOOTING_CLEANED_THRESHOLD = 10 #60 * 60 * 2

NODE_PASSWD = "ji97ilkoa"

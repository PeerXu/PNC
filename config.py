#!/usr/bin/env python
# -*- coding: utf-8 -*-

VERSION = "0.1.1"

LIBVIRT_CONNECTION = "qemu:///system"
#LIBVIRT_CONNECTION = "test:///default"
#STD_XML_CHAR = "abcdefghijklmnopqrstuvwxyz\
#                ABCDEFGHIJKLMNOPQRSTUVWXYZ\
#                0123456789\
#                _"

INSTANCE_MAC_PREFIX = "0A:EE:EE"

STANDARD_XML = """
<domain type='kvm'>
  <name>{{ NAME }}</name>
  <uuid>{{ UUID }}</uuid>
  <memory>{{ MEMORY }}</memory>
  <currentMemory>{{ CURRENTMEMORY }}</currentMemory>
  <vcpu>{{ VCPU }}</vcpu>
  <os>
    <type arch='x86_64' machine='pc-0.12'>hvm</type>
    <boot dev='hd'/>
  </os>
  <features>
    <acpi/>
    <apic/>
    <pae/>
  </features>
  <clock offset='utc'/>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>restart</on_crash>
  <devices>
    <emulator>/usr/bin/kvm</emulator>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2' cache='writeback'/>
      <source file='{{ DISK_SOURCE_FILE }}'/>
      <target dev='{{ DISK_TARGET_DEV }}' bus='ide'/>
    </disk>
    <interface type='network'>
      <source network='default'/>
      <mac address='{{ MAC_ADDRESS }}'/>
    </interface>
    <console type='pty'>
      <target port='0'/>
    </console>
    <console type='pty'>
      <target port='0'/>
    </console>
    <input type='mouse' bus='ps2'/>
    <graphics type='vnc' port='-1' autoport='yes' keymap='en-us'/>
    <video>
      <model type='cirrus' vram='9216' heads='1'/>
    </video>
  </devices>
</domain>
"""

#
# PATH
#
HOME_PATH = "/home/peer/PNC/"

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

NC_CALL_MAX = 4

CLUSTER_MONITOR_INTERVAL = 5 # second

#
# NODE
#

NODE_ADDR = ('localhost', 18003)

NODE_RESERVE_MEM = 256

NODE_WEIGHT = 4

NODE_MONITOR_INTERVAL = 5 # second

TEARDOWN_STATE_DURATION = 10 #180
BOOTING_CLEANED_THRESHOLD = 10 #60 * 60 * 2

NODE_PASSWD = "asd"

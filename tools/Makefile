BIN=get_sys_info startup_node startup_cluster populate_arp

DEST=/usr/sbin
SRC=/home/cloud/workspace/PNC/tools

LN=ln
LFLAGS=-s

all:	install

install:
	sudo chmod a+x $(BIN)
	(cd $(DEST); for bin in $(BIN); do if [ ! -x $$bin ];then sudo $(LN) $(LFLAGS) $(SRC)/$$bin $$bin; fi; done)

clean:
	(cd $(DEST); sudo rm -rf $(BIN))

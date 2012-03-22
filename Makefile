PROJECTNAME=PNC
ETAGS=TAGS
GTAGS=GPATH GRTAGS GSYMS GTAGS
TAGS=$(ETAGS) $(GTAGS)
CURDIR=`pwd`
INSTALLDIR=/opt/$(PROJECTNAME)
USER=`whoami`

RM=rm -rf

install:
	sudo ln -s $(CURDIR) $(INSTALLDIR)
	sudo chown $(USER) $(INSTALLDIR)
	(cd tools; make install)

uninstall:
	sudo rm $(INSTALLDIR)
	(cd tools; make uninstall)

reinstall:
	make uninstall
	make install

tags:
	find . -name "*.py" | xargs etags -a
	gtags

clean:
	$(RM) -f $(TAGS)
	find . -name "*~" | xargs $(RM) -f
	for f in `find . -name "*.pyc"`;do rm -rf $$f;done

lines:
	count=0; for f in `find . | grep -v .*git.* | grep -v *.log | grep -v .*.img | grep -v *.db`; do if [ ! -d $$f ]; then count=$$count+`cat $$f | wc -l`; fi; done; echo $$count | bc

ETAGS=TAGS
GTAGS=GPATH GRTAGS GSYMS GTAGS
TAGS=$(ETAGS) $(GTAGS)

RM=rm -rf



tags:
	find . -name "*.py" | xargs etags -a
	gtags

clean:
	$(RM) -f $(TAGS)
	find . -name "*~" | xargs $(RM) -f
	for f in `find . -name "*.pyc"`;do rm -rf $$f;done

lines:
	(cd log; rm -f *.log)
	count=0; for f in `find .`; do if [ ! -d $$f ]; then count=$$count+`cat $$f | wc -l`; fi; done; echo $$count | bc

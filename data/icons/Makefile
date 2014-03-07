# Original workspace files in the 'src' dir (not in the git repo)

# Inkscape fails to convert SVG to small PNG (it omits parts of the image).
# For this reason, we create a big PNG, then convert it to smaller ones.

SRC = hicolor/scalable/apps/photocollage.svg
BIG = hicolor/256x256/apps/photocollage.png
SMALL := $(shell for s in 16 22 24 32 48 64 128; do \
	echo hicolor/$${s}x$${s}/apps/photocollage.png; done)

all: $(BIG) $(SMALL)

$(BIG): $(SRC)
	$(eval SIZE := $(shell echo $@ | cut -d/ -f2))
	@echo "  SVG -> PNG  $(SIZE)"
	@mkdir -p $(shell dirname $@)
	@inkscape -z -e $@ -w 256 -h 256 $< >/dev/null

$(SMALL): $(BIG)
	$(eval SIZE := $(shell echo $@ | cut -d/ -f2))
	@echo "  PNG -> PNG  $(SIZE)"
	@mkdir -p $(shell dirname $@)
	@convert $< -resize $(SIZE) $@

.PHONY: clean
clean:
	rm -f $(BIG) $(SMALL)

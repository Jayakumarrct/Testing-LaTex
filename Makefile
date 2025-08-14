.PHONY: all clean

all:
	latexmk -pdf -interaction=nonstopmode -shell-escape main.tex

clean:
	latexmk -C

.PHONY: all clean pdf

all:
	latexmk -pdf -interaction=nonstopmode -shell-escape main.tex

pdf: all

clean:
	latexmk -C

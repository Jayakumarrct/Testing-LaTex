# Galois Theory — Graduate Notes

## Outline
1. Fields and polynomials  
2. Field extensions and minimal polynomials  
3. Splitting fields and algebraic closure  
4. Automorphisms and fixed fields  
5. Separable and normal extensions  
6. Galois extensions and the Fundamental Theorem  
7. Finite fields  
8. Cyclotomic and basic Kummer theory (over fields with enough roots of unity)  
9. Solvability by radicals and the insolvability of the general quintic  
10. Worked examples and computations  
11. Infinite Galois theory and the Krull topology  
12. Classical geometric constructibility  
99. Figures and diagrams

### Prerequisites
- Basic ring and module theory
- Group actions and Sylow theorems
- Polynomial rings over fields

### Build
Compile with `latexmk` or the provided `Makefile`:
```bash
latexmk -pdf -interaction=nonstopmode main.tex
# or
make
```

## Styling
The preamble now loads a light, print-friendly theme:

- `newtxtext,newtxmath` for readable text and math fonts
- `geometry` for A4 layout with 1in margins
- `xcolor` with a pastel palette (`SoftBlue`, `SoftGreen`, `SoftPurple`, `SoftGray`, `Ink`)
- `tcolorbox` and `titlesec` for boxed theorems and subtle headings
- `hyperref`+`cleveref` for colored links and smart references

Customize the palette by adjusting the `Soft*` color definitions in `main.tex`.

Three lightweight box environments are available:

- `infobox` for general notes
- `defbox` for definitions
- `thmbox` for theorems (with optional `theobox`, `defnbox`, and `exbox` wrappers)

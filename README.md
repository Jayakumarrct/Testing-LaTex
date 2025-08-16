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
```bash
latexmk -pdf -interaction=nonstopmode -shell-escape main.tex
```

## Proof Style
Proofs use the plain `amsthm` environment with simple English and only the steps needed. When a proof ends with a displayed equation we place the symbol using `\qedhere`. Sections&nbsp;1–2 and 9–12 now follow this style.

## Worked Examples
Example files live under `examples/section-*-examples.tex`. Add more by following the same format and labeling examples as `ex:sec<i>-<k>`. Compile the notes with:
```bash
make pdf
```

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



## Worked Examples
Example files live under `examples/section-*-examples.tex`. Add more by following the same format and labeling examples as `ex:sec<i>-<k>`. Compile the notes with:
```bash
make pdf
```

## Portrait Figures (Section 13)
Portrait images live under `assets/figures/people/`. To add a new portrait:
1. Ensure the image on Wikimedia Commons is Public Domain or CC BY/SA.
2. Download and convert to EPS with:
   ```bash
   pip install -r requirements.txt  # once
   python tools/fetch_and_convert.py IMAGE_URL assets/figures/people/filename.eps
   ```
3. Record title, author, year, license, and source URL in `CREDITS.md`.

If internet access is disabled, enable it and allowlist `commons.wikimedia.org` before fetching portraits.

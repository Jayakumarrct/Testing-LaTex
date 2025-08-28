# GALOIS THEORY CHEAT CODE
## Graduate-Level Study Guide & Quick Reference

### 📋 **OVERVIEW & ROADMAP**
This comprehensive guide covers Galois Theory from foundations to advanced applications. **Prerequisites:** Basic ring/field theory, group actions, Sylow theorems, polynomial rings.

---

## 1️⃣ **FIELDS & POLYNOMIALS** (Foundation Layer)

### Key Definitions
- **Field**: Commutative ring with multiplicative inverses for nonzero elements
- **Characteristic**: Smallest n such that n·1=0 (0 or prime p)
- **Prime Field**: Smallest subfield (ℚ or ℱₚ)

### Essential Theorems
- **Division Algorithm**: F[x] is Euclidean → PID → UFD
- **Eisenstein Criterion**: p divides all but leading coefficient, p²∤ constant term → irreducible
- **Degree 2/3 Irreducibility**: Irreducible iff no roots in base field

### 🔥 Pro Tips
- Always check characteristic first (affects everything!)
- For irreducibility: Try rational root theorem, then Eisenstein, then modulo p
- Remember: F[x] behaves like ℤ - Euclidean domain with degree metric

---

## 2️⃣ **FIELD EXTENSIONS & MINIMAL POLYNOMIALS**

### Core Concepts
- **Extension Degree**: [E:F] = dimension as F-vector space
- **Minimal Polynomial**: Monic irreducible polynomial with α as root
- **Simple Extension**: F(α) where α satisfies minimal polynomial of degree [F(α):F]

### Key Formulas
- [F(α,β):F] ≤ [F(α):F] × [F(β):F] (multiplicative when disjoint)
- If f irreducible degree n, then [F(α):F] = n for any root α

### Problem-Solving Algorithm
1. Find minimal polynomial m_α(x) over F
2. Degree of extension = deg(m_α)
3. For multiple elements: Use tower formula [F(α,β):F] = [F(α,β):F(α)] × [F(α):F]

---

## 3️⃣ **SPLITTING FIELDS & ALGEBRAIC CLOSURE**

### Definitions
- **Splitting Field**: Smallest field containing all roots of a polynomial
- **Algebraically Closed**: Every non-constant polynomial has a root
- **Algebraic Closure**: Algebraic closure of F (denoted F̄)

### Construction
- Start with F, adjoin roots one by one
- Degree: [splitting field:F] divides n! for degree n polynomial

### Common Splitting Fields
- x²-d: ℚ(√d), degree 2
- x³-2: ℚ(∛2, ζ₃), degree 6
- x⁴-2: ℚ(⁴√2, i), degree 8

---

## 4️⃣ **AUTOMORPHISMS & FIXED FIELDS**

### Galois Group Definition
Gal(E/F) = Aut_F(E) = {σ: E→E | σ|F = id_F, σ field homomorphism}

### Key Properties
- |Gal(E/F)| ≤ [E:F], equality iff Galois extension
- For finite extension: Galois group acts on roots
- Fixed field E^G = {x ∈ E | σ(x)=x ∀σ ∈ G}

### 🔥 Pro Tip
Galois group measures "symmetries" of the extension. Larger group = more symmetry = more structure.

---

## 5️⃣ **SEPARABLE & NORMAL EXTENSIONS**

### Separable Extensions
- **Definition**: Minimal polynomials are separable (no repeated roots)
- **Criterion**: Char ≠ p or inseparable degree < p
- **Perfect Fields**: ℝ, ℂ, finite fields, char 0 fields

### Normal Extensions
- **Definition**: Splitting field of some polynomial in base field
- **Equivalent**: Every irreducible polynomial with root in E splits in E

### Galois Extensions
**Galois = Normal + Separable**

---

## 6️⃣ **FUNDAMENTAL THEOREM OF GALOIS THEORY** ⭐⭐⭐

### The Big Bijection
```
Intermediate Fields F ⊆ K ⊆ E
        ↕️ inclusion-reversing
Subgroups H ≤ Gal(E/F)
```

### Key Formulas
- [E:K] = |H| where H = Gal(E/K)
- [K:F] = |G|/|H| where G = Gal(E/F)
- K/F normal ⇔ H ◅ G, then Gal(K/F) ≅ G/H

### Problem-Solving Flowchart
1. Identify Galois extension E/F with group G
2. Find subgroups H of G
3. Corresponding fixed fields K = E^H
4. Degrees: [E:K] = |H|, [K:F] = |G|/|H|

---

## 7️⃣ **FINITE FIELDS**

### Structure
- ℱₚ = {0,1,...,p-1} with mod p arithmetic
- ℱₚⁿ: Unique up to iso, |ℱₚⁿ| = pⁿ
- Gal(ℱₚⁿ/ℱₚ) ≅ ℂₙ (cyclic of order n)

### Frobenius Automorphism
σ: x ↦ xᵖ (generator of Galois group)

### Subfields
- Subfields of ℱₚⁿ are ℱₚᵈ where d|n
- Galois correspondence works perfectly

---

## 8️⃣ **CYCLOTOMIC & KUMMER THEORY**

### Cyclotomic Extensions
- **Cyclotomic Polynomial**: Φₙ(x) = ∏(x-ζ) where ζ runs over primitive n-th roots
- **Degree**: φ(n) = |{k < n | gcd(k,n)=1}|
- **Galois Group**: Gal(ℚ(ζₙ)/ℚ) ≅ (ℤ/nℤ)ˣ

### Kummer Extensions
**Theorem**: If char F ≠ p and p doesn't divide [E:F], then E = F(α) where αᵖ ∈ F

### Common Examples
- p=2: Quadratic extensions ℚ(√d)
- p=3: Cubic extensions like ℚ(∛2)
- General: Abelian extensions of exponent p

---

## 9️⃣ **SOLVABILITY BY RADICALS & THE QUINTIC**

### Radical Extensions
Tower F ⊆ F(√[n₁]a₁) ⊆ F(√[n₁]a₁, √[n₂]a₂) ⊆ ... ⊆ E

### Solvability Criterion
**f solvable by radicals over F ⇔ Gal(splitting field/F) is solvable**

### The Quintic Insolvability
- General quintic: Galois group S₅
- S₅ not solvable (has A₅ ≅ A₅ simple nonabelian)
- **Corollary**: General quintic not solvable by radicals

### Detecting Sₙ
- Irreducible prime degree p polynomial
- Exactly 2 non-real roots
- **Then**: Galois group ≅ Sₚ

---

## 🔟 **WORKED EXAMPLES PATTERNS**

### Common Problem Types
1. **Degree Computations**: Use tower formula, minimal polynomials
2. **Galois Group**: Find splitting field, count automorphisms
3. **Fixed Fields**: Given subgroup H, find E^H
4. **Subgroup from Field**: Given K, find Gal(E/K)
5. **Irreducibility**: Eisenstein, modulo p, rational roots
6. **Solvability**: Check if Galois group solvable

### Standard Techniques
- **Minimal Polynomials**: Always find these first
- **Discriminants**: For quadratic/cubic irreducibility
- **Frobenius/Mod p**: For finite field questions
- **Complex Conjugation**: For real subfields

---

## 🧮 **PROBLEM-SOLVING MASTER ALGORITHM**

### For Any Galois Theory Problem:
1. **Identify Base Field** F and Extension E
2. **Find Splitting Field** (if not given)
3. **Compute Extension Degree** [E:F]
4. **Find Galois Group** G = Gal(E/F)
5. **Apply Fundamental Theorem** (bijection between subgroups ↔ subfields)
6. **Compute Degrees** using [E:K] = |H| formula
7. **Check Normality/Separability** as needed

### Quick Degree Calculations:
- Quadratic: [ℚ(√d):ℚ] = 2 (if d square-free)
- Cyclotomic: [ℚ(ζₙ):ℚ] = φ(n)
- Finite: [ℱₚⁿ:ℱₚ] = n
- General: Use tower formula multiplicatively

---

## ⚠️ **COMMON PITFALLS & STUDY TIPS**

### Avoid These Mistakes:
- Forgetting characteristic affects everything
- Mixing up Galois group vs automorphism group
- Confusing splitting field with simple extension
- Not checking separability/normalcy for Galois
- Degree calculations without minimal polynomials

### Study Strategy:
1. **Master Section 1-3** (foundations) before proceeding
2. **Memorize Fundamental Theorem** - it's your north star
3. **Practice with cyclotomic fields** - they're concrete examples
4. **Draw subgroup lattices** for Galois groups
5. **Always compute degrees** - they're your reality check

### Key Insight:
Galois Theory bridges algebra (fields, polynomials) with geometry (symmetries, groups). Think of Galois groups as measuring how much "symmetry" your extension has.

---

## 📚 **QUICK REFERENCE CARDS**

### Essential Isomorphisms:
- Gal(ℚ(√d)/ℚ) ≅ ℂ₂ (d square-free)
- Gal(ℚ(ζₙ)/ℚ) ≅ (ℤ/nℤ)ˣ
- Gal(ℱₚⁿ/ℱₚ) ≅ ℂₙ

### Degree Formulas:
- [E:F(α)] = deg(min poly of α over F)
- [F(α,β):F] ≤ [F(α):F] × [F(β):F]
- Splitting field degree divides n! for degree n poly

### Galois Correspondence:
- More subgroups → more intermediate fields
- Normal subgroup H ↔ normal extension E^H/F
- |H| = [E:E^H], |G|/|H| = [E^H:F]

---

**🎯 FINAL TIP**: Galois Theory is about understanding when you can solve polynomial equations using "allowed" operations (radicals). The Galois group tells you exactly what's possible and what's impossible!
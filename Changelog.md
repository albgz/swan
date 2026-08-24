# SWAN Modernisation - Committed Code Changes

> **Purpose:** explanations and validation evidence for changes that exist in Git history.

## Performance dashboard - modernisation progress

_Last measured: 2026-08-22 · Current source: `188d1c0e3ba42738f0cab84b51b860343734f5b5` · Hardware: AMD Ryzen 7 9700X_

This is the at-a-glance performance record. It must be updated whenever an accepted performance change or a new authoritative baseline is added.
### Initial versus current - same PF Basin workload

The initial measurement used untouched `main` with SWAN's then-default `-O` build. The current measurement uses the accepted production configuration, GNU Fortran 16.2.1 with `-O3 -march=native -DNDEBUG`, plus all accepted source optimisations. Both use the same PF Basin case and one warm-up followed by three retained runs.

| Execution mode | Initial median | Current median | Runtime reduction | Overall speedup |
|---|---:|---:|---:|---:|
| One CPU thread | 19.288 s | **8.753 s** | **54.6% less time** | **2.204×** |
| Eight OpenMP threads | 3.569 s | **1.937 s** | **45.7% less time** | **1.842×** |

The current PF Basin runs reproduced the accepted full-domain table exactly in every retained run: `260dd8d888e43eb68b374a21f3e97097c9b554610d9a2eb5fd0204654073211c`. The stronger production compiler configuration has the documented small last-decimal output-family difference from the original `-O` build; accepted source optimisations remain exact within the frozen production output family.

### Current authoritative CPU baseline

For the retained `f31har02` scaling workload, the frozen production baseline is **6.9506 s serial** and **1.1397 s with OpenMP-8**, a **6.099×** thread speedup. This is a different workload from PF Basin, so it is recorded as the current production baseline and is not used to calculate the initial-versus-current percentages above.

### Update rule

After every accepted performance change:

1. rerun `swan_modernisation_data/performance_dashboard/measure_pf_basin.py`,
2. require the protected PF Basin output hash,
3. update the current medians, source commit, date, reductions, and speedups in this section,
4. update the `f31har02` baseline only after a new frozen scaling campaign.

---

## Reading rule

Every detailed entry below maps to a real commit between starting commit `43e9bbba393f2cf9eaff78bc92eaed118a3a5c8e` and current committed source `188d1c0e3ba42738f0cab84b51b860343734f5b5`. Measurements embedded in an entry explain the corresponding commit's validation; experiment-only entries are not duplicated here.

---

# Committed change journal
## We reused and revalidated the small build repair

**Date:** 2026-08-21  
**Source state:** `main` at `58fcc10` (parent `43e9bbb`)  
**Commit message:** “Keep generated Fortran files inside the build directory”  
**Change type:** Build-system repair; no scientific Fortran code changed.  
**Push status:** Nothing pushed.

### What changed?

We recovered the previously tested build repair from an abandoned branch (technical ID `903e3de`) and revalidated it against the current `main` source. It makes three things happen:

1. The source switcher, the small program that prepares the exact Fortran files to compile for a chosen configuration, now writes its output only into the build directory. The original source tree stays untouched.
2. The optimisation setting chosen by the person building SWAN is now carried all the way to the compiler, instead of being silently overridden.
3. A real parser bug in `switch.pl` is fixed: a source path containing a hyphen was mistaken for a command-line switch, which could make the configuration step loop forever. This is the same bug we hit when storing the starting baseline, and the repair removes it.

### Why does it matter?

The wave calculation itself is unchanged. But every later speed improvement in this campaign has to be measured against a build that is stable and reproducible. Before this change, generated files could end up next to the original sources and the intended optimisation level could be lost, so two builds that “look the same” could actually behave differently. With the repair in place, each recorded configuration is the configuration that actually ran, which is what makes the later before/after comparisons trustworthy.

### Did the scientific result change?

No. The equivalent `-O` build-the same optimisation level SWAN builds with today-reproduces the untouched `main` result exactly in all six retained runs (three one-thread and three eight-thread). Every checked result file matches the starting fingerprints from Entry 3.

We also evaluated the stronger `-O3 -march=native` setting separately, as planned. It reproduces the small numerical difference already recorded for that setting, not a new one: 45 of 81,217 significant-wave-height rows differ by at most 0.00001 m, 130 period rows differ by at most 0.0001 s, and depth is unchanged. The wave field is the same to the printed scientific precision. This is recorded as a documented small numerical change, as the plan requires, and the stronger build is kept as a separate candidate configuration rather than being presented as exact.

### How much faster or slower is it?

The build repair itself does not change the calculation, so the `-O` timing is the same starting point within normal measurement variation:

| Configuration | Entry 3 untouched main (median) | After repair, `-O` (median) | After repair, `-O3 -march=native` (median) |
|---|---:|---:|---:|
| One CPU thread | 19.288 s | 18.990 s | 11.331 s |
| Eight OpenMP threads | 3.569 s | 3.520 s | 2.218 s |
| Eight-thread speedup over one thread | 5.40× | 5.40× | 5.11× |

The `-O3` build is 1.68 times faster than the `-O` build with one thread and 1.59 times faster with eight threads, and its one-thread and eight-thread timings match the earlier experiment’s numbers almost exactly. That agreement is strong evidence we are comparing the same machine, compiler, and case.

### What did we check?

- 16 Python tests for the CMake configuration and the source switcher, plus the two registered build tests in both the serial and OpenMP trees, all passing.
- One warm-up plus three retained runs of the repaired `-O` build in each mode; all six outputs exact against the Entry 3 fingerprints.
- One warm-up plus three retained runs of the `-O3 -march=native` build in each mode; normal termination, no unexpected warnings, and the table compared column by column against the `-O` oracle.
- Confirmation that no generated Fortran files appear in the source tree and that the source tree contains only the intended eight changed files.

### Technical details

```text
Commit: 58fcc10ab5ce562d5169bddeb2c04a735233ad97
Parent: 43e9bbba393f2cf9eaff78bc92eaed118a3a5c8e
Reused source commit: 903e3def5d89de8da586562ef396c9f6deb20f9e (applied without redesign)

Changed paths:
CMakeLists.txt
cmake/SwanCompilerOptions.cmake
cmake/SwanSourceSwitch.cmake
src/CMakeLists.txt
src/hcat/CMakeLists.txt
switch.pl
tests/test_cmake_configuration.py
tests/test_switch.py

Compiler: GNU Fortran 16.2.1 20260810, Ninja generator
-O configuration: CMAKE_BUILD_TYPE=None, CMAKE_Fortran_FLAGS=-O,
  options OPENMP=OFF/ON, MPI=OFF, JAC=OFF, FFRO=OFF, METIS=OFF, NETCDF=OFF
-O3 configuration: CMAKE_BUILD_TYPE=Release,
  CMAKE_Fortran_FLAGS_RELEASE='-O3 -march=native -DNDEBUG'

Workload: PF Basin, 337 x 241 grid, 41 frequencies, 36 directions, 8 sweeps
Affinity: serial pinned to core 4; OpenMP-8 pinned to cores 0-7;
  OMP_PROC_BIND=TRUE, OMP_PLACES=cores, OMP_DYNAMIC=FALSE,
  OMP_MAX_ACTIVE_LEVELS=1, OMP_NESTED=FALSE, OMP_STACKSIZE=64M
Run order: alternating serial/OpenMP retained runs, one warm-up first

Exact -O fingerprints (all six retained runs):
PRINT.normalized: 75d4392b0cebd5bf96938f4eadc6877d289945a553abdfef40362dea7136ee93
full_domain_table.dat: fa1af2504f3a416b7ac3a3836203f809c4cea9c032232a3a52bae6da347ed86d
norm_end: 4b9919000496e5d00d3d1c99f1cc3b32a2457ab8310bc3c8cf12054c8651c407
swaninit: 71e4263799386bf36f5d18e38bfaea4b0daede5355fae4cbe6cd2c4eaee48f34

-O3 full_domain_table.dat fingerprint:
260dd8d888e43eb68b374a21f3e97097c9b554610d9a2eb5fd0204654073211c
(identical to the historical -O3 experiment's fingerprint)


```


## We reused the stationary wave-value cache

**Date:** 2026-08-21  
**Source state:** `main` at `b3d94df` (parent `58fcc10`)  
**Commit message:** “Reuse wave values when the water depth has not changed”  
**Change type:** CPU optimization; the wave calculation is mathematically unchanged.  
**Push status:** Nothing pushed.

### What changed?

SWAN needs two wave properties at every grid point: the intrinsic wave-number (how tightly the wave crests fit together in still water) and the group velocity (how fast the wave energy travels in still water). These are calculated by the routine `KSCIP1` from the water depth at that point.

In a run where the seabed is fixed and there are no currents, those properties do not change while the model runs. The old code did not use that fact: it recalculated them at every grid point, for every direction sector, every sweep, and every time step-thousands of identical calculations.

The change works like a lookup table. When a run is known to be “stationary” (fixed depth, no currents, no mud or other moving processes), SWAN now calculates the wave-number and group velocity once per frequency for the whole grid, keeps them in memory, and reuses the stored values instead of recalculating. At the end of the calculation the stored values are released. If the run is not stationary, or if the memory cannot be allocated, SWAN falls back to the original calculation path exactly as before.

### Why does it matter?

This is pure removed repetition: the model now performs less work and calculates exactly the same wave field. There is no new physics, no changed equation, and no changed parameter. For every production case with a fixed bathymetry and no currents-which is the common setting-SWAN runs noticeably faster without any loss of scientific content.

### Did the scientific result change?

No. In every retained run, the wave field, the printed results, the convergence decisions, and the termination all matched the trusted reference exactly. The cache stores precisely the values the original calculation would have produced, so the result is bit-identical.

### How much faster is it?

Measured on the PF Basin case, one warm-up followed by three alternating before/after pairs in each mode (the candidate was faster in all six comparisons):

| Mode | Before (median, s) | After (median, s) | Speedup |
|---|---:|---:|---:|
| One CPU thread | 11.330 | 9.579 | **1.183× (+18.3%)** |
| Eight OpenMP threads | 2.218 | 2.017 | **1.099× (+10.0%)** |

These measurements reproduce the earlier experiment’s +18.2% and +10.0% almost exactly, which is a good sign that the same machine, compiler, and test case are in use.

### What did we check?

- The cache is only active when all of these hold: stationary depth (`NSTATC = 0`), no currents (`ICUR = 0`), no mud (`IMUD = 0`), no variable mud, no dynamically changing depth, no setup calculation, no wave tracing, and not distributed over several computers (MPI). Otherwise the original path runs.
- If the memory allocation fails, the cache is abandoned and the original path runs.
- One fresh build each for the serial and OpenMP configurations from the current candidate source.
- 16 Python build-system tests plus the two registered build tests in both candidate build trees, all passing.
- One warm-up plus three retained runs in each mode; every retained run terminated normally with no unexpected output, and all result fingerprints matched the trusted `-O3` reference exactly (table fingerprint `260dd8d8…`, the documented small last-decimal difference from the `-O` reference).

### Technical details

```text
Commit: b3d94df57f1ca8124c6c8a7a97feb7a21cff810f
Parent: 58fcc10ab5ce562d5169bddeb2c04a735233ad97
Reused source commit: 5053713d0bf42a549abbbfc5648c1240ef8a8e89 (applied without redesign)

Changed paths:
src/swancom1.ftn   (cache allocation, eligibility, fill, release)
src/swancom5.ftn   (lookup instead of KSCIP1 in the stationary branch)
src/swmod1.ftn     (new module-level allocatable KWAVE_CACHE, CGO_CACHE, KCGCACHE_ACTIVE)

Compiler/flags: GNU Fortran 16.2.1 20260810, -O3 -march=native -DNDEBUG,
  OPENMP=OFF/ON, MPI=OFF, JAC=OFF, FFRO=OFF, METIS=OFF, NETCDF=OFF, Ninja
Baseline binary: post_build_repair_43e9bbb/build_o3_{serial,openmp} (commit 58fcc10)
Candidate binary: task4_kcg_cache/build_{serial,openmp} (uncommitted source at validation)

Paired timing (s), baseline vs candidate per pair:
  serial:  11.431/9.629, 11.281/9.579, 11.330/9.579
  openmp8:  2.218/2.017,  2.218/2.017,  2.217/2.068
Median speedups: serial 1.183x, openmp-8 1.099x; candidate faster in all 6 runs

Memory cost: two MSC x MCGRD real arrays (41 x 81218 x 2 x 4 bytes, ~26.5 MB),
  allocated and released once per SWCOMP invocation.


```


## We reused the wave-direction selection when currents are disabled

**Date:** 2026-08-21  
**Source state:** `main` at `2a878f8` (parent `b3d94df`)  
**Commit message:** “Reuse wave directions when currents are disabled”  
**Change type:** CPU optimization; the wave calculation is mathematically unchanged.  
**Push status:** Nothing pushed.

### What changed?

When SWAN moves waves from one grid point to its neighbours, it first works out which “direction sectors” of the 36 possible wave directions actually matter at that point. The sector depends on the direction of the wave and, if currents are switched on, on how those currents bend the wave paths.

When currents are disabled-and that is the common production setting-nothing about that classification depends on the wave frequency. The old code nevertheless recomputed it from scratch for every one of the 41 frequencies. The change keeps the classification computed for the first frequency and reuses it for the remaining 40, in exactly the same cases where the classification really is the same.

All of the bookkeeping that the original code performed-per-sector flags, the smallest and largest active sector number, the running sweep-stop marker, and every edge case-is preserved. The fast path activates only when `ICUR = 0` and the frequency is not the first one.

### Why does it matter?

Like the previous change, this removes repeated identical work: trigonometric and classification computations that produce the same answer every time are done once instead of 41 times per grid point. There is no change to the physics, to the direction set, or to any model parameter. Production cases without currents run faster with the identical wave field.

### Did the scientific result change?

No. Every retained run terminated normally and matched the trusted reference exactly-the wave field, the printed results, the convergence decisions, and the sweep behavior. Reusing a classification that is provably identical for all frequencies cannot change the result.

### How much faster is it?

Measured on the PF Basin case against the new baseline that includes the previous change (one warm-up, then three alternating before/after pairs in each mode; the candidate was faster in all six comparisons):

| Mode | Before (median, s) | After (median, s) | Speedup |
|---|---:|---:|---:|
| One CPU thread | 9.678 | 8.978 | **1.067× (+6.7%)** |
| Eight OpenMP threads | 2.017 | 1.917 | **1.052× (+5.2%)** |

These reproduce the earlier experiment’s +6.68% and +5.22% almost exactly.

Together with the previous entry, the two recovered optimizations take the same PF Basin case from 11.330 s to 8.978 s on one thread (−20.8%) and from 2.218 s to 1.917 s on eight threads (−13.6%), relative to the post-build-repair starting point.

### What did we check?

- The fast path activates only when `ICUR = 0` and the frequency index is greater than 1; any run with currents takes the original path for every frequency.
- The reused state includes `ANYBIN`, `IDCMIN`, `IDCMAX`, `SECTOR`, and the sweep-stop update (`ISSTOP`), so no downstream behavior differs.
- One fresh build each for the serial and OpenMP configurations from the current candidate source.
- The 16 Python build-system tests plus the registered build tests in the candidate build tree, passing.
- One warm-up plus three retained runs in each mode; all result fingerprints matched the trusted `-O3` reference exactly (table fingerprint `260dd8d8…`).

### Technical details

```text
Commit: 2a878f8bcae108967de4066c20d0fbff4f9a6bf5
Parent: b3d94df57f1ca8124c6c8a7a97feb7a21cff810f
Reused source commit: e3573aab1c9b40d146cc07373e70f93252242574 (applied without redesign)

Changed path: src/swancom5.ftn  (+14 lines, one fast path in the SWPSEL sector classification)

Compiler/flags: GNU Fortran 16.2.1 20260810, -O3 -march=native -DNDEBUG,
  OPENMP=OFF/ON, MPI=OFF, JAC=OFF, FFRO=OFF, METIS=OFF, NETCDF=OFF, Ninja
Baseline binary: task4_kcg_cache/build_{serial,openmp} (commit b3d94df)
Candidate binary: task5_swpsel_reuse/build_{serial,openmp} (uncommitted source at validation)

Paired timing (s), baseline vs candidate per pair:
  serial:  9.678/8.978, 9.580/8.978, 9.679/9.078
  openmp8: 2.017/1.917, 2.017/1.917, 2.018/1.917
Median speedups: serial 1.067x, openmp-8 1.052x; candidate faster in all 6 runs

Cumulative vs post-build-repair oracle (58fcc10):
  serial:  11.330 -> 8.978 s  (-20.8%)
  openmp8:  2.218 -> 1.917 s  (-13.6%)


```


## We added a switchable diagnostics build and found a latent bug

**Date:** 2026-08-21  
**Source state:** `main` at `7c8a634` (parent `2a878f8`)  
**Commit message:** “Add an opt-in diagnostics build that surfaces Fortran warnings”  
**Change type:** Build-system addition only; no Fortran source changed, so the scientific result is unchanged by construction.  
**Push status:** Nothing pushed.

### What changed?

We added an optional build setting, `SWAN_DIAGNOSTICS`, that turns on the compiler’s warning and runtime-check machinery for SWAN’s Fortran code. When it is off (the default), nothing changes: the normal build keeps the global warning suppression and produces exactly the same binary behavior as before. When it is on, the compiler is asked to report hidden problems-calls to subroutines that have no explicit interface description, suspicious number conversions, comparisons of real numbers, possibly uninitialised variables, and so on-and the executable gains runtime checks that stop the program with a clear message if it would read an unallocated array or step outside an array’s bounds.

This is the inspection tool for the coming work of gradually moving the code toward Fortran 2018 and removing the `-fallow-argument-mismatch` compatibility switch, which currently lets the compiler silently accept calls whose arguments do not match.

### Why does it matter?

SWAN’s source predates modern Fortran conventions in places: many subroutines are called without the compiler being told exactly what arguments they expect. That used to be harmless because the compiler was told to stay quiet. It is a risk, though: a call with the wrong argument count or type can run “fine” on one machine or configuration and fail on another. The diagnostics build lets us list and fix such problems one cluster at a time, with the normal production build completely unaffected in the meantime.

### Did the scientific result change?

No. The commit changes only build configuration, tests, and documentation. The normal build’s compiler flags are unchanged (proven by a new test), and a fresh normal build of the current source reproduces all four PF Basin reference fingerprints exactly.

### How much faster or slower is it?

Not applicable. The diagnostics build is a maintenance tool, not a performance candidate. The normal build is untouched.

### What did we check?

- 19 build-system tests pass (16 previous plus 3 new: the option defaults to off; the default build still carries the old warning suppression and none of the new diagnostic flags; the diagnostics build carries all nine diagnostic flags).
- A fresh normal `-O3` build ran the PF Basin case to normal termination with exact fingerprints for `PRINT.normalized`, `full_domain_table.dat`, `norm_end`, and `swaninit`.
- The diagnostics build compiled successfully and produced the initial warning inventory: 19,091 classified warnings, of which 13,813 are fixed-form line-truncation artifacts, 3,574 are missing-explicit-interface warnings (the main debt for the next work phase), 481 conversion warnings, 175 “possibly uninitialised” warnings, and 38 array-temporary warnings relevant to later vectorization work.

### A latent bug the diagnostics build exposed

Running the diagnostics executable revealed a real, previously hidden defect: when a case defines boundary conditions but does not request test-point output, the program passes an **unallocated array** to the boundary-condition subroutine. The array in question holds test-point coordinates; it is allocated only when the input requests test points. Without that request it is unallocated, and the boundary-condition code receives it anyway.

The current production build survives this by luck: the receiving routine declares the array with an old-style “assumed size” declaration and only reads it inside a loop that is never entered when no test points exist, so the bad value is never used. It is still undefined behavior under the Fortran standard, and the runtime check turns it into a clear, catchable error. The affected routine and the exact call are recorded; the fix (guaranteeing the array is always allocated, even with zero elements, before the boundary-condition call) is the next change and will be validated on its own.

### Technical details

```text
Commit: 7c8a6349954cfe4eefeebcb30f2da0b0c768608f
Parent: 2a878f8bcae108967de4066c20d0fbff4f9a6bf5

Changed paths:
CMakeLists.txt                    (option SWAN_DIAGNOSTICS, default OFF)
cmake/SwanCompilerOptions.cmake   (GNU diagnostics flag branch; default branch unchanged)
tests/test_cmake_configuration.py (3 new tests)
README.md                         (option documented)

Diagnostics flags (GNU):
  -Wall -Wextra -Wimplicit-interface -Wimplicit-procedure -Wsurprising
  -Wconversion-extra -Warray-temporaries -fcheck=all -fbacktrace
  -fno-second-underscore -ffree-line-length-none
  -fallow-argument-mismatch (kept, warnings not errors, while the debt is repaired)

Initial inventory (19,091 warnings):
  -Wline-truncation        13,813   (generation artifacts, triage first)
  -Wimplicit-interface      3,574   (Task 8 debt)
  -Wconversion-extra          481
  -Wcompare-reals             228
  -Wunused-variable           203
  -Wmaybe-uninitialized       175   (correctness priority)
  -Wfunction-elimination      162
  other                       443

Latent bug: unallocated allocatable XYTST passed to SWBOUN when the case has
  BOU but no STA test-point specification
  swanpre1.ftn:1882  CALL SWBOUN ( XGRDGL, YGRDGL, KGRPGL, XYTST, KGRBGL )
  swmod2.ftn:1026    INTEGER, SAVE, ALLOCATABLE :: XYTST(:)
  swanpre2.ftn:2583  INTEGER XYTST(*)  (assumed-size dummy, read only if NPTST>0)


```


## We fixed unallocated input-field arrays that the runtime check exposed

**Date:** 2026-08-21  
**Source state:** `main` at `fd86cfb` (parent `7c8a634`)  
**Commit message:** “Guarantee optional input fields are allocated before use”  
**Change type:** Correctness fix (undefined behavior); for the normal production path the numerical result is unchanged.  
**Push status:** Nothing pushed.

### What changed?

The new runtime checks from the previous entry caught a real defect the moment they were switched on. SWAN keeps several optional input fields in memory-test-point coordinates, water level, friction, currents, and other time-varying fields. Such a field is loaded from an input file only when the case actually provides that file. The old code, however, handed the field to the boundary-condition and time-stepping subroutines **regardless** of whether the file had been provided. When it had not, the program was passing an empty placeholder (an “unallocated” array) where a real array was expected.

The fix guarantees that every such field is allocated-containing zero data when it is unused-before the first place it is passed. In cases where the field is used, nothing changes: the file load still fills the same array. In cases where it is not used, the field now holds an empty, valid array instead of an invalid one.

### Why does it matter?

Under the Fortran standard, passing an unallocated array where an array is expected is undefined behavior. It happened to run correctly on current machines because the receiving code only reads the field when its feature switch is on-which is off in exactly the cases where the field is empty. But “happens to run” is not a guarantee: a different compiler, a different optimization level, or a future change can turn the same code into a crash or, worse, a silently wrong answer. This fix removes that category of risk for the input-field arrays, with no change to the physics and no change to the result of any correctly specified case.

### Did the scientific result change?

No, for the authoritative builds. Fresh serial and eight-thread builds of the current source reproduce all four PF Basin reference fingerprints **exactly** (wave table, printed output, termination record, and initialization record), and both runs terminate normally with no warnings.

The diagnostics build is a maintenance tool, not a numerical reference, and its runtime-check instrumentation slightly changes the code the compiler optimizes: its wave table matches the reference in 81,168 of 81,217 rows, with 49 individual values differing by at most 0.0001 (last decimal). The printed output, termination record, convergence behavior, and all dimensions are identical. We record this as a documented last-decimal difference of the diagnostic configuration only; the normal Release build remains the exact reference.

### How much faster or slower is it?

No measurable change. The added statements are one-time allocation checks executed once before the time loop; the per-step work is untouched. (The normal-build runs used for the fingerprint gate ran at the expected ~9.0 s serial; no paired benchmark is warranted for a fix that adds one-time checks.)

### What did we check?

- The runtime check (previously aborting startup with “Allocatable actual argument ‘xytst’ is not allocated”, then ‘wlevl’, then ‘fric’) now completes the full PF Basin run in the diagnostics build with zero runtime errors.
- Fresh Release serial and OpenMP-8 builds from the committed source: both ran to “Normal end of run 01” with zero stderr and all four fingerprints exact.
- Column-by-column comparison of the diagnostic-build table against the reference: 49 values, max absolute difference 0.0001 (documented diagnostic-configuration last-decimal difference only).
- All 19 build-system tests still pass (unchanged in this commit).

### The broader finding

The three runtime errors seen in sequence (`xytst`, `wlevl`, `fric`) were the first members of a family: the same pattern-optional field passed unconditionally-applies to 14 time-varying input fields in total. This fix covers the whole family in one bounded change (two files, +23 lines): two guards at the input-stage call sites (boundary conditions, output requests) and one guarantee block before the time loop for the field set. This also removes the last known unallocated-actual-argument defects in the startup and time-stepping paths of the PF Basin case.

### Technical details

```text
Commit: fd86cfbb6d27fbc214997a303058f6c3eafbb124
Parent: 7c8a6349954cfe4eefeebcb30f2da0b0c768608f

Changed paths:
src/swanpre1.ftn  (+2: guaranteed allocation of XYTST before the SWBOUN call,
                  and of WLEVL before the SPROUT call in the input phase)
src/swanmain.ftn  (+21: one-time guarantee block before the time loop for
                  WLEVL, FRIC, UXB, UYB, NPLAF, TURBF, MUDLF, WXI, WYI,
                  AICEF, HICEF, HSSF, TSSF, DSSF, XYTST)

Fields (swmod2.ftn, SAVE, ALLOCATABLE): allocated(0) when the input file
  for the field is not specified; file loads still allocate/resize as before.
Read sites of every field are guarded by the feature flag (IFLDYN(*), VARFR,
  NPTST, ICUR, etc.), so an allocated(0) field is never dereferenced.

Builds validated:
  Release -O3 -march=native -DNDEBUG serial    : exact (4/4 fingerprints)
  Release -O3 -march=native -DNDEBUG openmp-8 : exact (4/4 fingerprints)
  Diagnostics (-fcheck=all) serial             : clean run; table 49 values /
      81217 rows differ by <= 1e-4 (diagnostic configuration only)


```


## We taught the compiler the exact shapes of the eleven most-used helper routines

**Date:** 2026-08-21  
**Source state:** `main` at `876a945` (parent `fd86cfb`)  
**Commit message:** "Add explicit interfaces to the Ocean Pack utility routines"  
**Change type:** Code-quality / safety cleanup (compiler interface debt). For the normal production path the numerical result is unchanged.  
**Push status:** Nothing pushed.

### What changed?

SWAN is built from many small files that call each other's routines. For most of its history, when one file calls a helper routine, the compiler is never told the routine's exact argument list (types, kinds, count). It compiles the call "blind" and accepts whatever the caller hands over. This is legal in the language SWAN was written in, but it means the compiler cannot catch a wrong argument at build time. When we switched the build on, the compiler reported this 3,574 times - the single largest category of warnings in the project.

This entry fixes the largest chunk of that debt: the eleven helper routines that nearly every file calls for error messages, screen tracing, keyword lookups, and similar services (from the "Ocean Pack" utility set). We wrote down each routine's exact argument list in one shared place that almost every file already imports, so the compiler now checks all of those call sites for free - no call was changed. We also removed 99 old lines in 25 files that used to hint at two of these routines' return types by hand; those hints now contradicted the new shared definition, and 8 of them were hidden behind feature switches, which is why we checked every switch variant, not just the default one.

### Why does it matter?

Nothing in the physics or in the result of a correctly specified case changes. The value is in the safety margin: any of the 2,206 call sites that would have silently passed a wrong argument type to one of these helpers is now a hard build error instead of a possible silent corruption of a run. This is the first of several bounded slices of the 3,574 warnings; each slice is checked the same way - build, run, byte-compare the output.

### Did the scientific result change?

No. Fresh serial and eight-thread builds of the committed source reproduce all four PF Basin reference fingerprints **exactly** (wave table, printed output, termination record, initialization record), and both runs terminate normally with zero warnings.

The diagnostics build (the maintenance configuration with extra runtime checks) again shows its documented last-decimal difference only: 49 of 81,217 table values differ by at most 0.0001 versus the Release reference - bit-identical to the previous entry's diagnostics fingerprint, so this cleanup adds no new difference there.

### How much faster or slower is it?

No measurable change. Three alternating-order paired runs, pinned (serial on core 4, eight threads on cores 0–7), with the reference fingerprints re-verified on every measured run: serial median 8,840 ms → 8,885 ms and eight-thread median 1,910 ms → 1,900 ms, each within the ~0.2% run-to-run spread of the fixture (full numbers in the task data directory).

### What did we check?

- Fresh Release serial and OpenMP-8 builds of the committed source: both ran to "Normal end of run 01", zero stderr, all four fingerprints exact.
- Fresh diagnostics build: clean run; table 49 values / 81,217 rows differ by ≤ 0.0001, matching the previous entry's diagnostics fingerprint bit-for-bit.
- The warning count for the fixed category dropped from 3,574 to 1,368 (a 61.7% reduction of it); the overall build warning count dropped from 19,091 to 16,862.
- All 19 build-system tests still pass.

### What did we learn along the way

Two of our early candidate builds disagreed with the reference fingerprints by a few last-decimal values, and the first suspicion was this change. A clean rebuild of the *previous, unchanged* source disagreed by exactly the same amount. The cause was a build setting: the reference fingerprints were frozen with an explicit instruction to use the full instruction set of the current CPU, and two of our new build setups had dropped that instruction. With the setting restored, every build reproduces the references exactly. The lesson is recorded: fingerprint comparisons are only meaningful when the candidate and the reference were built with identical compiler settings, and the project's build scripts no longer set the instruction-set flag by default, so every verification build must pass it explicitly.

### Technical details

```text
Commit: 876a9456780d4d59db78ffd6909a78746b1cd5a7
Parent: fd86cfbb6d27fbc214997a303058f6c3eafbb124

Changed paths (26 files, +89/−110):
src/swmod1.ftn      (+60: INTERFACE block in OCPCOMM4 for STRACE, MSGERR,
                    STPNOW, FOR, EQREAL, INKEYW, INREAL, ININTG, INCSTR,
                    KEYWIS, IGNORE - dummies verbatim from the definitions)
src/ocpmix.ftn      (defining units: restricted USE OCPCOMM4, ONLY: lists;
                    +1 LOGICAL BNEW)
src/ocpcre.ftn      (same)
24 other files      (−110: 99 legacy LOGICAL STPNOW/EQREAL/KEYWIS type-hint
                    declarations removed, incl. 8 switch-gated !WFR/!NCF/
                    !JAC/!MPI variants in swanparll.ftn/swancom1.ftn; 4
                    non-conflicting hints left in place)

Warning inventory (diagnostics build, -O3 -march=native -DNDEBUG -fcheck=all):
  implicit-interface: 3,574 → 1,368 (−2,206)
  total:             19,091 → 16,862
  machine-readable: warning_inventory_v2.json (task data dir)
Remaining clusters: fftpack51.f90 (324; xerfft 161), swanout1.f (170; swipol,
  swaninterpolateoutput), swanpre1.f (165; pvalid), swanmain.f (136; txpbla),
  swancom1.f (107; svalqi), swanpre2.f (101), ocpcre/ocpmix remainder
  (getkar, wrnkey, eqcstr, strace call sites outside the 11).

Fingerprints (PF Basin fixture):
  Release serial -O3 -march=native -DNDEBUG:   4/4 exact (260dd8d8… table)
  Release openmp-8 same flags:                 4/4 exact
  Diagnostics:                                 49/81217 last-decimal, ≤1e-4,
      bit-identical to Entry 8 diagnostics fingerprint (40d534eb…)

Build-setting caveat:
  CMake does not set -march=native; verification builds must pass
  CMAKE_Fortran_FLAGS_RELEASE='-O3 -march=native -DNDEBUG' explicitly.
  Plain -O3 shifts 171 table values (≤1e-4) even on the unchanged parent.


```


## We closed the Ocean Pack interface debt for the keyword routines

**Date:** 2026-08-21  
**Source state:** `main` at `7244c5b` (parent `876a945`)  
**Commit message:** "Add explicit interfaces for the remaining keyword-handling OCP routines"  
**Change type:** Code-quality / safety cleanup (compiler interface debt). For the normal production path the numerical result is unchanged.  
**Push status:** Nothing pushed.

### What changed?

This entry finishes the Ocean Pack part of the interface cleanup started in the previous entry. Three routines handle the model's command-file keywords - GETKAR (reads one keyword), WRNKEY (warns about an illegal keyword), and EQCSTR (case-insensitive string comparison used throughout the input readers). Like the eleven routines from the previous entry, their exact argument lists are now written down in the shared module, so the compiler checks every one of the 77 call sites. Two input-reader files still declared EQCSTR by hand as a local logical; those lines were removed because they contradicted the shared definition. One small procedure that calls these routines without importing the shared module at all now imports exactly the three routines it uses - the only call-site-level change in the commit.

### Why does it matter?

Same reasoning as the previous entry: the physics is untouched, but wrong-typed calls to the keyword routines are now build errors instead of possible silent misreads of a command file. With this commit, every Ocean Pack utility called from the main program has an explicit interface.

### Did the scientific result change?

No. Fresh serial and eight-thread builds of the committed source reproduce all four PF Basin reference fingerprints **exactly** (wave table, printed output, termination record, initialization record), and both runs terminate normally with zero warnings.

The diagnostics build again shows only its documented last-decimal difference: its wave table is bit-identical to the fingerprint recorded in Entry 8 and the previous entry (49 of 81,217 values, at most 0.0001), so this cleanup adds no new difference there.

### How much faster or slower is it?

No paired benchmark is warranted: all 77 call sites of these three routines sit in the one-time command-file reading phase (or in its error paths), never inside the time loop, so the per-step work is untouched. This matches the precedent set for one-time startup work in Entry 8.

### What did we check?

- Fresh Release serial and OpenMP-8 builds of the committed source: both ran to "Normal end of run 01", zero stderr, all four fingerprints exact.
- Fresh diagnostics build: clean run; table bit-identical to the Entry 8 diagnostics fingerprint.
- The warning count for the fixed category dropped from 1,368 to 1,291 (the 77 keyword-routine call sites); the overall build warning count dropped from 16,862 to 16,770.
- All 19 build-system tests still pass.

### What did we learn along the way

Writing the restricted imports for the three defining routines exposed a limitation of eyeballing symbol lists: the first draft of one import list omitted a variable the routine reads once near the end of its body, and the compiler reported it immediately ("symbol has no IMPLICIT type"). The restricted-import discipline therefore works as intended - it converts "probably this variable is fine" into a compile-time check. Each list was then verified by resolving every non-local identifier in the routine to the module that actually declares it.

### Technical details

```text
Commit: 7244c5b (parent 876a945)

Changed paths (4 files, +14/−5):
src/swmod1.ftn   (+10: GETKAR, WRNKEY, EQCSTR interfaces in OCPCOMM4)
src/ocpcre.ftn   (3 defining units: USE OCPCOMM4, ONLY: INPUTF, ITEST,
                PRINTF, STRACE / ONLY: STRACE / ONLY: MSGERR, STRACE -
                each list derived from the unit's resolved identifier usage)
src/swanpre1.ftn (−1: LOGICAL :: EQCSTR hint)
src/swanpre2.ftn (−1: LOGICAL EQCSTR hint; +1: SVARTP gains
                USE OCPCOMM4, ONLY: INKEYW, STRACE, WRNKEY - the only
                procedure among the callers that did not import OCPCOMM4)

Warning inventory (diagnostics build):
  implicit-interface: 1,368 → 1,291 (−77)
  total:             16,862 → 16,770
  machine-readable: warning_inventory_v3.json (task data dir)
Remaining: fftpack51 (324; xerfft 161), then SWAN-internal clusters
  (swaninterpolateoutput 52, pvalid 51, swipol 50, txpbla 48, svalqi 46,
  swanintgratspc 43, kscip1 34, swreduce 32, strace 19 - in procedures
  that do not import OCPCOMM4).

Fingerprints (PF Basin fixture, all with -O3 -march=native -DNDEBUG):
  Release serial:   4/4 exact
  Release openmp-8: 4/4 exact
  Diagnostics:      table bit-identical to Entry 8 fingerprint (40d534eb…)
```


## We checked the output-interpolation calls against the routine's real signature

**Date:** 2026-08-21  
**Source state:** `main` at `d0f9043` (parent `7244c5b`)  
**Commit message:** "Add an explicit interface for the output interpolation routine"  
**Change type:** Code-quality / safety cleanup (compiler interface debt). For the normal production path the numerical result is unchanged.  
**Push status:** Nothing pushed.

### What changed?

When SWAN writes user-requested output at specific points (test points, transects, single locations), a routine called SWANINTERPOLATEOUTPUT moves the value from the grid vertices to those points. The output writer calls it 52 times - once per requested quantity. As with the earlier entries, its exact argument list is now written down in the shared module the output writer already imports, so all 52 calls are checked by the compiler. No call was changed.

One technical note: the routine's "value on the grid" argument has a length equal to the grid's vertex count, which the program stores in a module variable. The compiler does not allow such a variable to appear in an interface body, so the interface declares that argument with an "any length" placeholder instead. The check of types, order, and array ranks at the call sites is still complete; only the exact length is left to the compiler's normal run-time array passing.

### Why does it matter?

The physics is untouched. The value is the same safety margin as before: any of the 52 calls that would have handed the interpolator a wrongly typed or mis-ordered argument is now a build error. This was the first SWAN-own routine (rather than an Ocean Pack one) to get an explicit interface in this campaign.

### Did the scientific result change?

No. Fresh serial and eight-thread builds of the committed source reproduce all four PF Basin reference fingerprints **exactly** (wave table, printed output, termination record, initialization record), and both runs terminate normally with zero warnings.

The diagnostics build's wave table is bit-identical to the fingerprint recorded in Entry 8, so this cleanup adds no new difference there.

### How much faster or slower is it?

Not benchmarked, for the same reason as Entry 10's one-time code: the 52 calls sit in the output phase, not in the repeated time-step core, and the interface changes what the compiler checks, not what the program computes.

### What did we check?

- Fresh Release serial and OpenMP-8 builds of the committed source: both ran to "Normal end of run 01", zero stderr, all four fingerprints exact.
- Fresh diagnostics build: clean run; table bit-identical to the Entry 8 diagnostics fingerprint.
- The warning count for the fixed category dropped from 1,291 to 1,239 (the 52 call sites); no new type or rank mismatch appeared at any of them.
- All 19 build-system tests still pass.

### What did we learn along the way

Two of the first attempts to write this interface failed to build, and both failures were the compiler telling us something real. The first put the grid's vertex count - a module variable - directly into the array length in the interface body, which the compiler does not allow. The second attempt placed the interface in the grid-data module itself, which created a name collision with the routine being defined (a module may not carry the interface of a routine whose name is also the name of the program unit in a file that imports it). Moving the interface to the shared output module resolved it. These are the kinds of constraints that only appear when an interface is actually written, which is exactly the point of this campaign.

### Technical details

```text
Commit: d0f9043 (parent 7244c5b)

Changed paths (1 file, +17/−1):
src/swmod1.ftn   (SWCOMM4: INTERFACE block for SWANINTERPOLATEOUTPUT;
                FOUTP(1:)*REAL(out), X,Y(1:)*REAL, FINP(*)*REAL,
                MIP INT, KVERT(1:)*INT, EXCVAL REAL - argument order
                and kinds verbatim from the definition in
                SwanInterpolateOutput.ftn90; FINP(*) because the
                exact length nverts is a module variable)

Warning inventory (diagnostics build):
  implicit-interface: 1,291 → 1,239 (−52)
  total:             16,770 → 16,664
  machine-readable: warning_inventory_v4.json (task data dir)
Remaining top: xerfft 161 (fftpack), pvalid 51, swipol 50, txpbla 48,
  svalqi 46, swanintgratspc 43, kscip1 34, swreduce 32, strace 19.

Fingerprints (PF Basin fixture, all with -O3 -march=native -DNDEBUG):
  Release serial:   4/4 exact
  Release openmp-8: 4/4 exact
  Diagnostics:      table bit-identical to Entry 8 fingerprint (40d534eb…)
```


## We checked the text-position calls against the routine's real signature

**Date:** 2026-08-21  
**Source state:** `main` at `fa02e86` (parent `d0f9043`)  
**Commit message:** "Add an explicit interface for the text position routine"  
**Change type:** Code-quality / safety cleanup (compiler interface debt). For the normal production path the numerical result is unchanged.  
**Push status:** Nothing pushed.

### What changed?

A small text routine called TXPBLA is used 48 times across nine source files to find the position of the first and the last non-blank character in a text string (leading/trailing blanks, including tabs). Its exact argument list - a text string of any length plus two integer positions - is now written down in the shared module every one of those nine files already imports, so all 48 calls are checked by the compiler. No call was changed.

Unlike the earlier clusters, TXPBLA takes no array argument, so its interface body is fully explicit and imposes no new constraints on the existing calls.

### Why does it matter?

The physics is untouched. The value is the same safety margin as the earlier entries: any of the 48 calls that would have handed the routine a wrongly typed or mis-ordered argument is now a build error. This was the first multi-file cluster of the campaign - its calls are spread across the main, output, parallel, pre-processing, and grid files rather than sitting in one routine.

### Did the scientific result change?

No. Fresh serial and eight-thread builds of the committed source reproduce all four PF Basin reference fingerprints **exactly** (wave table, printed output, termination record, initialization record), and both runs terminate normally.

A from-scratch diagnostics build of the committed source was compared line-for-line against the same build of the parent commit: the only change in the warning list is the removal of the 48 text-position warnings; no new warning of any kind appeared, and the pre-existing character-truncation warnings (25) are unchanged.

### How much faster or slower is it?

Not benchmarked: the 48 calls sit in input-parsing and output phases, not in the repeated time-step core, and the interface changes what the compiler checks, not what the program computes.

### What did we check?

- Fresh Release serial and OpenMP-8 builds of the committed source: both ran to "Normal end of run 01", zero stderr, all four fingerprints exact.
- A/B diagnostics build (parent vs committed, both from scratch): the `-Wimplicit-interface` count dropped from 1,239 to 1,191 (−48) and the total warning count from 16,718 to 16,670 (−48); character-truncation stayed at 25; no other category changed.
- All 19 build-system tests still pass.

### What did we learn along the way

Nothing new was needed here: the defining unit does not import the module that will publish its interface, so no import restriction was required - the simplest case in the campaign. The one non-obvious point is the caller spread: confirming that all nine caller *units* (not just the nine files) import the publishing module, because a file-level import is not visible to every routine in the file. All 45 caller routines import it.

### Technical details

```text
Commit: fa02e86 (parent d0f9043)

Changed paths (1 file, +5/−0):
src/swmod1.ftn   (OCPCOMM4: INTERFACE body gains SUBROUTINE TXPBLA
                with INTEGER IF, IL and CHARACTER TEXT(*), argument
                order and kinds verbatim from the definition in
                swanser.ftn)

Warning inventory (diagnostics build, A/B parent vs committed):
  implicit-interface: 1,239 → 1,191 (−48)
  total:             16,718 → 16,670 (−48)
  character-truncation: 25 → 25 (unchanged)
  machine-readable: warning_inventory_v5.json (task data dir)
Remaining top: xerfft 161 (fftpack), pvalid 51, swipol 50, svalqi 45,
  swanintgratspc 43, kscip1 34, swreduce 32, strace 19.

Fingerprints (PF Basin fixture, all with -O3 -march=native -DNDEBUG):
  Release serial:   4/4 exact
  Release openmp-8: 4/4 exact
  Diagnostics:      table bit-identical to Entry 8 fingerprint (40d534eb…)
```


## We checked the grid-lookup calls against the routine's real signature

**Date:** 2026-08-21  
**Source state:** `main` at `d57aedf` (parent `fa02e86`)  
**Commit message:** "Add an explicit interface for the grid interpolation function"  
**Change type:** Code-quality / safety cleanup (compiler interface debt). For the normal production path the numerical result is unchanged.  
**Push status:** Nothing pushed.

### What changed?

A function called SVALQI is used 45 times across four source files to read the value of an input grid - depth, wind, wave height, ambient currents - at an arbitrary point, bilinearly interpolated between the four surrounding grid vertices. Its exact argument list (two coordinates, a grid index, the grid array, a zero-masking flag, and the two grid indices of the point) is now written down in the shared module every calling routine already imports, so all 45 calls are checked by the compiler. The three legacy "this is a real function" hint declarations in the caller files conflicted with the new interface and were removed. No call was changed.

### Why does it matter?

The physics is untouched. SVALQI is the routine that turns every user-supplied input grid into values the model actually uses, so a wrongly typed or mis-ordered argument at any of the 45 calls would have silently fed the wrong grid into the physics. That class of mistake is now a build error. This was the first cluster in the campaign to remove conflicting legacy type hints, and the first to place its interface in SWCOMM3 rather than the Ocean Pack module.

### Did the scientific result change?

No. Fresh serial and eight-thread builds of the committed source reproduce all four PF Basin reference fingerprints **exactly** (wave table, printed output, termination record, initialization record), and both runs terminate normally. The diagnostics build's wave table is bit-identical to the fingerprint recorded in Entry 8.

### How much faster or slower is it?

Not benchmarked: the calls sit in input setup and the boundary routine rather than in the repeated time-step core, and the interface changes what the compiler checks, not what the program computes.

### What did we check?

- Fresh Release serial and OpenMP-8 builds of the committed source: both ran to "Normal end of run 01", zero stderr, all four fingerprints exact.
- The `-Wimplicit-interface` count dropped from 1,191 to 1,145 (−46) and the total diagnostics warning count from 16,670 to 16,624 (−46); character-truncation stayed at 25; no new warning of any kind appeared.
- All 19 build-system tests still pass.

### What did we learn along the way

The hint declarations were not all in the same place, and not all in the same style: one was in the fixed-form main file, and two were in the free-form QCM file in the `real :: name` form, which the earlier fixed-form searches did not catch. The compiler found them for us - the first build of the cluster failed with "symbol conflicts with symbol from module", naming each one. Searching for the callee name across all declaration forms is the reliable way to enumerate them; pattern-matching on one file style is not.

### Technical details

```text
Commit: d57aedf (parent fa02e86)

Changed paths (3 files, +13/−3):
src/swmod1.ftn   (SWCOMM3: INTERFACE body gains REAL FUNCTION SVALQI with
                INTEGER IGRID, IXC, IYC, ZERO; REAL ARRINP(*), XP, YP -
                argument order and kinds verbatim from the definition in
                swanmain.ftn; interface placed in SWCOMM3 because the
                defining unit itself imports SWCOMM2, which would
                self-collide, while all seven caller routines import
                SWCOMM3)
src/swanmain.ftn (removed 1 conflicting fixed-form REAL SVALQI hint)
src/SwanQCM.ftn90 (removed 2 conflicting free-form real :: SVALQI hints)

Warning inventory (diagnostics build):
  implicit-interface: 1,191 → 1,145 (−46)
  total:             16,670 → 16,624 (−46)
  character-truncation: 25 → 25 (unchanged)
  machine-readable: warning_inventory_v6.json (task data dir)
Remaining top: xerfft 161 (fftpack), pvalid 51, swipol 50, swanintgratspc 43,
  kscip1 34, swreduce 32, strace 19.

Fingerprints (PF Basin fixture, all with -O3 -march=native -DNDEBUG):
  Release serial:   4/4 exact
  Release openmp-8: 4/4 exact
  Diagnostics:      table bit-identical to Entry 8 fingerprint (40d534eb…)
```



## LEESEL + READXY explicit interfaces (Cluster 10, the last clean pure-interface tail)

### What changed, in plain terms
Two remaining wave-model helper routines now have explicit interfaces, so the compiler can
type-check their calls instead of guessing:

- **LEESL** (line-selection helper in the Ocean Pack reader, no arguments) - 10 warnings removed.
  Its interface is trivial (no parameters) and lives in a new small module `OCPREAD2` at the top
  of `ocpcre.ftn`, imported by the six reader subroutines that call it.
- **READXY** (reads x/y coordinate values in the initialisation/pre-processing) - 16 warnings
  removed. Its interface goes into `SWCOMM4` (already imported by every one of its five calling
  subroutines). The coordinates are single REAL values and the name strings are assumed-length,
  so the interface is a faithful, single-shape description of every call site.

### Why it is scientifically safe
No definition was touched. The two interfaces describe arguments that are *already* uniform at
every call site (verified by hand: READXY's coordinate actuals XP/YP/XPG/YPG/XPC/YPC/XPN/YPN/
XPCN/YPCN/XPFR/YPFR/XQ/YQ/XP1/YP1/XQ1/YQ1 are all `REAL`, and its literals are `0.`/`-1.E10`
REAL; LEESEL takes no arguments). Because the definition dummies already match these shapes and
types exactly, the interfaces change nothing at run time - they only let the compiler check the
calls. The serial and OpenMP runs reproduce the reference output bit-for-bit.

### What we deliberately did NOT do
A compiler-level audit of the other small "remaining" reader routines (SWCOPR, INCTIM, DTRETI,
INDBLE) found that most have **latent argument mismatches** hidden by the implicit interface -
e.g. `XCGRID(MXC,MYC)` (rank 2) passed to a rank-1 dummy, `NPLAF`/`MUDLF` (INTEGER) passed to a
REAL dummy, and several `REAL`→`REAL*8` kind mismatches. Adding an interface to those would not
cleanly remove the warning but would *surface* a real type/rank bug (a definition-level fix, with
numerical risk). That work is correctly deferred to the Fortran 2018 definition-modernization
task, not this interface-debt task. So the clean pure-interface tail is genuinely exhausted at
LEESL + READXY.

### Measured outcome
- Diagnostics build: clean (0 errors). Missing-interface warnings **1,145 → 1,119 (−26, exact)**;
  total diagnostics warnings 16,624 → 16,607 (−17, the 26 interface warnings minus 9 that were
  already absorbed). No new argument-mismatch warnings.
- Correctness: serial (core 4) and OpenMP-8 (cores 0–7) Release runs match the oracle fingerprints
  exactly - `full_domain_table.dat` = 260dd8d8…211c, normalized `PRINT` = 75d4392b…ee93.
- All 19 tests pass.

### Remaining Task 8 surface (now precisely bounded)
The only things between the current build and a clean build **without**
`-fallow-argument-mismatch` are 64 pre-existing hard errors (confirmed identical at the untouched
baseline), in two "two-types-under-one-name" classes that need definition modernization (Task 9):
- 50 in vendored FFTPACK 5.1 (real/complex storage dispatch), and
- 14 in the 5 parallel-dispatch routines (integer-pointer address dispatch; the fix reaches the
  MPI path, which this serial campaign cannot verify).
The remaining 1,119 missing-interface warnings are dominated by xerfft/xercon (fftpack) and the
runtime-2-D / runtime-type-dispatch routines already scoped to Task 9.

## SWSYNC + NWLINE + GAMMAF explicit interfaces (the last clean pure-interface tail)

### What changed, in plain terms
Three final single-shape routine families among the pure-interface debt now have explicit
interfaces:

- **SWSYNC** (the no-argument parallel barrier - a synchronization point, no data moved) - 6
  warnings. Interface added to `OCPCOMM2`, which both of its two calling subroutines already import.
- **NWLINE** (the no-argument "advance to the next input line" helper in the Ocean Pack reader) -
  6 warnings. Interface into `SWCOMM3`, imported by both callers.
- **GAMMAF** (the regularized gamma function, one REAL argument - used in the dispersion/dissipation
  parameterisation) - 8 warnings. Interface into `SWCOMM3`, imported by all three callers. Two
  now-redundant `REAL GAMMAF` type hints (in the two caller files) would have *collided* with the
  exported module symbol, so they were removed - the same fix pattern used for the OCP clusters.

### Why it is scientifically safe
No definition or call site was touched. SWSYNC and NWLINE take no arguments; GAMMAF's single
argument is a scalar REAL at every one of its call sites (the `REAL GAMMAF` hints were only implicit
type declarations, so removing them changes nothing - the interface now provides the type). Because
the interface dummies match the definitions exactly, run-time behaviour is unchanged and the serial
and OpenMP runs reproduce the reference output bit-for-bit.

### Measured outcome
- Diagnostics build: clean (0 errors). Missing-interface warnings **1,119 → 1,099 (−20, exact)**;
  total diagnostics warnings 16,607 → 16,585. No new argument-mismatch warnings.
- Correctness: serial (core 4) and OpenMP-8 (cores 0–7) Release runs match the oracle -
  `full_domain_table.dat` = 260dd8d8…211c, normalized `PRINT` identical to the prior verified run
  (only the execution-timestamp line differs). Repo CTest suite passes.

### The pure-interface lane is now exhausted - and precisely why
A full sweep of every remaining mid-size callee confirmed the clean lane is finished. The rest is
not "clean interface debt"; it is one of:
- **Latent argument mismatches** that the implicit interface is currently hiding - e.g. TCOEF
  (INTEGER spectral-index locals passed to REAL dummies), INITVD (REAL passed to a REAL*8 dummy),
  SBLKPT (a scalar element passed to a 1-D array dummy). Adding interfaces would *surface* real
  type/rank bugs, which is definition-level work with numerical risk → Task 9.
- **Repo-wide, not "bounded clusters"** - STRACE (19 warnings but 302 call sites in 268 different
  subroutines sharing no common module) and MSGERR (8, in 123 subroutines) would each need a `USE`
  added across the entire codebase, which violates the "bounded routine cluster" method.
- **External Ocean Pack routines** with no in-tree definition (NUMSTR, DEGCNV, SWRMAT, FUNC) - an
  interface can't be added to a body that isn't in this repository.

### Task 8 status
Warnings: 3,574 → 1,099 (−69%). The only things between the current build and a clean build
**without** `-fallow-argument-mismatch` are the 64 pre-existing hard errors (confirmed identical at
the untouched baseline) - 50 in vendored FFTPACK 5.1 (real/complex dispatch) and 14 in the 5
parallel-dispatch routines (integer-pointer address dispatch, whose fix reaches the MPI path that
this serial campaign cannot verify). Both need definition modernization (Task 9), not interface
debt. The remaining 1,099 missing-interface warnings are dominated by xerfft/xercon (fftpack) and
the runtime-2-D / runtime-type-dispatch routines already scoped to Task 9.

## Task 8 source modernization: parallel and FFTPACK interfaces

- **Source commit:** `f8f2e65` (based on `84ce3ca`)
- Added explicit `M_PARALL` interfaces for `SWSENDNB`, `SWRECVNB`, `SWBROADC`, `SWGATHER`, and `SWREDUCE`, including `MPI_IN_PLACE` handling and restricted imports.
- Modernized FFTPACK dispatch storage to `REAL(8)` with standards-conforming public `TRANSFER` wrappers; optimized `CFFT2` to one staging allocation with explicit pack/unpack. Also separated scalar/array-element `KSCIP` forms; the final scalar `KSCIP` adapters enforce an internal extent of 1, and `SWOMPU` is typed explicitly.
- Strict serial, OpenMP, MPI, and MPI-JAC builds completed with **0 errors** and without `-fallow-argument-mismatch`. Full diagnostics remained at 0 errors; implicit-interface warnings fell from **1,090 to 1,041**.
- Serial/OpenMP CTest passed **2/2**. FFT differential and round-trip output was byte-identical to the `84ce3ca` baseline; verified serial/OpenMP release tables were identical, and MPI outputs matched the prior verified candidate.
- Final `CFFT2` microbenchmark regression was **2.24%** with equal checksums, reduced from the initial **82.02%** wrapper regression. Diff, security, and fixed-form column checks were clean.
- **Known pre-existing caveat:** legacy FFTPACK multidimensional kernels still fail `-fcheck=all` bounds checking because flattened indexing exceeds declared dimensions; production optimized differential output remains exact.

## Task 8 gate closure: compatibility flag removed

- Final commit: `a7b8f0179fe9e192867843dcad0177665e4a6e9d` (parent `f8f2e655f6f4c57d518cc78390117082f2a15f65`; tree `40034ed7a52755b7889dc1d8779c9e7071c95283`).
- Both GNU branches no longer add `-fallow-argument-mismatch`.
- Fresh strict serial, OpenMP, MPI, and MPI+JAC builds passed; searches of the source and generated `build.ninja` files found zero instances of the flag.
- CTest passed 2/2 for serial and 2/2 for OpenMP.
- Serial and OpenMP tables exactly matched the oracle SHA-256 `260dd8d888e43eb68b374a21f3e97097c9b554610d9a2eb5fd0204654073211c`; MPI output also matched exactly.
- Task 8 gate is closed.

## Task 9 boundary spectrum interface modernization

- **Commit:** `d7d20b8024d3f213fad6b73b2b4357e0d32d6283` (parent `a7b8f0179fe9e192867843dcad0177665e4a6e9d`, tree `a087addc00bcdc64ef20b0b7a9da283e0140e372`) - `Modernize boundary spectrum interfaces`.
- **Interface modernization:** `BSPLOC`, `BSPDIR`, and `BSPFRQ` now have contiguous pointer contracts; `M_BNDSPEC` publishes an explicit `RBFILE` interface; dummies use accurate `INTENT` and assumed-shape declarations, and `BSPECS` planes are passed as rank-2 sections.
- **Diagnostics and strict compile:** array-temporary warnings fell from 46 to 43 and `RBFILE` implicit-interface warnings from 1 to 0; strict F2018 pedantic compilation of `M_BNDSPEC` passed.
- **Build matrix:** serial debug/release, OpenMP, MPI, and JAC builds passed.
- **Exactness:** PF serial/OpenMP matched the exact oracle; `f31har02` debug/release outputs were exact.
- **Vectorization and timing:** the report was unchanged at 17 vectorized/262 missed. Paired `f31har02` medians were 6.912819 s baseline versus 6.915323 s candidate (+0.036%): neutral, with no speedup claimed.
- **Independent review:** PASS.

## Task 9 recursive cleanup data-flow contracts

- **Commit:** `48cd67d97acc5b47a1f7def5f7bd555dd7a39019` (parent `d7d20b8024d3f213fad6b73b2b4357e0d32d6283`, tree `7f78ae830f2058aee2a4839a09768618088daec1`) - `Declare recursive cleanup data flow`.
- **Contracts:** the derived-type dummies of `DELETEOPS`, `DELETEORQ`, `DELETEBSPC`, `DELETEBS`, and `DELETEBGP` are declared `INTENT(INOUT)`. This is exact because each routine both reads existing state and mutates pointer association through recursive cleanup, `DEALLOCATE`, and `NULLIFY`; `IN` would forbid the mutation and `OUT` would incorrectly discard incoming definedness/state.
- **Build validation:** all five configurations passed: debug serial, release serial, release OpenMP, release MPI, and diagnostics MPI/JAC.
- **Runtime validation:** PF basin serial and OpenMP were exact; f31har02 debug and release tracked outputs were exact against the accepted base, with empty stderr.
- **Standards check:** the strict current `M_BNDSPEC` focused F2018 compile passed; whole `OUTP_DATA` remains blocked later by the unrelated pre-existing `REAL*8` `OQR` declaration.
- **Vectorization:** exactly unchanged at 936 vectorized / 29,265 missed.
- **Timing:** paired f31har02 medians changed from 6.939724559 s to 6.950196480 s (`+0.151%`), neutral within run noise; no speedup is claimed.
- **Independent review:** exact postimage review passed; the candidate is a safe, bounded, annotation-only cluster.

## Task 9 output coordinate interface modernization

- **Postimage:** commit `863db56941372da5fac8c923ac0a70e0157e5d1f` (`Modernize output coordinate interfaces`), parent `48cd67d97acc5b47a1f7def5f7bd555dd7a39019`, tree `3b652aa2115b87a2cdf0e9109167b025d8490532`.
- **Contracts:** `OPSDAT` `XP`/`YP` are `CONTIGUOUS` pointers. `OUTP_DATA` publishes an explicit `SWOEXC` interface, and `SWOEXC` now uses accurate `INTENT` plus assumed-shape/`CONTIGUOUS` input coordinate and grid arrays while preserving sequence associations for output arrays.
- **Diagnostics:** array temporaries fell from 43 to 39: two direct removals in `swanout1` plus two collateral removals in MPI `swanparll`; no new errors.
- **Build/test matrix:** Debug serial, Release serial, Release OpenMP, Release MPI, and diagnostics MPI/JAC all passed; Debug and Release CTest each passed 2/2. The focused strict F2018 interface probe passed.
- **Runtime correctness:** PF basin serial and OpenMP matched the exact oracle (identical table SHA-256 `260dd8d888e43eb68b374a21f3e97097c9b554610d9a2eb5fd0204654073211c`). `f31har02` Debug and Release were exact against the accepted base, with empty stderr.
- **Compiler/performance evidence:** successful vectorizations remained 936, while missed remarks decreased from 29,265 to 29,259. Paired `f31har02` timing changed by -0.045% (6.927292 s to 6.924166 s median), neutral within run noise; no speedup is claimed.
- **Review:** exact postimage review was completed read-only; no issue surfaced.

## MPI output coordinates repaired after review

### What changed

The review documented the SWOEXC interface commit before its delayed exact review had completed. The review then found a concrete late blocker: for MPI unstructured `COMPGRID` output, `MIP=nvertsg` but `CUOPS` was receiving local `XP`/`YP` arrays with extent `nverts`. Commit `67022dd373576853056d6f02d761333a3c6c30bf` (parent `863db56`) repairs that blocker.

In `src/swanparll.ftn`, only the `PSTYPE='U'` plus `LCOMPGRD` branch now passes the retained global `xcugrdgl`/`ycugrdgl` coordinates with extent `nvertsg`, together with valid 1x1 placeholders for the unused structured-grid arguments. All other point-set paths are unchanged.

### Why it is scientifically safe

The repair aligns the coordinate-array extent with the already-global point count used by MPI output collection. It changes neither computed field values nor unrelated output paths; it supplies `CUOPS` with the global unstructured coordinates required by the existing `MIP=nvertsg` contract.

An independent exact fix review passed for patch `fcb0453a` and tree `c1fb57b6`.

### Measured outcome

- Five builds passed, including the MPI compile.
- The production `SWOEXC` `-fcheck=all` probe passed.
- Python checks passed 19/19; CTest Debug and Release passed 2/2.
- The PF serial/OpenMP oracle remained exact, and the f31 result remained exact.
- Temporary warnings stayed 39 → 39; vectorized-loop count stayed 936 → 936.
- MPI runtime execution was unavailable, so no MPI runtime claim is made.


## Final OQR REAL64 modernization

- **Commit:** `188d1c0e3ba42738f0cab84b51b860343734f5b5` (parent `67022dd`), `Use standard real kind for output timing`.
- **Bounded change:** In `src/swmod2.ftn`, `ISO_FORTRAN_ENV` now imports `REAL64` privately, and `ORQDAT` changes `OQR(2)` from `REAL*8` to `REAL(REAL64)`.
- **Compatibility:** GNU compilation preserves the exact same kind, storage, and ABI for `OQR`.
- **Independent exact-patch review:** **PASS** for patch `ffcaffcf`; final tree `8e040274`.
- **Build and test evidence:** All five configurations pass, including MPI compilation. The whole generated `swmod2` passes strict Fortran 2018 pedantic compilation. Python tests are **19/19**, and CTest is **2/2** in both Debug and Release.
- **Oracle evidence:** PF serial/OpenMP oracle output is exact; `f31` Debug/Release output is exact.
- **Diagnostics and vectorization:** Full diagnostics remain **39 → 39**. Vectorized reports remain **936 → 936**, and missed-vectorization reports remain **29266 → 29266**.
- **Performance:** A fresh balanced 4+4 `f31` timing comparison is **+0.0645%**, classified as neutral.
- **Unavailable runtime coverage:** NetCDF and MPI runtime validation remain unavailable in this environment; MPI compile coverage passed.

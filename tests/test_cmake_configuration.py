#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
MPI_FORTRAN_AVAILABLE = any(
    shutil.which(name) for name in ("mpifort", "mpif90", "mpiifort", "mpiifx")
)


def available_single_config_generator() -> str | None:
    capabilities = json.loads(
        subprocess.run(
            ["cmake", "-E", "capabilities"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    )
    generators = {
        generator["name"]: generator
        for generator in capabilities["generators"]
        if not generator.get("multiConfig", False)
    }
    if "Ninja" in generators and shutil.which("ninja"):
        return "Ninja"
    if "Unix Makefiles" in generators and shutil.which("make"):
        return "Unix Makefiles"
    return None


def copy_repository(destination: Path) -> Path:
    source = destination / "source [with] spaces-and-dash"

    def ignore(directory: str, names: list[str]) -> set[str]:
        path = Path(directory)
        ignored = {".git"} if path == REPOSITORY else set()
        try:
            relative = path.relative_to(REPOSITORY)
        except ValueError:
            return ignored
        if relative == Path("src") or relative == Path("src/hcat"):
            ignored.update(
                name
                for name in names
                if Path(name).suffix.lower() in {".f", ".f90", ".for"}
            )
        return ignored

    shutil.copytree(REPOSITORY, source, ignore=ignore)
    return source


class CMakeConfigurationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="swan-cmake-test-")
        root = Path(self.temporary.name)
        self.source = copy_repository(root)
        self.build = root / "build [with] spaces-and-dash"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def configure(self, *arguments: str) -> None:
        subprocess.run(
            [
                "cmake",
                "-S",
                str(self.source),
                "-B",
                str(self.build),
                *arguments,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_fresh_single_config_build_defaults_to_release(self) -> None:
        generator = available_single_config_generator()
        if generator is None:
            self.skipTest("No usable single-configuration CMake generator")
        self.configure("-G", generator)
        cache = (self.build / "CMakeCache.txt").read_text(encoding="utf-8")
        self.assertRegex(cache, r"(?m)^CMAKE_BUILD_TYPE:STRING=Release$")

    def test_install_preserves_runtime_and_support_files(self) -> None:
        self.configure("-DCMAKE_BUILD_TYPE=Release", "-DBUILD_TESTING=OFF")
        subprocess.run(
            ["cmake", "--build", str(self.build)],
            check=True,
            capture_output=True,
            text=True,
            timeout=180,
        )
        install_prefix = Path(self.temporary.name) / "install [with] spaces"
        subprocess.run(
            ["cmake", "--install", str(self.build), "--prefix", str(install_prefix)],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertTrue((install_prefix / "bin" / "swan.exe").is_file())
        self.assertTrue(list((install_prefix / "lib").glob("*swan41.51*")))
        launcher = "swanrun.bat" if os.name == "nt" else "swanrun"
        self.assertTrue((install_prefix / "bin" / launcher).is_file())
        self.assertTrue((install_prefix / "misc" / "hcat.nml").is_file())
        self.assertTrue((install_prefix / "tools" / "cvspec1d.for").is_file())

    def test_target_options_do_not_force_optimization_or_toolchain_policy(self) -> None:
        options = (self.source / "cmake" / "SwanCompilerOptions.cmake").read_text(
            encoding="utf-8"
        )
        forbidden_options = (
            "-O1",
            "-O2",
            "-O3",
            "-fast",
            "-staticlink",
            "-qarch",
            "-qtune",
            "-qcache",
        )
        for forbidden in forbidden_options:
            with self.subTest(option=forbidden):
                self.assertNotIn(forbidden, options)

    def test_preserves_caller_build_type_and_fortran_flags(self) -> None:
        self.configure(
            "-DCMAKE_BUILD_TYPE=Debug",
            "-DCMAKE_Fortran_FLAGS=",
        )
        cache = (self.build / "CMakeCache.txt").read_text()
        self.assertIn("CMAKE_BUILD_TYPE:STRING=Debug\n", cache)
        self.assertIn("CMAKE_Fortran_FLAGS:STRING=\n", cache)

    def test_generates_switched_sources_only_in_build_tree(self) -> None:
        self.configure("-DCMAKE_BUILD_TYPE=Release")
        source_outputs = list((self.source / "src").glob("*.f"))
        source_outputs.extend((self.source / "src").glob("*.f90"))
        source_outputs.extend((self.source / "src").glob("*.for"))
        self.assertEqual(source_outputs, [])

        subprocess.run(
            [
                "cmake",
                "--build",
                str(self.build),
                "--target",
                "swan-generated-sources",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        generated = self.build / "generated"
        fixed_extension = ".for" if os.name == "nt" else ".f"
        generated_swancom1 = generated / f"swancom1{fixed_extension}"
        self.assertTrue(generated_swancom1.is_file())
        self.assertTrue((generated / "SwanGriddata.f90").is_file())
        self.assertTrue((generated / f"swanmain{fixed_extension}").is_file())
        template_count = len(list((self.source / "src").glob("*.ftn")))
        template_count += len(list((self.source / "src").glob("*.ftn90")))
        generated_outputs = list(generated.glob(f"*{fixed_extension}"))
        generated_outputs.extend(generated.glob("*.f90"))
        self.assertGreater(len(generated_outputs), 0)
        self.assertLessEqual(len(generated_outputs), template_count)

        previous_mtime = generated_swancom1.stat().st_mtime_ns
        (self.source / "src" / "swancom1.ftn").touch()
        subprocess.run(
            [
                "cmake",
                "--build",
                str(self.build),
                "--target",
                "swan-generated-sources",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertGreater(generated_swancom1.stat().st_mtime_ns, previous_mtime)

    def test_ffro_uses_the_supported_fixfront_switch(self) -> None:
        self.configure("-DFFRO=ON", "-DCMAKE_BUILD_TYPE=Release")
        subprocess.run(
            [
                "cmake",
                "--build",
                str(self.build),
                "--target",
                "swan-generated-sources",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        generated = (
            self.build / "generated" / "SwanCompdata.f90"
        ).read_text(encoding="utf-8")
        self.assertIn("integer                                    :: nfront", generated)
        self.assertNotIn("!FXFRO    integer", generated)

    @unittest.skipUnless(MPI_FORTRAN_AVAILABLE, "MPI Fortran compiler unavailable")
    def test_jac_enables_mpi_and_generates_hcat_in_build_tree(self) -> None:
        self.configure("-DJAC=ON", "-DCMAKE_BUILD_TYPE=Release")

        subprocess.run(
            [
                "cmake",
                "--build",
                str(self.build),
                "--target",
                "swan-hcat-generated-source",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertTrue(
            (
                self.build
                / "generated"
                / "hcat"
                / f"swanhcat{'.for' if os.name == 'nt' else '.f'}"
            ).is_file()
        )
        self.assertFalse(
            (
                self.source
                / "src"
                / "hcat"
                / f"swanhcat{'.for' if os.name == 'nt' else '.f'}"
            ).exists()
        )

    @unittest.skipUnless(MPI_FORTRAN_AVAILABLE, "MPI Fortran compiler unavailable")
    def test_disabling_jac_does_not_leave_mpi_cached_on(self) -> None:
        self.configure("-DJAC=ON", "-DCMAKE_BUILD_TYPE=Release")
        self.configure("-DJAC=OFF", "-DCMAKE_BUILD_TYPE=Release")

        cache = (self.build / "CMakeCache.txt").read_text(encoding="utf-8")
        self.assertRegex(cache, r"(?m)^JAC:BOOL=OFF$")
        self.assertRegex(cache, r"(?m)^MPI:BOOL=OFF$")

    def test_rejects_openmp_with_mpi(self) -> None:
        with self.assertRaises(subprocess.CalledProcessError) as context:
            self.configure("-DOPENMP=ON", "-DMPI=ON")
        self.assertIn(
            "OPENMP cannot be combined with MPI or JAC",
            context.exception.stderr + context.exception.stdout,
        )

    def _collect_flag_text(self) -> str:
        """Read every compiler-flag record CMake generated for this build.

        Ninja records flags in build.ninja files; Makefiles records them in
        flags.make files. Both are written at configure time.
        """
        text_parts = []
        for ninja_file in self.build.rglob("*.ninja"):
            text_parts.append(ninja_file.read_text(encoding="utf-8", errors="replace"))
        for flags_file in self.build.rglob("flags.make"):
            text_parts.append(flags_file.read_text(encoding="utf-8", errors="replace"))
        return "\n".join(text_parts)

    def test_diagnostics_option_is_off_by_default(self) -> None:
        generator = available_single_config_generator()
        if generator is None:
            self.skipTest("No usable single-configuration CMake generator")
        self.configure("-G", generator, "-DCMAKE_BUILD_TYPE=Release")
        cache = (self.build / "CMakeCache.txt").read_text(encoding="utf-8")
        self.assertRegex(cache, r"(?m)^SWAN_DIAGNOSTICS:BOOL=OFF$")

    def test_default_build_keeps_suppressed_warnings_and_has_no_diagnostics(self) -> None:
        generator = available_single_config_generator()
        if generator is None:
            self.skipTest("No usable single-configuration CMake generator")
        self.configure("-G", generator, "-DCMAKE_BUILD_TYPE=Release")
        flags = self._collect_flag_text()
        self.assertIn("-w", flags)
        for diagnostic_flag in (
            "-Wall",
            "-Wextra",
            "-Wimplicit-interface",
            "-Wimplicit-procedure",
            "-Wsurprising",
            "-Wconversion-extra",
            "-Warray-temporaries",
            "-fcheck=all",
            "-fbacktrace",
        ):
            with self.subTest(flag=diagnostic_flag):
                self.assertNotIn(diagnostic_flag, flags)

    def test_diagnostics_flags_are_opt_in(self) -> None:
        generator = available_single_config_generator()
        if generator is None:
            self.skipTest("No usable single-configuration CMake generator")
        self.configure(
            "-G", generator, "-DCMAKE_BUILD_TYPE=Release", "-DSWAN_DIAGNOSTICS=ON"
        )
        cache = (self.build / "CMakeCache.txt").read_text(encoding="utf-8")
        self.assertRegex(cache, r"(?m)^SWAN_DIAGNOSTICS:BOOL=ON$")
        flags = self._collect_flag_text()
        for diagnostic_flag in (
            "-Wall",
            "-Wextra",
            "-Wimplicit-interface",
            "-Wimplicit-procedure",
            "-Wsurprising",
            "-Wconversion-extra",
            "-Warray-temporaries",
            "-fcheck=all",
            "-fbacktrace",
        ):
            with self.subTest(flag=diagnostic_flag):
                self.assertIn(diagnostic_flag, flags)


if __name__ == "__main__":
    unittest.main()

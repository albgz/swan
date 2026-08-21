#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
SWITCH = REPOSITORY / "switch.pl"
MARKERS = [
    "plain",
    "!!ESMF esmf-disabled",
    "!ESMF esmf-enabled",
    "!TIMG timing",
    "!JAC jacobi",
    "!WFR wavefront",
    "!FXFRO fixed-front",
    "!GRAPH graph",
    "!MPI mpi",
    "!F95 fortran-95",
    "!DOS dos",
    "!UNIX unix",
    "!/Cray cray",
    "!/SGI sgi",
    "!/impi intel-mpi",
    "!CVIS cvis",
    "!ADC adc",
    "!NADC no-adc",
    "!COH coherent",
    "!NCOH no-coherent",
    "!METIS metis",
    "!NCF netcdf",
    "!NNCF no-netcdf",
    "!MatL4 matlab-4",
    "!MatL5 matlab-5",
]


class SwitchTests(unittest.TestCase):
    def run_switch(self, *options: str) -> tuple[Path, Path]:
        self.temporary = tempfile.TemporaryDirectory(
            prefix="switch.ftn-path-with-dash-"
        )
        directory = Path(self.temporary.name)
        fixed = directory / "sample.ftn"
        free = directory / "modern.ftn90"
        contents = "\n".join(MARKERS) + "\n"
        fixed.write_text(contents)
        free.write_text(contents)
        subprocess.run(
            [
                "perl",
                str(SWITCH),
                *options,
                str(directory / "*.ftn"),
                str(directory / "*.ftn90"),
            ],
            check=True,
            timeout=10,
        )
        return directory / ("sample.f" if "-unix" in options else "sample.for"), directory / "modern.f90"

    def tearDown(self) -> None:
        temporary = getattr(self, "temporary", None)
        if temporary is not None:
            temporary.cleanup()

    def test_unix_defaults_expand_globs_and_handle_dashed_paths(self) -> None:
        fixed, free = self.run_switch("-unix")
        expected = [
            "plain",
            " esmf-disabled",
            "!ESMF esmf-enabled",
            "!TIMG timing",
            "!JAC jacobi",
            " wavefront",
            "!FXFRO fixed-front",
            " graph",
            "!MPI mpi",
            "!F95 fortran-95",
            "!DOS dos",
            " unix",
            "!/Cray cray",
            "!/SGI sgi",
            "!/impi intel-mpi",
            "!CVIS cvis",
            "!ADC adc",
            " no-adc",
            "!COH coherent",
            " no-coherent",
            "!METIS metis",
            "!NCF netcdf",
            " no-netcdf",
            "!MatL4 matlab-4",
            " matlab-5",
        ]
        expected_text = "\n".join(expected) + "\n"
        self.assertEqual(fixed.read_text(), expected_text)
        self.assertEqual(free.read_text(), expected_text)

    def test_exact_source_path_preserves_glob_metacharacters(self) -> None:
        with tempfile.TemporaryDirectory(prefix="switch-exact-path-") as temporary:
            directory = Path(temporary) / "source [one] with space"
            directory.mkdir()
            source = directory / "sample.ftn"
            source.write_text("!UNIX exact-path\n")
            subprocess.run(
                ["perl", str(SWITCH), "-unix", str(source)],
                check=True,
                timeout=10,
            )
            self.assertEqual((directory / "sample.f").read_text(), " exact-path\n")

    def test_all_positive_switches(self) -> None:
        fixed, free = self.run_switch(
            "-esmf",
            "-timg",
            "-jac",
            "-fixfront",
            "-mpi",
            "-f95",
            "-dos",
            "-unix",
            "-cray",
            "-sgi",
            "-impi",
            "-cvis",
            "-coh",
            "-netcdf",
            "-matl4",
        )
        expected = [
            "plain",
            "!!ESMF esmf-disabled",
            " esmf-enabled",
            " timing",
            " jacobi",
            "!WFR wavefront",
            " fixed-front",
            "!GRAPH graph",
            " mpi",
            " fortran-95",
            " dos",
            " unix",
            " cray",
            " sgi",
            " intel-mpi",
            " cvis",
            "!ADC adc",
            " no-adc",
            " coherent",
            "!NCOH no-coherent",
            "!METIS metis",
            " netcdf",
            "!NNCF no-netcdf",
            " matlab-4",
            "!MatL5 matlab-5",
        ]
        expected_text = "\n".join(expected) + "\n"
        self.assertEqual(fixed.read_text(), expected_text)
        self.assertEqual(free.read_text(), expected_text)

    def test_adcirc_switch(self) -> None:
        fixed, _ = self.run_switch("-unix", "-adcirc")
        text = fixed.read_text()
        self.assertIn(" adc\n", text)
        self.assertIn("!NADC no-adc\n", text)

    def test_metis_switch(self) -> None:
        fixed, _ = self.run_switch("-unix", "-metis")
        self.assertIn(" metis\n", fixed.read_text())

    def test_unknown_option_fails_fast(self) -> None:
        process = subprocess.run(
            ["perl", str(SWITCH), "-unknown"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("unsupported option -unknown", process.stderr)

    def test_unsupported_esmf_combinations_fail(self) -> None:
        for option in ("-adcirc", "-metis"):
            with self.subTest(option=option):
                process = subprocess.run(
                    ["perl", str(SWITCH), "-esmf", option],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                self.assertNotEqual(process.returncode, 0)
                self.assertIn("is not supported", process.stderr)


if __name__ == "__main__":
    unittest.main()

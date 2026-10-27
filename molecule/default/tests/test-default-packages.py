"""Test the package-update helper without downloading or installing packages."""

import configparser
import io
from pathlib import Path
import runpy
import stat
import subprocess
import sys
import unittest
from unittest.mock import patch

HELPER = Path(__file__).resolve().parents[3] / "files" / "unattended-upgrades-default-packages"
MAIN = runpy.run_path(str(HELPER))["main"]


class DefaultPackagesTests(unittest.TestCase):
    def execute(
        self, packages=("google-chrome-stable", "firefox"), mode="security",
        apply=True, download=True, installed="google-chrome-stable\nfirefox\n",
        overrides="", fail=None, base_config_file="/etc/dnf/dnf.conf",
        base_configuration="[main]\ngpgcheck=True\nkeepcache=True\n", installroot="/",
    ):
        automatic = (
            "[commands]\nupgrade_type=" + mode
            + "\napply_updates=" + str(apply)
            + "\ndownload_updates=" + str(download)
            + "\nbase_config_file=" + base_config_file
            + "\n[base]\n" + overrides
        )
        calls = []
        configurations = []
        paths = []

        def read_configuration(path, **kwargs):
            if path == "/etc/dnf/automatic.conf":
                return io.StringIO(automatic)
            if path == base_config_file:
                if isinstance(base_configuration, Exception):
                    raise base_configuration
                return io.StringIO(base_configuration)
            raise AssertionError("unexpected configuration path: " + str(path))

        def run(command, **kwargs):
            calls.append(command)
            self.assertTrue(kwargs["check"])
            if command[0] == "/usr/bin/rpm":
                if fail == command[0]:
                    raise subprocess.CalledProcessError(1, command)
                self.assertEqual(command, [
                    "/usr/bin/rpm", "--root", installroot, "-qa", "--queryformat", "%{NAME}\\n",
                ])
                return subprocess.CompletedProcess(command, 0, installed)
            self.assertEqual(command[0], "/usr/bin/dnf")
            path = Path(command[command.index("--config") + 1])
            paths.append(path)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            configuration = configparser.ConfigParser(interpolation=None)
            configuration.read_string(path.read_text())
            configurations.append(configuration)
            if fail == command[0]:
                raise subprocess.CalledProcessError(1, command)
            return subprocess.CompletedProcess(command, 0)

        with patch.object(sys, "argv", [str(HELPER), *packages]), \
                patch("builtins.open", side_effect=read_configuration), \
                patch("subprocess.run", side_effect=run), \
                patch("sys.stdout", new_callable=io.StringIO) as output:
            try:
                MAIN()
                diagnostics = output.getvalue()
            finally:
                for path in paths:
                    self.assertFalse(path.exists(), "temporary configuration was not removed")
        return calls, configurations, diagnostics

    def test_installed_packages_receive_default_updates(self):
        calls, configurations, _ = self.execute()
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1][-4:], ["upgrade", "--", "google-chrome-stable", "firefox"])
        self.assertNotIn("--security", calls[1])
        self.assertNotIn("--downloadonly", calls[1])
        self.assertNotIn("includepkgs", configurations[0]["main"])
        self.assertTrue(configurations[0].getboolean("main", "gpgcheck"))

    def test_download_only(self):
        calls, _, _ = self.execute(apply=False)
        self.assertIn("--downloadonly", calls[1])

    def test_installation_implies_downloading(self):
        calls, _, _ = self.execute(download=False)
        self.assertNotIn("--downloadonly", calls[1])

    def test_disabled_updates_make_no_package_calls(self):
        calls, _, _ = self.execute(apply=False, download=False)
        self.assertEqual(calls, [])

    def test_global_default_mode_makes_no_package_calls(self):
        calls, _, _ = self.execute(mode="default")
        self.assertEqual(calls, [])

    def test_missing_packages_are_skipped_and_reported(self):
        calls, _, diagnostics = self.execute(installed="firefox\n")
        self.assertEqual(calls[1][-3:], ["upgrade", "--", "firefox"])
        self.assertIn("skipping uninstalled packages: google-chrome-stable", diagnostics)

    def test_no_selected_packages_installed(self):
        calls, _, diagnostics = self.execute(installed="bash\n")
        self.assertEqual(len(calls), 1)
        self.assertIn("no selected packages are installed", diagnostics)

    def test_invalid_or_duplicate_packages_fail_before_external_calls(self):
        for packages in ((), ("-y",), ("foo*",), ("/tmp/foo",),
                         ("firefox\n",), ("two names",), ("firefox", "firefox")):
            with self.subTest(packages=packages):
                with self.assertRaises(ValueError):
                    self.execute(packages=packages)

    def test_invalid_runtime_settings_fail(self):
        for settings in ({"mode": "unexpected"}, {"apply": "not-a-boolean"}):
            with self.subTest(settings=settings):
                with self.assertRaises(ValueError):
                    self.execute(**settings)

    def test_package_tool_failures_propagate(self):
        for executable in ("/usr/bin/rpm", "/usr/bin/dnf"):
            with self.subTest(executable=executable):
                with self.assertRaises(subprocess.CalledProcessError):
                    self.execute(fail=executable)

    def test_base_overrides_are_shared_without_exposing_values_in_arguments(self):
        calls, configurations, _ = self.execute(overrides="keepcache=False\nproxy_password=private%value\n")
        self.assertFalse(configurations[0].getboolean("main", "keepcache"))
        self.assertEqual(configurations[0]["main"]["proxy_password"], "private%value")
        self.assertNotIn("private%value", " ".join(calls[1]))

    def test_custom_base_configuration_and_repository_sections_are_preserved(self):
        calls, configurations, _ = self.execute(
            base_config_file="/etc/dnf/custom.conf",
            base_configuration="[main]\ngpgcheck=True\n[private]\nbaseurl=https://example.invalid/$releasever\n",
        )
        self.assertEqual(len(calls), 2)
        self.assertEqual(
            configurations[0]["private"]["baseurl"],
            "https://example.invalid/$releasever",
        )

    def test_installed_package_query_uses_the_overridden_installroot(self):
        self.execute(overrides="installroot=/image\n", installroot="/image")

    def test_relative_installroot_fails_before_package_calls(self):
        with self.assertRaises(ValueError):
            self.execute(overrides="installroot=relative\n")

    def test_invalid_or_missing_base_configuration_fails(self):
        for configuration in ("not an INI file", FileNotFoundError("missing dnf.conf")):
            with self.subTest(configuration=configuration):
                with self.assertRaises((configparser.Error, OSError)):
                    self.execute(base_configuration=configuration)


if __name__ == "__main__":
    unittest.main()

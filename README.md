# escapace.unattended_upgrades

Configures DNF automatic updates on Red Hat-family systems and enables the existing `dnf-automatic-install.timer` without starting it or running updates during image preparation. The service obeys the configured download/install mode instead of the vendor unit's forced-install flag.

## Variables

- `unattended_upgrades_dnf_upgrade_type` defaults to `security`; accepts `security` or `default`. Security mode requires repository security-advisory metadata. Default mode considers all available updates.
- `unattended_upgrades_dnf_default_packages` defaults to `[]`. Supply unique, plain RPM package names, without paths, globs or command options. After a successful security pass, the same service upgrades these installed packages without requiring security advisories. Dependencies may also change. Uninstalled names are skipped and reported. Global `default` mode skips the extra transaction.
- `unattended_upgrades_dnf_apply_updates` defaults to `true`. Installing updates implies downloading them.
- `unattended_upgrades_dnf_download_updates` defaults to `true`. With installation disabled, both passes only download updates. When both settings are false, neither pass downloads or installs packages.
- `unattended_upgrades_dnf_random_sleep` defaults to `300` seconds, in addition to the distribution timer's random delay.
- `unattended_upgrades_dnf_base_overrides` defaults to `{}`. These DNF base-setting overrides apply to both transactions. The additional pass inherits the normal DNF configuration and applies these overrides through a private temporary configuration, not process arguments.
- `unattended_upgrades_dnf_emit_via` defaults to `stdio`; accepts comma-separated DNF automatic emitter names.
- `unattended_upgrades_dnf_command_format` defaults to `cat`, and `unattended_upgrades_dnf_stdin_format` defaults to `{body}`; these configure the command emitter.
- `unattended_upgrades_dnf_email_command_format` defaults to `mail -s {subject} -r {email_from} {email_to}`, and `unattended_upgrades_dnf_email_stdin_format` defaults to `{body}`; these configure the email-command emitter.
- `unattended_upgrades_dnf_email_from` and `unattended_upgrades_dnf_email_to` both default to `root`; `unattended_upgrades_dnf_email_host` defaults to `localhost`.

For example, keep ordinary updates security-only while accepting all Chrome and Firefox package updates:

```yaml
unattended_upgrades_dnf_upgrade_type: security
unattended_upgrades_dnf_default_packages:
  - google-chrome-stable
  - firefox
```

Both transactions run sequentially under the existing service and timer. If the normal pass fails, the additional pass does not run. Failures in the additional pass fail the service and appear in its journal. Removing the list removes the additional command and helper. The role does not create another timer or configure repositories.

The role adds no browser-termination or reboot operation; RPM maintenance scripts still run. Callers activate the timer after image preparation. Changed unit configuration reloads only a running systemd manager, including when the update service is inactive.

See the [DNF automatic configuration reference](https://dnf.readthedocs.io/en/latest/automatic.html) for emitter and base-setting semantics. A package exception does not repair missing security-advisory metadata for other packages.

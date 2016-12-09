<p align="right">
    <a href="https://travis-ci.org/epiloque/ansible-unattended-upgrades">
        <img src="https://travis-ci.org/epiloque/ansible-unattended-upgrades.svg?branch=master"
             alt="build status">
    </a>
        <a href="https://galaxy.ansible.com/epiloque/epiloque">
        <img src="https://img.shields.io/badge/ansible--galaxy-unattended--upgrades-blue.svg"
             alt="ansible galaxy">
    </a>
</p>

unattended-upgrades role

## Role Variables

Available variables are listed below, along with default values:

```yaml
# what kind of update to use:
#
# default
# security
# security-severity:critical
# minimal
# minimal-security
# minimal-security-severity:critical

unattended_upgrades_yum_update_cmd: security

unattended_upgrades_apt_origins_patterns:
  - 'origin=Ubuntu,archive=${distro_codename}-security,label=Ubuntu'

unattended_upgrades_apt_package_blacklist: []

# On a unclean dpkg exit unattended-upgrades will run
#   dpkg --force-confold --configure -a
unattended_upgrades_apt_autofix_interrupted_dpkg: true

# Split the upgrade into the smallest possible chunks so that they can be
# interrupted with SIGUSR1. This makes the upgrade a bit slower but it has the
# benefit that shutdown while a upgrade is running is possible (with a small
# delay)
unattended_upgrades_apt_minimal_steps: false

# Install all unattended-upgrades when the machine is shuting down instead of
# doing it in the background while the machine is running This will (obviously)
# make shutdown slower
unattended_upgrades_apt_install_on_shutdown: false

# Send email to this address for problems or packages upgrades If empty or unset
# then no email is sent, make sure that you have a working mail setup on your
# system. A package that provides 'mailx' must be installed.
unattended_upgrades_apt_mail: false

# Set this value to "true" to get emails only on errors. Default is to always
# send a mail if Unattended-Upgrade::Mail is set
unattended_upgrades_apt_mail_only_on_error: false

# Do automatic removal of new unused dependencies after the upgrade (equivalent
# to apt-get autoremove)
unattended_upgrades_apt_remove_unused_dependencies: false

# Automatically reboot *WITHOUT CONFIRMATION* if a the file
# /var/run/reboot-required is found after the upgrade
unattended_upgrades_apt_automatic_reboot: false

# If automatic reboot is enabled and needed, reboot at the specific time instead
# of immediately
unattended_upgrades_apt_automatic_reboot_time: false

# Do upgrade application even if it requires restart after upgrade I.e.
# "XB-Upgrade-Requires: app-restart" is set in the debian/control file
unattended_upgrades_apt_ignore_apps_require_restart: false
```

## Example Playbook

```yaml
- hosts: servers
  roles:
    - epiloque.unattended-upgrades
```

## License

BSD

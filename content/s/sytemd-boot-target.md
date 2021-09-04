+++
title = "💾 Systemd boot target"
slug = "systemd-boot-target"
+++


#### Deacivate the graphical interface
This is a multi-user and non-graphical runlevel. Multiple users can log in via local consoles/terminals or remote network access.
```bash
systemctl set-default multi-user.target
reboot
```

#### Set graphical 
The `graphical.target` target unit, starts the services that lead to launch a graphics session.
```bash
systemctl set-default graphical.target
reboot
```
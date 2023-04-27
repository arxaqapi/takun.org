+++
draft = true
title = "Fedora on WSL"
slug = "fedora-on-wsl"
date = 2021-08-30
[taxonomies]
tags = ["linux", "windows"]
[extra]
summary = "Installing fedora (34) on WSL"
+++

I hate windows.

But sadly the laptop I currently own is not well supported under linux, there are a lot of missing divers and strange behaviours can occur.

Since WSL has become a good solution for developpers who want to work with the correct tools (linux) but also want to benefit from Windows-only software.

This simple guide aims to install a very well known and up to date linux distribution, [fedora](https://getfedora.org).

### Prerequisites
[Have WSL2 installed and set as default.](https://docs.microsoft.com/en-us/windows/wsl/install-win10)

### Fedora 3x rootfs
Get the latest fedora rootfs.

<!-- > **What is a rootfs?**
> a rootfs is, well, simply the root file system of fedora -->

You can pick it [here](https://github.com/fedora-cloud/docker-brew-fedora/tree/34/x86_64) just make sure the branch name matches the version you want to install.

Unzip the file to obtain a fedora-3x-xxxx.tar file (Do not unpack it).

### Composing the fedora build
The distro will be installed in the `C:\WSL\` folder, feel free to pick a  custom location. To do this, just type the following command in a powershell and replace x with the version of fedora that you want to install.
```powershell
wsl --import Fedora-3x c:\WSL\Fedora-3x $HOME\Downloads\fedora-3x-xxxx.tar
```

Fedora will then show-up in WSL's list of installed distros.
```powershell 
wsl -l -v
  NAME         STATE           VERSION
* Fedora-34    Running         2
```

To get a fedora shell, just type the following command:
```powershell
wsl -d Fedora-3x
```

Next we will install a few usefull packages and prepare the creation of a user.

```bash
dnf update
dnf install wget curl sudo ncurses dnf-plugins-core dnf-utils passwd findutils
```

### Adding a user 
To add a default user (we do not want to login as root everytime we open a new shell), we first need to create a new user.
```bash
useradd -G wheel username
passwd username
```

Cnce the user has been created it is time to check if it was successfull by login in with the new created user and testing the sudo command.
```powershell
wsl -d Fedora-33 -u yourusername
$ id -u
1000
$ sudo cat /etc/shadow
```

Now it is time to declare the user as the default one. Make sure you have exited the wsl instance and got a powershell back.
```powershell
Get-ItemProperty Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Lxss\*\ DistributionName | Where-Object -Property DistributionName -eq Fedora-3x  | Set-ItemProperty -Name DefaultUid -Value 1000
```


### Fedora "build-essential"
A lot of tools are missing to guaranty a smooth user experience. To remedy that, we an install the fedora equivalent of ubuntu's build-essential.

I name the *groupinstall* subcommand.
```bash
sudo dnf groupinstall "Development Tools" "Development Libraries"
```
 
### Conclusion

And there it is, a simple guide to install fedora on WSL2.

This guide will probably be updated in the future to explain more in details some of the used commands.

----------


### References

This guide is more a personnal memo to install fedora on wsl, it compiles two resources.
1. [Using Fedora 33 with Microsoft’s WSL2](https://fedoramagazine.org/wsl-fedora-33/)
2. [What is the Fedora equivalent of the Debian build-essential package?](https://unix.stackexchange.com/a/1344)
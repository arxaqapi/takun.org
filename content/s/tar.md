+++
title = "🗃️ tar"
slug = "tar"
+++

tar is a very handy tool and important to know if dealing with a lot of archives in a linux environnment
#### Compressing an archive
```bash
tar -czvf archive_name.tar.gz
```
- ' -c ': creates a new archive
#### extracting an archive
```bash
tar -xzvf archive_name.tar.gz
```
- ' -x ': stands for extract
- ' -z ': filters the archive through gzip
- ' -j ': filters the archive through gzip2
- ' -v ': verbose
- ' -f ': allows to specify a filename

with ' -C ', the archive can be extracted into another directory
```bash
tar -xzvf archive_name.tar.gz -C /home/user/destination_dir
```
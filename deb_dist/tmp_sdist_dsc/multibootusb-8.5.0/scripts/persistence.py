#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Name:     persistence.py
# Purpose:  Module to deal with persistence of a selected distro.
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import sys
import os
import platform
import tarfile
import subprocess
from . import usb
from . import iso
from . import gen
from . import config


def persistence_distro(distro, usb_disk, iso_link):
    """
    Function to detect if distro can have persistence option.
    :param distro: Detected distro name.
    :return: Distro name as string or None otherwise.
    """
    iso_size = iso.iso_size(iso_link)
    fat_max_size = (4096 * 1024 * 1024)
    usb_details = usb.details(usb_disk)
    usb_sf = usb_details['file_system']
    usb_free_size = usb_details['size_free']
    config.usb_uuid = usb_details['uuid']
    config.usb_label = usb_details['label']
    if usb_sf == 'vfat' or 'FAT32':
        if usb_free_size > fat_max_size:
            _max_size = fat_max_size
        else:
            _max_size = usb_free_size
    else:
        _max_size = usb_free_size
    if distro == "ubuntu":
        gen.log("Persistence option is available.")
        return "ubuntu", _max_size
    # FIXME to get debian persistence workable...
    #  Able to add successfully but unable to keep persistence data.
    elif distro == "debian" or distro == "debian-install":
        gen.log("Persistence option is available.")
        return "debian", _max_size
    elif distro == "fedora":
        gen.log("Persistence option is available.")
        return "fedora", _max_size
    else:
        return None, None


def create_persistence():
    if config.distro == "ubuntu":
        fs_name = 'casper-rw'
    elif config.distro == 'debian' or config.distro == "debian-install":
        fs_name = 'live-rw'
    elif config.distro == 'fedora':
        fs_name = 'overlay-' + config.usb_label + '-' + config.usb_uuid

    persistence = config.persistence / 1024 / 1024

    if platform.system() == 'Linux':
        mkfs = 'mkfs.ext3'
        dd = 'dd'
        persistence_mkfs_cmd = mkfs + ' -F ' + os.path.join(config.usb_mount, 'multibootusb',
                                                            iso.iso_basename(config.iso_link),
                                                            fs_name)
    elif platform.system() == 'Windows':
        mkfs = gen.quote(gen.resource_path(os.path.join("data", "tools", "mkfs", "mke2fs.exe")))
        dd = gen.quote(gen.resource_path(os.path.join("data", "tools", "dd", "dd.exe")))
        persistence_mkfs_cmd = 'echo y|' + mkfs + ' -b 1024 -L ' + fs_name + ' ' + os.path.join(config.usb_mount, 'multibootusb',
                                                            iso.iso_basename(config.iso_link), fs_name)

    if config.distro == 'fedora':
        persistence_dd_cmd = dd + ' if=/dev/zero ' \
                                  'of=' + os.path.join(config.usb_mount, 'multibootusb',
                                                       iso.iso_basename(config.iso_link), 'LiveOS', fs_name) + \
                             ' bs=1M count=' + str(int(persistence))
    else:
        persistence_dd_cmd = dd + ' if=/dev/zero of=' + os.path.join(config.usb_mount, 'multibootusb',
                                                   iso.iso_basename(config.iso_link), fs_name) +\
                                ' bs=1M count=' + str(int(persistence))

    gen.log('Executing ==>' + persistence_dd_cmd)
    config.status_text = 'Creating persistence file...'

    if subprocess.call(persistence_dd_cmd, shell=True) == 0:
        gen.log("\nSuccessfully created persistence file...\n")

    if not config.distro == 'fedora':
        gen.log('Applying filesystem to persistence file...')
        gen.log('Executing ==> ' + persistence_mkfs_cmd)
        config.status_text = 'Applying filesystem to persistence file...'
        if subprocess.call(persistence_mkfs_cmd, shell=True) == 0:
            gen.log("\nSuccessfully applied filesystem...\n")


def extract_file(file_path, install_dir):
    """
    Function to extract persistence files to distro install directory.
    :param file_path: Path to persistence file.
    :param install_dir: Path to distro install directory.
    :return:
    """
    tar = tarfile.open(file_path, "r:bz2")
    tar.extractall(install_dir)
    tar.close()


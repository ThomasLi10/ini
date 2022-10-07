#! /bin/bash
# Author: lixiang
# Created Time : Mon 17 Aug 2020 11:34:03 AM CST
# File Name: install.sh
# Description:

# Constants
CUR_DIR=$PWD
MAIN_DIR=/q/lib/platform/src/ini
sudo -u quant mkdir -m 755 $MAIN_DIR
# Inputs
VERSION=$1
# Default values
if [ -z $VERSION ];then
    cd $MAIN_DIR
    echo "- Current versions:"
    ls -l|tail -5
    read -p "- Enter the version you want to install: " VERSION
fi
if [ -z $VERSION ];then
    echo "- VERSION is not defined. Exit install.sh."
    exit 0
fi
DEST_DIR=$MAIN_DIR/$VERSION

#%% INSTALL
cd $CUR_DIR
BUILD_DIR=lib.linux-x86_64-3.9
CPY_VERSION=cpython-39-x86_64-linux-gnu
sudo -u quant mkdir -m 755 -p $DEST_DIR
sudo -u quant install -m 555 -o quant -g quant build/$BUILD_DIR/ini.$CPY_VERSION.so $DEST_DIR/ini.so

# Soft link of release
cd $MAIN_DIR
read -p "- Do you want to re-softlink? release/dev/[n] : " RELINK
if [ -z $RELINK ];then RELINK="n";fi
if [ ! $RELINK = "n" ]
then
    sudo -u quant rm -f $RELINK
    sudo -u quant ln -s $VERSION $RELINK
fi
sudo -u quant ls -l | grep -E "dev|release"

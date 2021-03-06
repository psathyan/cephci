#!/bin/bash

# As we are dynamically creating the Jenkins node using the OpenStack plugin,
# we require additional configurations to enable us to use the system for
# executing the cephci test suites. This script performs the required changes.

echo "Initialize Node"
sudo yum install -y wget git-core python3

# Workaround: Disable IPv6 to have quicker downloads
sudo sysctl -w net.ipv6.conf.eth0.disable_ipv6=1

# Mount reesi for storing logs
if [ ! -d "/ceph" ]; then
    echo "Mounting ressi004"
    sudo mkdir -p /ceph
    sudo mount -t nfs -o sec=sys,nfsvers=4.1 reesi004.ceph.redhat.com:/ /ceph
fi

# Copy the auth files from internal server to the Jenkins user home directory
wget http://magna002.ceph.redhat.com/cephci-jenkins/.osp-cred-ci-2.yaml -O ${HOME}/osp-cred-ci-2.yaml
wget http://magna002.ceph.redhat.com/cephci-jenkins/.cephci.yaml -O ${HOME}/.cephci.yaml

# Install cephci pre-requisistes
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
deactivate

echo "Done bootstraping the Jenkins node."


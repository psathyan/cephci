"""
This module contains workflow for deploying OSD on specific device

Sample test script

    - test:
      abort-on-fail: true
      desc: deploy osd on specific device
      module: osd_specific_device.py
      name: OSD on specific device
"""
import json
from typing import List

from ceph.ceph import Ceph, CephNode, CommandFailed
from utility.log import Log
from utility.retry import retry

log = Log(__name__)


def generate_osd_list(ceph_cluster: Ceph):
    """
    Generates OSD list from conf file

    Args:
        ceph_cluster (class): Ceph cluster info from conf file
    Returns:
        None
    """
    client = ceph_cluster.get_ceph_object("installer")
    ceph_osds = ceph_cluster.get_ceph_objects("osd")

    osd_nodes = set()
    disk_list = set()
    for osd in ceph_osds:
        osd_nodes.add(osd.node.vmshortname)
    osd_node_list = list(osd_nodes)
    log.info(osd_node_list)
    for osn in osd_node_list:
        for osd in ceph_osds:
            if osd.node.vmshortname == osn:
                for i in osd.node.vm_node.volumes:
                    disk_list.add(i)
                osd_node = osd.node
        osd_disk_list = list(disk_list)
        log.info(osd_disk_list)
        log.info(len(osd_disk_list))
        dump_osd_data(client, osn, osd_node, osd_disk_list)
        disk_list.clear()
        osd_disk_list.clear()


def dump_osd_data(node: CephNode, osn, osd_node, disk_list: List) -> None:
    """
    Deploy OSD on specific device

    Args:
        node:   Installer node
        osn:    OSD node name
        osd_node : node_ip of node where osd is to be deployed
        disk_list:   List of devices to deploy OSD
    Returns:
        None
    Raises:
        CommandFailed
    """
    for i in range(len(disk_list)):
        add_disk = 0
        try:
            node.exec_command(
                cmd=f"sudo cephadm shell -- ceph orch daemon add osd {osn}:{disk_list[i]}"
            )
        except CommandFailed:
            log.info(
                f"Could not deploy OSD on {disk_list[i]},could be root disk, looking for alternate disk of same size"
            )
            new_disk = get_new_disk(osd_node, disk_list)
            add_disk = 1
        if add_disk == 1:
            try:
                node.exec_command(
                    cmd=f"sudo cephadm shell -- ceph orch daemon add osd {osn}:{new_disk}"
                )
            except CommandFailed:
                log.info(
                    f"WARNING:Could not deploy all OSDs. Failed to deploy OSD on alternate disk {new_disk}"
                )
    expected_osd_count = len(disk_list)
    validate_osd(node, osn, expected_osd_count)


def get_new_disk(node, disk_list: List) -> None:
    """
    Find new disk with size same as in disk_list
    Args:
        node: node to get alternate disk
        disk_list: List of devices planned for OSD deploy
    Returns:
        newdisk
    """
    disk_size, rc = node.exec_command(cmd="lsblk -o NAME,SIZE -d")
    disk_size_list = str(disk_size).splitlines()
    disk_dict = {}
    root_disk_info, rc = node.exec_command(
        cmd='lsblk -o PKNAME,MOUNTPOINT -P | grep "MOUNTPOINT=\\"/\\""'
    )
    log.info(f"root_disk_info:{root_disk_info}")
    for line in disk_size_list:
        (disk, size) = line.split()
        if disk not in str(root_disk_info):
            disk_path = f"/dev/{disk}"
            disk_dict[disk_path] = size
            if disk_path in disk_list:
                disk_size = size

    for disk in disk_dict.keys():
        if (disk_size in disk_dict[disk]) and (disk not in disk_list):
            return disk


@retry(AssertionError, tries=60, delay=10)
def validate_osd(node: CephNode, osn, expected_osds):
    out, _ = node.exec_command(
        cmd="sudo cephadm shell -- ceph osd tree --format json-pretty"
    )
    oks = json.loads(out)
    for i in range(len(oks["nodes"])):
        if oks["nodes"][i]["name"] == osn:
            if len(oks["nodes"][i]["children"]) < expected_osds:
                raise AssertionError("Expected OSDs doesn't exist")
            osd_list = oks["nodes"][i]["children"]
            log.info(f"OSDs on {osn} : {osd_list}")
            break


def run(ceph_cluster: Ceph, **kwargs) -> int:
    """
    Entry point to this module that configures OSDs.
    """
    log.info("Configuring OSDs on given device")
    try:
        generate_osd_list(ceph_cluster)
    except BaseException as be:  # noqa
        log.error(be)
        return 1

    log.info("Successfully deployed OSDs on specific devices.")
    return 0

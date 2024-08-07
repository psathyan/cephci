"""Module to deploy RGW service and individual daemon(s)."""

from typing import Dict

from .apply import ApplyMixin
from .orch import Orch


class RGW(ApplyMixin, Orch):
    SERVICE_NAME = "rgw"

    def apply(self, config: Dict) -> None:
        """
        Deploy the RGW service using the provided data.

        Args:
            config (Dict): test arguments

        Example::

            <cephadm_shell> ceph orch apply rgw realm zone --placement="label:rgw"

            config:
                command: apply
                service: rgw
                base_cmd_args:              # arguments to ceph orch
                    concise: true
                    verbose: true
                    input_file: <name of spec>
                pos_args:                   # positional arguments
                    - my_rgw                # service id
                args:
                    rgw-realm: realm        # realm name in case of multi-site
                    rgw-zone: zone          # zone name in case of multi-site
                    port: int               # port number
                    ssl: true               # certification
                    placement:
                        label: rgw_south
                        nodes:              # A list of strings that would looked up
                            - node1
                        limit: 3            # no of daemons
                        sep: " "            # separator to be used for placements
                    dry-run: true
                    unmanaged: true

        """
        super().apply(config)

"""This module holds the configuration generators for routing daemons
that can be used in a router."""
from .base import BasicRouterConfig, RouterConfig
from .zebra import Zebra
from .ospf import OSPF, OSPFArea
from .bgp import BGP, AS, iBGPFullMesh, bgp_peering, bgp_fullmesh, ebgp_session

__all__ = ['BasicRouterConfig', 'Zebra', 'OSPF', 'OSPFArea', 'BGP', 'AS',
           'iBGPFullMesh', 'bgp_peering', 'RouterConfig', 'bgp_fullmesh',
           'ebgp_session']

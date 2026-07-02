"""
ServerDeals — 25 hardware categories with eBay US search queries and category IDs.

Groups: server, cpu, ram, storage, mainboard, gpu, network, systems, build
"""

from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# Group constants
# ---------------------------------------------------------------------------
GROUP_SERVER = "server"
GROUP_CPU = "cpu"
GROUP_RAM = "ram"
GROUP_STORAGE = "storage"
GROUP_MAINBOARD = "mainboard"
GROUP_GPU = "gpu"
GROUP_NETWORK = "network"
GROUP_SYSTEMS = "systems"
GROUP_BUILD = "build"


@dataclass(frozen=True)
class CategoryDef:
    key: str
    display_name: str
    ebay_search_query: str
    group_key: str
    ebay_category_id: Optional[int] = None


# ---------------------------------------------------------------------------
# All 25 categories
# ---------------------------------------------------------------------------
CATEGORIES: list[CategoryDef] = [
    # ── Server Group ──────────────────────────────────────────────────────
    CategoryDef(
        key="dell-poweredge",
        display_name="Dell PowerEdge Server",
        ebay_search_query="Dell PowerEdge server",
        group_key=GROUP_SERVER,
        ebay_category_id=175672,  # Servers, Clients & Terminals
    ),
    CategoryDef(
        key="hp-proliant",
        display_name="HP ProLiant Server",
        ebay_search_query="HP ProLiant server",
        group_key=GROUP_SERVER,
        ebay_category_id=175672,
    ),
    CategoryDef(
        key="supermicro-server",
        display_name="Supermicro Server",
        ebay_search_query="Supermicro server",
        group_key=GROUP_SERVER,
        ebay_category_id=175672,
    ),
    CategoryDef(
        key="rackmount-server",
        display_name="Rackmount Server",
        ebay_search_query="rackmount server",
        group_key=GROUP_SERVER,
        ebay_category_id=175672,
    ),

    # ── CPU Group ─────────────────────────────────────────────────────────
    CategoryDef(
        key="cpu",
        display_name="Intel Xeon CPU",
        ebay_search_query="Intel Xeon E5 CPU",
        group_key=GROUP_CPU,
        ebay_category_id=164,  # Computer Components & Parts → CPUs/Processors
    ),
    CategoryDef(
        key="cpu-consumer",
        display_name="AMD Ryzen Threadripper",
        ebay_search_query="AMD Ryzen Threadripper",
        group_key=GROUP_CPU,
        ebay_category_id=164,
    ),
    CategoryDef(
        key="amd-epyc",
        display_name="AMD EPYC CPU",
        ebay_search_query="AMD EPYC CPU",
        group_key=GROUP_CPU,
        ebay_category_id=164,
    ),

    # ── RAM Group ─────────────────────────────────────────────────────────
    CategoryDef(
        key="ecc-ram",
        display_name="ECC DDR4 Registered RAM",
        ebay_search_query="ECC RAM DDR4 registered",
        group_key=GROUP_RAM,
        ebay_category_id=170083,  # Enterprise Server Memory (RAM)
    ),
    CategoryDef(
        key="ddr5-ram",
        display_name="DDR5 RAM",
        ebay_search_query="DDR5 RAM",
        group_key=GROUP_RAM,
        ebay_category_id=170599,  # Desktop Memory (RAM)
    ),

    # ── Storage Group ─────────────────────────────────────────────────────
    CategoryDef(
        key="nas",
        display_name="NAS (Synology/QNAP)",
        ebay_search_query="Synology QNAP NAS",
        group_key=GROUP_STORAGE,
        ebay_category_id=124418,  # Network Attached Storage (NAS)
    ),
    CategoryDef(
        key="ssd-nvme",
        display_name="Enterprise SSD NVMe U.2",
        ebay_search_query="enterprise SSD NVMe U.2",
        group_key=GROUP_STORAGE,
        ebay_category_id=175669,  # Enterprise Solid State Drives
    ),
    CategoryDef(
        key="ssd-sata",
        display_name="Enterprise SSD SATA",
        ebay_search_query="enterprise SSD SATA",
        group_key=GROUP_STORAGE,
        ebay_category_id=175669,
    ),
    CategoryDef(
        key="ssd-m2-nvme",
        display_name="NVMe SSD M.2",
        ebay_search_query="NVMe SSD M.2",
        group_key=GROUP_STORAGE,
        ebay_category_id=175669,
    ),
    CategoryDef(
        key="sas-drive",
        display_name="SAS Hard Drive",
        ebay_search_query="SAS hard drive",
        group_key=GROUP_STORAGE,
        ebay_category_id=56083,  # Enterprise Hard Drives
    ),

    # ── Mainboard Group ───────────────────────────────────────────────────
    CategoryDef(
        key="motherboard",
        display_name="Server Motherboard",
        ebay_search_query="server motherboard",
        group_key=GROUP_MAINBOARD,
        ebay_category_id=1244,  # Motherboards
    ),
    CategoryDef(
        key="motherboard-consumer",
        display_name="Desktop Motherboard LGA",
        ebay_search_query="desktop motherboard LGA",
        group_key=GROUP_MAINBOARD,
        ebay_category_id=1244,
    ),

    # ── GPU Group ─────────────────────────────────────────────────────────
    CategoryDef(
        key="gpu",
        display_name="Datacenter GPU (Tesla)",
        ebay_search_query="NVIDIA Tesla datacenter GPU",
        group_key=GROUP_GPU,
        ebay_category_id=27386,  # Graphics/Video Cards
    ),
    CategoryDef(
        key="gpu-consumer",
        display_name="Consumer GPU (RTX)",
        ebay_search_query="gaming GPU RTX",
        group_key=GROUP_GPU,
        ebay_category_id=27386,
    ),

    # ── Network Group ─────────────────────────────────────────────────────
    CategoryDef(
        key="network-switch",
        display_name="Managed Network Switch",
        ebay_search_query="managed network switch",
        group_key=GROUP_NETWORK,
        ebay_category_id=51268,  # Enterprise Network Switches
    ),
    CategoryDef(
        key="nic",
        display_name="10Gb Network Interface Card",
        ebay_search_query="network interface card 10Gb",
        group_key=GROUP_NETWORK,
        ebay_category_id=20318,  # Network Interface Cards (NICs)
    ),
    CategoryDef(
        key="hba-card",
        display_name="HBA Controller Card",
        ebay_search_query="HBA controller card",
        group_key=GROUP_NETWORK,
        ebay_category_id=90715,  # Disk Controllers / RAID Cards
    ),

    # ── Systems Group ─────────────────────────────────────────────────────
    CategoryDef(
        key="mini-pc",
        display_name="Mini PC Server",
        ebay_search_query="mini PC server",
        group_key=GROUP_SYSTEMS,
        ebay_category_id=179,  # Desktops & All-in-Ones
    ),
    CategoryDef(
        key="thin-client",
        display_name="Thin Client",
        ebay_search_query="thin client",
        group_key=GROUP_SYSTEMS,
        ebay_category_id=179,
    ),
    CategoryDef(
        key="sbc",
        display_name="Single Board Computer",
        ebay_search_query="single board computer",
        group_key=GROUP_SYSTEMS,
        ebay_category_id=171957,  # Single Board Computers
    ),

    # ── Build Group ───────────────────────────────────────────────────────
    CategoryDef(
        key="case",
        display_name="Server Chassis Case",
        ebay_search_query="server chassis case",
        group_key=GROUP_BUILD,
        ebay_category_id=51064,  # Computer Cases
    ),
]

# ---------------------------------------------------------------------------
# Derived helpers
# ---------------------------------------------------------------------------
CATEGORIES_BY_KEY: dict[str, CategoryDef] = {c.key: c for c in CATEGORIES}

GROUPS: list[str] = [
    GROUP_SERVER,
    GROUP_CPU,
    GROUP_RAM,
    GROUP_STORAGE,
    GROUP_MAINBOARD,
    GROUP_GPU,
    GROUP_NETWORK,
    GROUP_SYSTEMS,
    GROUP_BUILD,
]


def by_group(group_key: str) -> list[CategoryDef]:
    """Return all categories belonging to *group_key*."""
    return [c for c in CATEGORIES if c.group_key == group_key]


def get_category(key: str) -> CategoryDef:
    """Look up a category by its unique key."""
    cat = CATEGORIES_BY_KEY.get(key)
    if cat is None:
        raise KeyError(f"Unknown category key: {key!r}")
    return cat

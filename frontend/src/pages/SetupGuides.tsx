import { Link } from 'react-router-dom';

const GUIDES = [
  {
    slug: 'proxmox',
    title: 'Proxmox VE Homelab',
    description: 'Build a virtualized homelab with Proxmox — perfect for learning, testing, and self-hosting.',
    icon: '🖥️',
    content: `## Proxmox VE Homelab Guide

### Minimum Specs
- **CPU:** Any server-class CPU (Xeon E5 v3+, EPYC 7001+, or even a Ryzen)
- **RAM:** 32 GB minimum (64 GB+ recommended for multiple VMs)
- **Storage:** Boot SSD (128 GB+) + VM storage (NVMe recommended)
- **Networking:** At least 2× 1GbE ports

### Recommended eBay Deals
- Dell PowerEdge R730 / R730xd — great balance of price and performance
- HPE ProLiant DL380 Gen9 — widely available, good value
- Supermicro 6028U — flexible whitebox option

### Getting Started
1. Install Proxmox VE from ISO onto the boot SSD
2. Configure storage pools (ZFS recommended for mirrors)
3. Set up networking — bridges for VMs, VLANs for isolation
4. Deploy your first VM (Ubuntu Server 22.04 LTS)
5. Set up automated backups via Proxmox Backup Server

### Tips
- Look for "2× E5-2680 v4" or "2× E5-2690 v4" listings for high core counts
- DDR4 ECC RAM is cheap on eBay — max it out
- LFF (3.5") chassis accept cheaper high-capacity HDDs`,
  },
  {
    slug: 'nas',
    title: 'NAS / Home Server',
    description: 'Build a reliable NAS for media storage, backups, and file sharing.',
    icon: '💾',
    content: `## NAS Build Guide

### Minimum Specs
- **CPU:** Low-power Xeon or modern Celeron/Pentium
- **RAM:** 16 GB minimum (ZFS likes RAM)
- **Storage:** 4+ drive bays, mix of SSD cache + HDD bulk
- **OS:** TrueNAS Scale or Unraid

### Recommended eBay Deals
- Dell PowerEdge T330 / T430 — quiet tower servers
- HPE ProLiant ML30 / ML110 — compact, efficient
- Supermicro 846 chassis — high density storage

### Getting Started
1. Choose TrueNAS Scale (ZFS) or Unraid (flexible array expansion)
2. Plan your pool layout — mirror vdevs for performance, RAID-Z2 for capacity
3. Install OS on a small dedicated SSD
4. Create SMB/NFS shares for your network
5. Set up automated SMART tests and scrubs

### Tips
- Used enterprise SAS drives are incredibly cheap — get 3-4 TB drives for ~$25-40 each
- Add a small NVMe SSD as a ZFS SLOG or L2ARC for acceleration`,
  },
  {
    slug: 'plex',
    title: 'Plex / Jellyfin Media Server',
    description: 'Stream your media collection anywhere with hardware transcoding.',
    icon: '🎬',
    content: `## Plex / Jellyfin Media Server Guide

### Minimum Specs
- **CPU:** Intel 7th+ gen with Quick Sync (or a cheap NVIDIA Quadro for transcoding)
- **RAM:** 8 GB minimum (16 GB+ for 4K transcoding)
- **Storage:** SSD for OS/metadata + HDD array for media
- **GPU:** Optional — Intel iGPU or NVIDIA P400/T400 for hardware transcoding

### Recommended eBay Deals
- Dell OptiPlex 7060 / 7070 SFF — cheap, quiet, Intel Quick Sync
- HP EliteDesk 800 G4/G5 SFF — excellent value
- NVIDIA Quadro P400 (~$30-40 on eBay) — great transcoding on a budget

### Getting Started
1. Install Ubuntu Server or Debian
2. Set up Docker with Portainer
3. Deploy Plex or Jellyfin via Docker Compose
4. Mount media storage (local or NAS)
5. Configure hardware transcoding (Intel QSV or NVENC)
6. Set up Sonarr/Radarr for automated media management

### Tips
- Don't buy a rack server for Plex — a used office desktop with Intel Quick Sync is quieter, cheaper, and more power efficient
- Plex Pass is required for hardware transcoding; Jellyfin is free`,
  },
  {
    slug: 'llm',
    title: 'LLM / AI Workstation',
    description: 'Build a budget GPU rig for running local LLMs, Stable Diffusion, and AI workloads.',
    icon: '🤖',
    content: `## LLM / AI Workstation Guide

### Minimum Specs
- **CPU:** Any modern platform (single socket is fine)
- **RAM:** 64 GB+ system RAM
- **GPU:** NVIDIA RTX 3090 (24 GB VRAM) — best value for LLMs
- **Storage:** 1 TB+ NVMe for models

### Recommended eBay Deals
- NVIDIA RTX 3090 (~$600-800) — 24 GB VRAM for large models
- NVIDIA Tesla P40 (24 GB, ~$170-200) — no fan, needs DIY cooling
- Dell Precision / HP Z-series workstations with GPU support

### Getting Started
1. Install Ubuntu 22.04 or 24.04
2. Install NVIDIA drivers + CUDA toolkit
3. Set up Ollama for easy LLM serving
4. Install text-generation-webui (oobabooga) or vLLM for advanced use
5. Try models: Llama 3 (8B/70B), Mixtral 8×7B, Gemma 2

### Tips
- 24 GB VRAM runs Llama 3 70B at Q3_K_M quantization (~30 GB total, offloads to system RAM)
- Multiple P40s can be combined for more VRAM headroom
- Look for "blower" style GPUs if putting multiple in one case`,
  },
];

export default function SetupGuides() {
  return (
    <div>
      <h1 className="mb-2 text-3xl font-bold text-gray-900">Setup Guides</h1>
      <p className="mb-8 text-gray-500">
        Everything you need to turn eBay server deals into working homelab rigs.
      </p>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {GUIDES.map((guide) => (
          <Link
            key={guide.slug}
            to={`/setup/${guide.slug}`}
            className="group rounded-2xl border border-gray-200 bg-white p-6 transition-all hover:shadow-lg hover:border-brand-300"
          >
            <span className="mb-3 block text-4xl">{guide.icon}</span>
            <h2 className="mb-2 text-xl font-semibold text-gray-900 group-hover:text-brand-600">
              {guide.title}
            </h2>
            <p className="text-sm text-gray-500">{guide.description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}

export function SetupGuideDetail() {
  const slug = window.location.pathname.split('/setup/')[1];
  const guide = GUIDES.find((g) => g.slug === slug);

  if (!guide) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center">
        <h1 className="mb-2 text-2xl font-bold text-gray-900">Guide not found</h1>
        <Link to="/setup" className="text-brand-600 hover:text-brand-700">
          ← Back to guides
        </Link>
      </div>
    );
  }

  return (
    <div>
      <Link to="/setup" className="mb-6 inline-block text-sm text-brand-600 hover:text-brand-700">
        ← Back to guides
      </Link>
      <h1 className="mb-1 text-3xl font-bold text-gray-900">{guide.icon} {guide.title}</h1>
      <p className="mb-8 text-gray-500">{guide.description}</p>
      <div className="rounded-xl border border-gray-200 bg-white p-6 md:p-8">
        <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-gray-700">
          {guide.content}
        </pre>
      </div>
    </div>
  );
}

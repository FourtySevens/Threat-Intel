"""High-signal RSS sources seeded on explicit operator request."""

RSS_SEEDS = (
    {"name": "CISA Cybersecurity Advisories", "feed_url": "https://www.cisa.gov/cybersecurity-advisories/all.xml", "source_type": "advisory", "reliability": "high", "default_priority": 1},
    {"name": "Microsoft MSRC", "feed_url": "https://api.msrc.microsoft.com/update-guide/rss", "source_type": "advisory", "reliability": "high", "default_priority": 1},
    {"name": "The DFIR Report", "feed_url": "https://thedfirreport.com/feed/", "source_type": "research", "reliability": "high", "default_priority": 2},
    {"name": "Palo Alto Unit 42", "feed_url": "https://unit42.paloaltonetworks.com/feed/", "source_type": "research", "reliability": "high", "default_priority": 2},
    {"name": "Cisco Talos", "feed_url": "https://blog.talosintelligence.com/feeds/posts/default?alt=rss", "source_type": "research", "reliability": "high", "default_priority": 2},
    {"name": "SANS Internet Storm Center", "feed_url": "https://isc.sans.edu/rssfeed.xml", "source_type": "research", "reliability": "high", "default_priority": 2},
    {"name": "BleepingComputer", "feed_url": "https://www.bleepingcomputer.com/feed/", "source_type": "news", "reliability": "medium", "default_priority": 3},
)

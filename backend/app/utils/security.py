import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeURLError(ValueError):
    """Raised when a URL fails security/SSRF validation checks."""
    pass


def validate_safe_url(url: str) -> str:
    """Validate that a URL uses http/https and does not resolve to private, loopback, or local IP addresses."""
    if not url or not isinstance(url, str):
        raise UnsafeURLError("URL must be a non-empty string.")

    parsed = urlparse(url.strip())

    if parsed.scheme.lower() not in ("http", "https"):
        raise UnsafeURLError(f"Invalid URL scheme '{parsed.scheme}'. Only 'http' and 'https' are supported.")

    hostname = parsed.hostname
    if not hostname:
        raise UnsafeURLError("Invalid URL: missing hostname.")

    hostname_lower = hostname.lower()
    if hostname_lower in ("localhost", "localhost.localdomain", "loopback"):
        raise UnsafeURLError(f"Access to local hostname '{hostname}' is forbidden.")

    try:
        addr_info = socket.getaddrinfo(hostname, None)
    except socket.gaierror as err:
        raise UnsafeURLError(f"Failed to resolve host '{hostname}': {err}")

    for family, socktype, proto, canonname, sockaddr in addr_info:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue

        if ip.is_loopback:
            raise UnsafeURLError(f"Access to loopback IP '{ip_str}' is forbidden.")
        if ip.is_private:
            raise UnsafeURLError(f"Access to private IP '{ip_str}' is forbidden.")
        if ip.is_link_local:
            raise UnsafeURLError(f"Access to link-local IP '{ip_str}' is forbidden.")
        if ip.is_reserved:
            raise UnsafeURLError(f"Access to reserved IP '{ip_str}' is forbidden.")
        if ip.is_multicast:
            raise UnsafeURLError(f"Access to multicast IP '{ip_str}' is forbidden.")

    return url

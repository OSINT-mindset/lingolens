import asyncio

import streamlit as st

from lingolens import *
import webpage


async def get_proxies():
    from proxybroker2 import Broker, ProxyPool
    from proxybroker2.errors import NoProxyError

    proxies = asyncio.Queue()
    proxy_pool = ProxyPool(proxies)

    broker = Broker(
        proxies, timeout=8, max_conn=200, max_tries=3, verify_ssl=False,
        stop_broker_on_sigint=False,
    )

    types = [('HTTP', ('Anonymous', 'High')), ]

    await broker.find(types=types, strict=True, limit=10)
    return proxy_pool


webpage.main()

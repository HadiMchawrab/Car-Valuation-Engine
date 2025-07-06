import requests

cookies = {
    'anonymous_session_id': '357f450a-fd81-4af3-bbda-0d24b51a099d',
    'device_id': 'mc68z0uffwlwh483',
    'settings': '%7B%22area%22%3Anull%2C%22currency%22%3A%22SAR%22%2C%22installBanner%22%3Atrue%2C%22searchHitsLayout%22%3A%22LIST%22%7D',
    '_tt_enable_cookie': '1',
    '_ttp': '01JY9985PSSN77PBGDNWXHHB3Q_.tt.1',
    '_scid': '4gw28BNPv-cYG-qgJFHwSR8R8n-yESQw',
    '_ScCbts': '%5B%5D',
    '_sctr': '1%7C1750449600000',
    '_gid': 'GA1.2.610373445.1750868394',
    '_scid_r': '-4w28BNPv-cYG-qgJFHwSR8R8n-yESQw70kNlw',
    '_ga': 'GA1.1.668047289.1750510868',
    '_ga_664MMPB68F': 'GS2.1.s1750935369$o3$g1$t1750938281$j56$l0$h0',
    'referrer': '%2Fad%2F%D9%87%D9%8A%D9%88%D9%86%D8%AF%D8%A7%D9%8A-%D8%A8%D8%A7%D9%84%D9%8A%D8%B3%D8%A7%D8%AF-2019-ID110475918.html',
    'landing_url': '%2Fad%2F%D9%87%D9%8A%D9%88%D9%86%D8%AF%D8%A7%D9%8A-%D8%A8%D8%A7%D9%84%D9%8A%D8%B3%D8%A7%D8%AF-2019-ID110475918.html',
    'ttcsid_CQBMQO3C77U7A8U7NOIG': '1750935368882::GT2Xr5lZKJF0EdNBqtTQ.3.1750938281436',
    'ttcsid': '1750935368883::vP9M38Bawo17eTpdqYER.3.1750938281436',
    'hb-session-id': 'eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0.._V4VKCXoYFiSUC00.vLuxP32qAxb1z1fbXUH1uzqTcjbtRK6sMnTOLWs6PFp0eWVTykB63PnSZCDK9Rr6-5W8uNytKeiZR0aHR8MW-bV2ljfBor25PIgVZh5LWrbP6T6d5xEmP9zGDrVI65C2PgsUIggPhYiOeh3bG54b6ruRzDuRnJvoHOTxT6xsm9VDec1zyAbslk-Z4iB2uKjsqtHfvZaj3QhPGMjhoja69AuF-ASN4pweyYNaDGTDUZjyNXBx-JwLQc-uHtcWJxJcj7goE3MXrnt4ddL_mna6VY_kzhv1LeEZgu0kcJ5X8_tqEln7vH38SJvXeaXCfsWibCVPhH8XP-g43D3QMFxFH4ZhJCQaP4Psr-JoIyiI8KqZQfG7BrQUzHcYrfTiUqjV2Ik.anvxzoHMaPR2xYQvRNNYXA',
}

headers = {
    'accept': 'application/json',
    'accept-language': 'ar',
    'if-none-match': 'W/"409a5c16c24e89a41f6ae8da6368bb27"',
    'priority': 'u=1, i',
    'referer': 'https://www.dubizzle.sa/en/ad/%D9%87%D9%88%D9%86%D8%AF%D8%A7%D9%8A-%D8%A8%D8%A7%D9%84%D8%B3%D9%8A%D8%AF-2019-%D8%AF%D9%8A%D8%B2%D9%84-hyundai-palisade-2019-diesel-ID110474910.html',
    'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
    # 'cookie': 'anonymous_session_id=357f450a-fd81-4af3-bbda-0d24b51a099d; device_id=mc68z0uffwlwh483; settings=%7B%22area%22%3Anull%2C%22currency%22%3A%22SAR%22%2C%22installBanner%22%3Atrue%2C%22searchHitsLayout%22%3A%22LIST%22%7D; _tt_enable_cookie=1; _ttp=01JY9985PSSN77PBGDNWXHHB3Q_.tt.1; _scid=4gw28BNPv-cYG-qgJFHwSR8R8n-yESQw; _ScCbts=%5B%5D; _sctr=1%7C1750449600000; _gid=GA1.2.610373445.1750868394; _scid_r=-4w28BNPv-cYG-qgJFHwSR8R8n-yESQw70kNlw; _ga=GA1.1.668047289.1750510868; _ga_664MMPB68F=GS2.1.s1750935369$o3$g1$t1750938281$j56$l0$h0; referrer=%2Fad%2F%D9%87%D9%8A%D9%88%D9%86%D8%AF%D8%A7%D9%8A-%D8%A8%D8%A7%D9%84%D9%8A%D8%B3%D8%A7%D8%AF-2019-ID110475918.html; landing_url=%2Fad%2F%D9%87%D9%8A%D9%88%D9%86%D8%AF%D8%A7%D9%8A-%D8%A8%D8%A7%D9%84%D9%8A%D8%B3%D8%A7%D8%AF-2019-ID110475918.html; ttcsid_CQBMQO3C77U7A8U7NOIG=1750935368882::GT2Xr5lZKJF0EdNBqtTQ.3.1750938281436; ttcsid=1750935368883::vP9M38Bawo17eTpdqYER.3.1750938281436; hb-session-id=eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0.._V4VKCXoYFiSUC00.vLuxP32qAxb1z1fbXUH1uzqTcjbtRK6sMnTOLWs6PFp0eWVTykB63PnSZCDK9Rr6-5W8uNytKeiZR0aHR8MW-bV2ljfBor25PIgVZh5LWrbP6T6d5xEmP9zGDrVI65C2PgsUIggPhYiOeh3bG54b6ruRzDuRnJvoHOTxT6xsm9VDec1zyAbslk-Z4iB2uKjsqtHfvZaj3QhPGMjhoja69AuF-ASN4pweyYNaDGTDUZjyNXBx-JwLQc-uHtcWJxJcj7goE3MXrnt4ddL_mna6VY_kzhv1LeEZgu0kcJ5X8_tqEln7vH38SJvXeaXCfsWibCVPhH8XP-g43D3QMFxFH4ZhJCQaP4Psr-JoIyiI8KqZQfG7BrQUzHcYrfTiUqjV2Ik.anvxzoHMaPR2xYQvRNNYXA',
}

params = {
    'external_id': '110474910',
}

response = requests.get('https://www.dubizzle.sa/api/listing/', params=params, cookies=cookies, headers=headers)
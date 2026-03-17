# tests/test_wifi_patch.py

import pytest

@pytest.mark.asyncio
async def test_patch_status_and_security(async_client, any_wifi_id, restore_helper, auth_headers_async):

    async with restore_helper(any_wifi_id, "status"):
        r = await async_client.patch(
            f"/hotspots/{any_wifi_id}/status",
            params={"status": "Live"},
            headers=auth_headers_async
        )
        assert r.status_code == 200

    async with restore_helper(any_wifi_id, "security_protection"):
        r = await async_client.patch(
            f"/hotspots/{any_wifi_id}/security",
            params={"security_protection": "wpa2"},
            headers=auth_headers_async
        )
        assert r.status_code == 200
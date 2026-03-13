import pytest

@pytest.mark.asyncio
async def test_patch_status_and_security(async_client, any_wifi_id, restore_helper):
    # Backup current values and ensure they are restored at the end
    async with restore_helper(any_wifi_id, "status") as before_status:
        r = await async_client.patch(f"/hotspots/{any_wifi_id}/status", params={"status": "Live"})
        assert r.status_code == 200
        # status restored automatically by fixture on exit

    async with restore_helper(any_wifi_id, "security_protection") as before_sec:
        r = await async_client.patch(
            f"/hotspots/{any_wifi_id}/security",
            params={"security_protection": "wpa2"},
        )
        assert r.status_code == 200
        # security_protection restored automatically by fixture
import aiohttp
import asyncio


async def main():
    async with aiohttp.ClientSession() as session:
        response = await session.post(
            "http://0.0.0.0:8080/adv/",
            json={"header": "sdfg", "description": "gfhj", "owner": "User1"},
        )
        json_data = await response.json()
        print(json_data)

        # response = await session.get(
        #     "http://0.0.0.0:8080/adv/1",
        # )
        # json_data = await response.json()
        # print(json_data)

        # response = await session.delete(
        #     "http://0.0.0.0:8080/adv/1",
        # )
        # json_data = await response.json()
        # print(json_data)


asyncio.run(main())

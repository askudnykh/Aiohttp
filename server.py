import json
import datetime
from aiohttp import web
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import Column, Integer, String, DateTime, create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError

app = web.Application()

NAME_DATABASE = "db_aiohttp"
USER_DATABASE = "postgres"
PASS_USER_DATABASE = "postgres"
HOST_NAME = "10.0.2.15"
PORT_HOST = "5432"

# инициализация подключения через строку провайдера DSN
DSN = (
    "postgresql+asyncpg://"
    + USER_DATABASE
    + ":"
    + PASS_USER_DATABASE
    + "@"
    + HOST_NAME
    + ":"
    + PORT_HOST
    + "/"
    + NAME_DATABASE
)

engine = create_async_engine(DSN)
Base = declarative_base()
Session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class Adv(Base):
    __tablename__ = "advs"
    id = Column(Integer, primary_key=True)
    header = Column(String(50), nullable=False)
    description = Column(String(50), nullable=False)
    date = Column(DateTime, server_default=func.now())
    owner = Column(String(50))


async def orm_context(app):
    print("START")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
    print("SHUT DOWN")


@web.middleware
async def session_middleware(request: web.Request, handler):
    async with Session() as session:
        request["session"] = session
        response = await handler(request)
        return response


app.cleanup_ctx.append(orm_context)
app.middlewares.append(session_middleware)


async def get_adv(adv_id: int, session: Session) -> Adv:
    adv = await session.get(Adv, adv_id)
    if adv is None:
        raise web.HTTPNotFound(
            text=json.dumps({"error": "adv not found"}), content_type="application/json"
        )
    return adv


class AdvView(web.View):
    @property
    def session(self) -> Session:
        return self.request["session"]

    @property
    def adv_id(self) -> int:
        return int(self.request.match_info["adv_id"])

    async def get(self):
        adv = await get_adv(self.adv_id, self.session)
        return web.json_response(
            {
                "id": adv.id,
                "header": adv.header,
                "description": adv.description,
                "date": int(adv.date.timestamp()),
            }
        )

    async def post(self):
        json_data = await self.request.json()
        new_adv = Adv(**json_data)
        self.session.add(new_adv)
        try:
            await self.session.commit()
        except IntegrityError as er:
            raise web.HTTPNotFound(
                text=json.dumps({"error": "avd already exist"}),
                content_type="application/json",
            )

        return web.json_response(
            {
                "id": new_adv.id,
                "header": new_adv.header,
                "description": new_adv.description,
                "owner": new_adv.owner,
            }
        )

    async def delete(self):
        adv = await get_adv(self.adv_id, self.session)
        await self.session.delete(adv)
        await self.session.commit()
        return web.json_response(
            {
                "id": adv.id,
            }
        )


app.add_routes(
    [
        web.get("/adv/{adv_id:\d+}", AdvView),
        web.post("/adv/", AdvView),
        web.delete("/adv/{adv_id:\d+}", AdvView),
    ]
)


if __name__ == "__main__":
    web.run_app(app)

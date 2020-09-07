import aiohttp
from aiohttp import web
from aiohttp_validate import validate
import aiohttp_cors

from serverModule.stream import StreamPool
from serverModule.log import log

PAUSE = 0x101
RESUME = 0x100
DELETE = 0x102

@validate(
    request_schema={
        "type": "object",
        "properties": {
            "uri": {"type": "string"},
            "options": {
                "type": "object",
                "properties": {
                    "should_end": {"type": "boolean"},
                    "width": {"type": ["integer", "null"]},
                    "height": {"type": ["integer", "null"]},
                }
            }
        },
        "required": ["uri"],
        "additionalProperties": False
    }
)

async def handle_stream_management(params, request):
    uri = params['uri']
    options = params['options']

    if options.get('should_end'):
        await request.app['stream_pool'].delete_stream(uri)
        return web.json_response({
            'streams': 'Deleted'
        })

    stream = await request.app['stream_pool'].create_stream(uri, options)
    return web.json_response(stream.get_json_object())


async def handle_stream_list(request):
    streams = await request.app['stream_pool'].get_streams()
    return web.json_response({
        'streams': [stream.get_json_object() for stream in streams.values()]
    })


async def handle_ws(request):
    key = request.match_info['key']
    stream = request.app['stream_pool'].streams[key]

    ws = web.WebSocketResponse()
    await ws.prepare(request)
    stream.ws_add(ws)

    if not stream.is_started():
        await stream.start()
    try:
        async for msg in ws:
            msg_data_value = int(msg.data[10:13])
            if msg_data_value == PAUSE:
                log.info('Paused')
                stream.ws_remove(ws)
            elif msg_data_value == RESUME:
                log.info('Resumed')
                stream.ws_add(ws)
            elif msg.type == aiohttp.WSMsgType.TEXT:
                log.info(msg)

    finally:
        log.info('ENDED')
        stream.ws_remove(ws)
    return ws

def init():
    app = web.Application()
    app['stream_pool'] = StreamPool()

    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    cors.add(app.router.add_post('/stream/manage', handle_stream_management))
    cors.add(app.router.add_get('/stream', handle_stream_list))
    cors.add(app.router.add_get('/ws/{key}', handle_ws))

    web.run_app(app, port=8088, host='192.168.1.108')


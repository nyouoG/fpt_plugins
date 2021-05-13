from FFxivPythonTrigger import *
from aiohttp import web
import traceback
import sys
import io

_logger = Logger.Logger("DebugExec")


class DebugExecPlugin(PluginBase):
    name = "DebugExec"

    async def exec_debug(self, request: web.Request):
        data = {'msg': 'success'}
        str_out = io.StringIO()
        try:
            normal_out = sys.stdout
            sys.stdout = str_out
            exec(await request.text())
            sys.stdout = normal_out
        except Exception:
            data['msg'] = 'error occurred'
            data['traceback'] = traceback.format_exc()
        data['print'] = str_out.getvalue()
        return web.json_response(data)

    def __init__(self):
        super().__init__()
        # self.register_event("act log line",_logger.debug)
        api.HttpApi.register_post_route('exec', self.exec_debug)
        self.data = dict()

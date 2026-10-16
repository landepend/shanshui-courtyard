"""Verify the local MCP server separately from the Unity Editor bridge."""
import argparse, asyncio, json, os, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def resolve_server(explicit=None):
    if explicit:
        executable = shutil.which(explicit)
        path = Path(explicit).expanduser()
        if executable or path.is_file():
            return executable or str(path.resolve())
        raise FileNotFoundError('MCP executable not found: ' + explicit)
    executable = shutil.which('mcp-for-unity')
    if executable:
        return executable
    venv = Path.home() / '.codex/mcp/unity-mcp-v10.3.0/Server/.venv'
    for path in (venv / 'bin/mcp-for-unity', venv / 'Scripts/mcp-for-unity.exe'):
        if path.is_file():
            return str(path)
    raise FileNotFoundError('Unity MCP server is not installed here. Pass --server PATH or add mcp-for-unity to PATH.')

async def verify(server):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    env = {**os.environ, 'UNITY_MCP_DISABLE_TELEMETRY': '1', 'PYTHONIOENCODING': 'utf-8'}
    params = StdioServerParameters(command=server, args=['--transport', 'stdio'], env=env)
    (ROOT / 'tests/results').mkdir(parents=True, exist_ok=True)
    with (ROOT / 'tests/results/unity-mcp-server.log').open('w', encoding='utf-8') as log:
        async with stdio_client(params, errlog=log) as (read, write):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                tools = await session.list_tools()
                resources = await session.list_resources()
                result = {'server': init.serverInfo.model_dump(), 'server_executable': server, 'tool_count': len(tools.tools),
                          'tools': [tool.name for tool in tools.tools],
                          'resources': [str(resource.uri) for resource in resources.resources],
                          'editor_connected': False}
                instances = next((r for r in resources.resources if 'instances' in str(r.uri)), None)
                if instances:
                    response = await session.read_resource(instances.uri)
                    result['unity_instances'] = response.model_dump(mode='json')
                    for item in response.contents:
                        if hasattr(item, 'text'):
                            data = json.loads(item.text)
                            result['editor_connected'] = data.get('instance_count', 0) > 0
                (ROOT / 'tests/results/unity-mcp-verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
                print(json.dumps(result, ensure_ascii=False))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', help='MCP executable; defaults to PATH or the local Codex MCP venv')
    args = parser.parse_args()
    try:
        server = resolve_server(args.server)
        asyncio.run(asyncio.wait_for(verify(server), timeout=45))
    except (FileNotFoundError, ImportError) as error:
        parser.exit(1, str(error) + '\nUse a Python environment with the mcp package for this optional check.\n')

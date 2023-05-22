import asyncio
import base64
import hashlib
import json
import os
import uuid
from textwrap import dedent

import websockets
from rich.console import Console
from rich.markdown import Markdown


class Colors:
    GREEN = '\033[38;5;121m'
    END = '\033[0m'


class ShakoChatbot:
    OPTIONS = """
        Shako - A command-line tool for interacting with Shako AI chatbot. (https://shako.ai)
            DOUBLE "enter" to send a message.
            - Type "!exit" to exit the program.
            - Type "!clear" to clear the console.
            - Type "!new" to start a new conversation.
    """

    def __init__(self):
        self.uri = 'wss://api.shako.ai/api/chat'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0',
            'Sec-WebSocket-Version': '13',
            'Origin': 'https://shako.ai',
            'Sec-WebSocket-Extensions': 'permessage-deflate',
            'Sec-WebSocket-Key': self.web_key(),
            'Connection': 'Upgrade',
        }
        self.clear = lambda: os.system('cls' if os.name == 'nt' else 'clear')
        self.console = Console()
        self.websocket = None
        self.chat_id = None

    def web_key(self):
        key = base64.b64encode(uuid.uuid4().bytes).decode('utf-8')
        return base64.b64encode(hashlib.sha1(key.encode('utf-8')).digest()).decode('utf-8')

    def get_query(self, prompt: str):
        print(prompt, end='')
        return '/n'.join(iter(input, ''))

    async def connect(self):
        conversation = []
        while True:
            query = self.get_query(f'{Colors.GREEN}You{Colors.END} : ').lower()

            if query == '!exit':
                break
            elif query == '!clear':
                self.clear()
                print(dedent(self.OPTIONS))
                continue
            elif query == '!new':
                self.chat_id = None
                self.clear()
                print(dedent(self.OPTIONS))
                conversation = []
                continue

            initial_data = {
                'chat_id': str(uuid.uuid4()) if self.chat_id is None else self.chat_id,
                'metadata': {},
                'prompt': conversation + [{'content': query, 'role': 'user'}]
            }
            with self.console.status("[bold blue]Please wait! Shako is thinking..[/bold blue]", spinner='point'):
                async with websockets.connect(self.uri, extra_headers=self.headers) as self.websocket:
                    await self.websocket.send(json.dumps(initial_data))

                    result = []
                    while True:
                        response = await self.websocket.recv()
                        response_data = json.loads(response)
                        content = response_data.get('content')
                        if content:
                            result.append(content)

                        response_type = response_data.get('type')
                        if response_type == 'end':
                            break

                    joined_result = ''.join(result).strip()
                    self.console.print(Markdown(joined_result, code_theme='fruity'))
                    print()
                    self.chat_id = response_data.get('chat_id')

            conversation.extend([
                {'content': query, 'role': 'user'},
                {'content': joined_result, 'role': 'model'}
            ])

    def run(self):
        self.clear()
        print(dedent(self.OPTIONS))
        asyncio.run(self.connect())


if __name__ == '__main__':
    ShakoChatbot().run()
